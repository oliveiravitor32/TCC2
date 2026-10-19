"""Interface de dados urbanos (TCC 3.2, 4.6.1, Quadro 14).

Emula a interface de programacao que a plataforma municipal precisaria
publicar. Recebe e disponibiliza eventos (RF01) e expoe o historico de
decisoes e de telemetria para o painel (RF08).

Execucao local:  uvicorn api_eventos.app:app --reload
Banco: variavel DATABASE_URL (padrao: Postgres do docker-compose).
Publicacao: com CHAVE_API definida, o POST /eventos exige o cabecalho
X-Chave-Api (DIVERGENCIAS 22); as consultas continuam abertas ao painel.
CHAVE_DEMO, se definida, e uma segunda chave aceita no POST: a do painel de
demonstracao, publica por decisao do autor e desligavel sem afetar a outra.
Os POST de /bancada (conferencia e calibracao do no) aceitam SO a CHAVE_API:
com a chave publica, qualquer pessoa gravaria uma calibracao falsa.
"""

from __future__ import annotations

import logging
import os
import time as _relogio
import uuid
from pathlib import Path
import secrets
from collections.abc import Iterator
from contextlib import asynccontextmanager
from datetime import datetime, time, timedelta, timezone

from typing import Any

import psycopg
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from psycopg.errors import ForeignKeyViolation
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import ValidationError

from decisao import config
from decisao.sessao_bancada import PontoNaoCadastrado, registrar_calibracao, registrar_conferencia
from decisao.inferencia import carregar as carregar_regras
from decisao.energia import (
    energia_decisoes,
    energia_pleno_constante,
    energia_por_fracao,
    trajetoria_horario_fixo,
)

from .esquemas import (
    CalibracaoEntrada,
    SessaoBancada,
    SessaoBancadaEntrada,
    Alerta,
    Decisao,
    Energia,
    Evento,
    EventoEntrada,
    Ponto,
    ResultadoPacote,
    Telemetria,
    Explicacao,
    Tipo,
    Trecho,
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://iluminacao:iluminacao@localhost:5432/iluminacao"
)
LIMITE_MAX = 5000
# O painel e servido de outra origem (Vercel) e a API roda na VM: sem CORS o
# navegador bloqueia a leitura. Lista separada por virgula; "*" libera todas.
ORIGENS = [o.strip() for o in os.environ.get("ORIGENS_PAINEL", "*").split(",") if o.strip()]
# Linha de base por horario fixo (3.11): a programacao agendada que uma
# telegestao sem dados urbanos faria.
# Chave de publicacao (DIVERGENCIAS 22). Vazia = sem exigencia (desenvolvimento).
CHAVE_API = os.environ.get("CHAVE_API", "")
CHAVE_DEMO = os.environ.get("CHAVE_DEMO", "")
REGRAS_DIR = Path(__file__).resolve().parent.parent / "decisao" / "regras"
HORA_INICIO_ATENUACAO = time(0, 0)
HORA_FIM_ATENUACAO = time(5, 0)

_pool: ConnectionPool | None = None

# Log da API (chave=valor, hora UTC). Nunca registra a chave de acesso nem
# dado pessoal (RNF08): so origem da requisicao, trecho, tipo e motivo.
log = logging.getLogger("api")
if not log.handlers:
    _saida = logging.StreamHandler()
    _formato = logging.Formatter("%(asctime)sZ %(levelname)s api %(message)s", "%Y-%m-%dT%H:%M:%S")
    _formato.converter = _relogio.gmtime
    _saida.setFormatter(_formato)
    log.addHandler(_saida)
    log.setLevel(logging.INFO)
    log.propagate = False


def _cliente(request: Request) -> str:
    """IP de quem chamou; atras do Caddy, o primeiro de X-Forwarded-For."""
    encaminhado = request.headers.get("x-forwarded-for")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else "-"


@asynccontextmanager
async def _ciclo_de_vida(_: FastAPI):
    global _pool
    _pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=5, open=True)
    try:
        yield
    finally:
        _pool.close()


app = FastAPI(
    title="Interface de dados urbanos",
    description="Emulacao da interface da plataforma municipal (TCC 4.6.2, Quadro 14).",
    version="0.1.0",
    lifespan=_ciclo_de_vida,
)

@app.middleware("http")
async def _registro(request: Request, chamar):
    """Identificador da requisicao (devolvido em X-Request-ID) e registro das
    escritas e de toda resposta de erro, com a duracao."""
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request.state.rid = rid
    inicio = _relogio.perf_counter()
    try:
        resposta = await chamar(request)
    except Exception:
        log.exception("rid=%s %s %s erro interno", rid, request.method, request.url.path)
        resposta = JSONResponse({"detail": "erro interno", "request_id": rid}, status_code=500)
    ms = (_relogio.perf_counter() - inicio) * 1000
    if request.method != "GET" or resposta.status_code >= 400:
        nivel = logging.WARNING if resposta.status_code >= 400 else logging.INFO
        log.log(nivel, "rid=%s %s %s status=%s ms=%.0f ip=%s", rid, request.method,
                request.url.path, resposta.status_code, ms, _cliente(request))
    resposta.headers["X-Request-ID"] = rid
    return resposta


@app.exception_handler(RequestValidationError)
async def _validacao(request: Request, erro: RequestValidationError):
    motivos = "; ".join(".".join(str(x) for x in e.get("loc", ())) + ": " + str(e.get("msg"))
                        for e in erro.errors()[:5])
    log.warning("rid=%s %s recusado: %s", getattr(request.state, "rid", "-"),
                request.url.path, motivos)
    return await request_validation_exception_handler(request, erro)


app.add_middleware(
    CORSMiddleware,
    expose_headers=["X-Request-ID"],
    allow_origins=ORIGENS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def conexao() -> Iterator[psycopg.Connection]:
    """Uma transacao por requisicao: confirma no sucesso, desfaz no erro."""
    assert _pool is not None, "pool nao inicializado"
    with _pool.connection() as conn:
        conn.row_factory = dict_row
        yield conn


Conn = Depends(conexao)


def _recusar_chave(request: Request) -> None:
    log.warning("rid=%s chave ausente ou invalida em %s %s ip=%s",
                getattr(request.state, "rid", "-"), request.method, request.url.path,
                _cliente(request))
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "chave de acesso ausente ou invalida")


def exigir_chave(request: Request, x_chave_api: str | None = Header(default=None)) -> None:
    """So quem tem a chave publica eventos: sem ela, qualquer pessoa na
    internet mudaria a luz. A comparacao em tempo constante nao entrega a
    chave por diferenca de tempo de resposta."""
    if not CHAVE_API:
        return
    validas = [c for c in (CHAVE_API, CHAVE_DEMO) if c]
    if x_chave_api is None or not any(secrets.compare_digest(x_chave_api, c) for c in validas):
        _recusar_chave(request)


def exigir_chave_secreta(request: Request, x_chave_api: str | None = Header(default=None)) -> None:
    """Para gravar dados de medicao: so a CHAVE_API, nunca a CHAVE_DEMO.

    A chave do painel e publica (esta na aplicacao estatica); aceita-la aqui
    deixaria qualquer visitante gravar uma calibracao falsa e corromper o
    diagnostico. Sem CHAVE_API (ambiente local), fica aberto como o POST
    /eventos.
    """
    if not CHAVE_API:
        return
    if x_chave_api is None or not secrets.compare_digest(x_chave_api, CHAVE_API):
        _recusar_chave(request)


# ---------------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------------
def _gravar(conn: psycopg.Connection, evento: EventoEntrada) -> dict:
    """Grava um item; ForeignKeyViolation = trecho fora do cadastro."""
    with conn.transaction():
        return conn.execute(
            """
            INSERT INTO evento_urbano
                (ocorrido_em, tipo, pessoas_media, periodo_s, ocorrencia, abrangencia,
                 origem, trecho_id, vigente_ate)
            VALUES (%(ocorrido_em)s, %(tipo)s, %(pessoas_media)s, %(periodo_s)s, %(ocorrencia)s,
                    %(abrangencia)s, %(origem)s, %(trecho)s, %(vigente_ate)s)
            RETURNING *, trecho_id AS trecho
            """,
            evento.model_dump(),
        ).fetchone()


def _log_aceito(rid: str, ev: dict) -> None:
    medida = (f"pessoas_media={ev['pessoas_media']}" if ev["tipo"] == "volume"
              else f"ocorrencia={ev['ocorrencia']}")
    log.info("rid=%s evento=%s trecho=%s tipo=%s %s origem=%s", rid, ev["id"], ev["trecho"],
             ev["tipo"], medida, ev["origem"])


@app.post("/eventos", response_model=Evento | ResultadoPacote, status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(exigir_chave)])
def publicar_evento(
    request: Request, response: Response, corpo: Any = Body(...), conn: psycopg.Connection = Conn
) -> dict:
    """Um item ou um pacote (lista) de itens (DIVERGENCIAS 56).

    Item unico: 201 com o evento gravado, ou 422. Pacote: 200 com os itens
    aceitos e os recusados (indice e motivo) - um item errado nao derruba os
    outros. A especificacao pede que cada trecho seja atualizado a cada 5 min
    e que os envios sejam distribuidos no periodo, sem pico.
    """
    if isinstance(corpo, dict):
        try:
            evento = EventoEntrada.model_validate(corpo)
        except ValidationError as erro:
            raise RequestValidationError(erro.errors()) from None
        try:
            gravado = _gravar(conn, evento)
            _log_aceito(request.state.rid, gravado)
            return gravado
        except ForeignKeyViolation:
            # Trecho fora do cadastro: o evento nao tem a que luminaria se referir.
            log.warning("rid=%s recusado: trecho %s nao cadastrado", request.state.rid, evento.trecho)
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                                f"trecho {evento.trecho} nao cadastrado") from None
    if not isinstance(corpo, list) or not 1 <= len(corpo) <= config.MAX_ITENS_PACOTE:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                            f"o corpo deve ser um item ou uma lista de 1 a "
                            f"{config.MAX_ITENS_PACOTE} itens")
    aceitos, recusados = [], []
    for i, item in enumerate(corpo):
        try:
            evento = EventoEntrada.model_validate(item)
        except ValidationError as erro:
            recusados.append({"indice": i, "erro": "; ".join(e["msg"] for e in erro.errors())})
            continue
        try:
            aceitos.append(_gravar(conn, evento))
            _log_aceito(request.state.rid, aceitos[-1])
        except ForeignKeyViolation:
            recusados.append({"indice": i, "erro": f"trecho {evento.trecho} nao cadastrado"})
    for r in recusados:
        log.warning("rid=%s pacote item=%s recusado: %s", request.state.rid, r["indice"], r["erro"])
    log.info("rid=%s pacote itens=%s aceitos=%s recusados=%s", request.state.rid, len(corpo),
             len(aceitos), len(recusados))
    response.status_code = status.HTTP_200_OK
    return {"aceitos": aceitos, "recusados": recusados}


@app.get("/eventos", response_model=list[Evento])
def consultar_eventos(
    inicio: datetime | None = None,
    fim: datetime | None = None,
    tipo: Tipo | None = None,
    trecho: int | None = None,
    limite: int = Query(500, ge=1, le=LIMITE_MAX),
    conn: psycopg.Connection = Conn,
) -> list[dict]:
    return conn.execute(
        """
        SELECT *, trecho_id AS trecho FROM evento_urbano
         WHERE (%(inicio)s::timestamptz IS NULL OR ocorrido_em >= %(inicio)s)
           AND (%(fim)s::timestamptz    IS NULL OR ocorrido_em <  %(fim)s)
           AND (%(tipo)s::text          IS NULL OR tipo = %(tipo)s)
           AND (%(trecho)s::bigint      IS NULL OR trecho_id = %(trecho)s)
         ORDER BY ocorrido_em DESC, id DESC
         LIMIT %(limite)s
        """,
        {"inicio": inicio, "fim": fim, "tipo": tipo, "trecho": trecho, "limite": limite},
    ).fetchall()


# ---------------------------------------------------------------------------
# Decisoes e telemetria (leitura, para o painel)
# ---------------------------------------------------------------------------
@app.get("/decisoes", response_model=list[Decisao])
def consultar_decisoes(
    ponto: str | None = None,
    inicio: datetime | None = None,
    fim: datetime | None = None,
    execucao_id: int | None = None,
    limite: int = Query(500, ge=1, le=LIMITE_MAX),
    conn: psycopg.Connection = Conn,
) -> list[dict]:
    return conn.execute(
        """
        SELECT d.id, d.criado_em, p.codigo AS ponto, d.classe_codigo,
               d.nivel_pretendido, d.nivel_emitido, d.restricao_aplicada,
               d.nivel_anterior, d.previsao_movimentacao,
               r.rotulo AS versao_base_regras, m.rotulo AS versao_modelo,
               d.execucao_id, d.entrada, d.ativacoes,
               COALESCE(array_agg(de.evento_id ORDER BY de.evento_id)
                        FILTER (WHERE de.evento_id IS NOT NULL), '{}') AS evento_ids
          FROM decisao d
          JOIN ponto_de_luz p            ON p.id = d.ponto_de_luz_id
          JOIN versao_base_regras r      ON r.id = d.versao_base_regras_id
          JOIN versao_modelo_previsao m  ON m.id = d.versao_modelo_id
          LEFT JOIN decisao_evento de    ON de.decisao_id = d.id
         WHERE (%(ponto)s::text           IS NULL OR p.codigo = %(ponto)s)
           AND (%(inicio)s::timestamptz   IS NULL OR d.criado_em >= %(inicio)s)
           AND (%(fim)s::timestamptz      IS NULL OR d.criado_em <  %(fim)s)
           AND (%(execucao_id)s::bigint   IS NULL OR d.execucao_id = %(execucao_id)s)
         GROUP BY d.id, p.codigo, r.rotulo, m.rotulo
         ORDER BY d.criado_em DESC
         LIMIT %(limite)s
        """,
        {"ponto": ponto, "inicio": inicio, "fim": fim, "execucao_id": execucao_id, "limite": limite},
    ).fetchall()


@app.get("/pontos", response_model=list[Ponto])
def consultar_pontos(conn: psycopg.Connection = Conn) -> list[dict]:
    """Estado de cada ponto de luz, com a ultima decisao e a ultima medicao.

    Fora do Quadro 14: o painel precisa mostrar o estado do no (RF08) e o
    RF11 so e observavel se o operador vir o ponto em falha.
    """
    return conn.execute(
        """
        SELECT p.codigo, p.placa, p.logradouro, p.classe_codigo, p.estado_operacional,
               p.latitude, p.longitude, p.simulado, p.grupo_id,
               (SELECT count(*) FROM alerta_diagnostico a
                 WHERE a.ponto_de_luz_id = p.id AND a.encerrado_em IS NULL) AS alertas_abertos,
               ARRAY(SELECT tp.trecho_id FROM trecho_ponto tp
                      WHERE tp.ponto_de_luz_id = p.id ORDER BY tp.distancia_m) AS trechos,
               c.iluminancia_media_min_lux AS lux_pleno,
               cm.iluminancia_media_min_lux / c.iluminancia_media_min_lux AS piso_fracao,
               u.nivel_emitido, u.restricao_aplicada, u.criado_em AS decidido_em,
               t.lux_medido, t.duty, t.medido_em, t.nivel_antes, t.lux_antes
          FROM ponto_de_luz p
          JOIN classe_iluminacao c       ON c.codigo = p.classe_codigo
          LEFT JOIN classe_iluminacao cm ON cm.codigo = c.classe_min_dimerizacao
          LEFT JOIN LATERAL (
                SELECT d.* FROM decisao d
                 WHERE d.ponto_de_luz_id = p.id
                 ORDER BY d.criado_em DESC LIMIT 1
               ) u ON true
          LEFT JOIN telemetria t ON t.decisao_id = u.id
         ORDER BY p.simulado, p.codigo
        """
    ).fetchall()


# ---------------------------------------------------------------------------
# Explicacao: o que o sistema recebeu e por que decidiu (painel, RNF04)
# ---------------------------------------------------------------------------
_bases: dict[str, object] = {}


def _base(rotulo: str):
    """Base de regras de uma versao, lida do arquivo versionado."""
    nome = rotulo.removesuffix("-degraus")
    if nome not in _bases:
        caminho = REGRAS_DIR / f"{nome}.toml"
        _bases[nome] = carregar_regras(caminho) if caminho.exists() else None
    return _bases[nome]


def _motivo(restricao: str, pretendido: float, emitido: float, anterior: float | None,
            piso: float | None) -> str:
    if restricao == "piso":
        return (f"a inferencia pediu {pretendido:.3f}, abaixo do piso da classe "
                f"({piso:.3f}); a verificacao elevou ao piso")
    if restricao == "taxa":
        return (f"descer de {anterior:.3f} para {pretendido:.3f} de uma vez excederia 0,1 do "
                f"pleno por minuto; a verificacao limitou a descida a {emitido:.3f}")
    return "o nivel pedido respeita o piso e a taxa: emitido sem correcao"


@app.get("/eventos/{evento_id}/explicacao", response_model=Explicacao)
def explicar_evento(evento_id: int, conn: psycopg.Connection = Conn) -> dict:
    evento = conn.execute(
        "SELECT *, trecho_id AS trecho FROM evento_urbano WHERE id = %s", (evento_id,)
    ).fetchone()
    if evento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"evento {evento_id} nao encontrado")
    trecho = conn.execute(
        "SELECT tipo_logradouro, nome_logradouro FROM trecho_via WHERE id = %s", (evento["trecho"],)
    ).fetchone()

    linhas = conn.execute(
        """
        SELECT p.codigo AS ponto, p.placa, tp.distancia_m,
               d.id, d.criado_em, d.nivel_pretendido, d.nivel_emitido, d.restricao_aplicada,
               d.nivel_anterior, d.entrada, d.ativacoes, r.rotulo AS versao_base_regras,
               cm.iluminancia_media_min_lux / c.iluminancia_media_min_lux AS piso_fracao,
               t.lux_medido, t.duty, c.iluminancia_media_min_lux AS lux_pleno
          FROM trecho_ponto tp
          JOIN ponto_de_luz p ON p.id = tp.ponto_de_luz_id
          LEFT JOIN LATERAL (
                SELECT d.* FROM decisao d
                  JOIN decisao_evento de ON de.decisao_id = d.id AND de.evento_id = %(ev)s
                 WHERE d.ponto_de_luz_id = p.id
                 ORDER BY d.criado_em LIMIT 1
               ) d ON true
          LEFT JOIN versao_base_regras r ON r.id = d.versao_base_regras_id
          LEFT JOIN classe_iluminacao c  ON c.codigo = COALESCE(d.classe_codigo, p.classe_codigo)
          LEFT JOIN classe_iluminacao cm ON cm.codigo = c.classe_min_dimerizacao
          LEFT JOIN telemetria t ON t.decisao_id = d.id
         WHERE tp.trecho_id = %(trecho)s
         ORDER BY tp.distancia_m
        """,
        {"ev": evento_id, "trecho": evento["trecho"]},
    ).fetchall()

    decisoes = []
    for l in linhas:
        item = {"ponto": l["ponto"], "placa": l["placa"], "distancia_m": float(l["distancia_m"])}
        if l["id"] is None:
            item["decidida"] = False
            decisoes.append(item)
            continue
        base = _base(l["versao_base_regras"])
        ativ = l["ativacoes"] or {}
        regras = []
        if base is not None:
            for r in base.regras:
                grau = float(ativ.get(r.id, 0.0))
                if grau > 0:
                    regras.append({"id": r.id, "texto": r.texto(), "origem": r.origem, "grau": grau})
            regras.sort(key=lambda x: -x["grau"])
        pret, emit = float(l["nivel_pretendido"]), float(l["nivel_emitido"])
        ant = None if l["nivel_anterior"] is None else float(l["nivel_anterior"])
        piso = None if l["piso_fracao"] is None else float(l["piso_fracao"])
        item.update({
            "decidida": True,
            "decisao_id": str(l["id"]),
            "criado_em": l["criado_em"],
            "versao_base_regras": l["versao_base_regras"],
            "entrada": l["entrada"],
            "regras_ativadas": regras,
            "nivel_pretendido": pret,
            "restricao_aplicada": l["restricao_aplicada"],
            "motivo_restricao": _motivo(l["restricao_aplicada"], pret, emit, ant, piso),
            "nivel_anterior": ant,
            "nivel_emitido": emit,
            "lux_esperado": None if l["lux_pleno"] is None else round(emit * float(l["lux_pleno"]), 2),
            "lux_medido": None if l["lux_medido"] is None else float(l["lux_medido"]),
            "duty": None if l["duty"] is None else float(l["duty"]),
        })
        decisoes.append(item)

    nome = None if trecho is None else " ".join(x for x in (trecho["tipo_logradouro"], trecho["nome_logradouro"]) if x)
    return {"evento": evento, "trecho_nome": nome, "decisoes": decisoes}


@app.get("/trechos", response_model=list[Trecho])
def consultar_trechos(conn: psycopg.Connection = Conn) -> list[dict]:
    """Trechos de via cadastrados e as luminarias associadas a cada um.

    Parte da especificacao de integracao (DIVERGENCIAS 54): e o vocabulario
    de lugares que a plataforma de monitoramento pode citar no POST /eventos.
    """
    return conn.execute(
        """
        SELECT t.id, t.codlog, t.tipo_logradouro, t.nome_logradouro,
               t.numero_inicial, t.numero_final,
               ARRAY(SELECT p.codigo FROM trecho_ponto tp
                       JOIN ponto_de_luz p ON p.id = tp.ponto_de_luz_id
                      WHERE tp.trecho_id = t.id ORDER BY p.codigo) AS pontos,
               t.geometria_wgs84,
               -- Regua do trecho (3.6): o "cheio" tipico, em pessoas. Aprendida
               -- (p99 de 28 dias) quando ha historico; senao, o valor inicial.
               COALESCE(t.referencia_aprendida, t.referencia_pessoas)::float AS regua,
               t.referencia_aprendida IS NOT NULL AS regua_aprendida,
               -- Para o mapa: volume vigente (15 min) normalizado pela regua do
               -- trecho e ocorrencia aberta (a mais recente nao encerrada e vigente).
               (SELECT round((e.pessoas_media / COALESCE(t.referencia_aprendida,
                                                         t.referencia_pessoas))::numeric, 3)
                  FROM evento_urbano e
                 WHERE e.trecho_id = t.id AND e.tipo = 'volume'
                   AND e.ocorrido_em > now() - interval '15 minutes'
                 ORDER BY e.ocorrido_em DESC LIMIT 1) AS nivel_observado,
               COALESCE((SELECT e.ocorrencia <> 'encerrada'
                           AND COALESCE(e.vigente_ate, e.ocorrido_em + interval '15 minutes') > now()
                  FROM evento_urbano e
                 WHERE e.trecho_id = t.id AND e.tipo = 'ocorrencia'
                 ORDER BY e.ocorrido_em DESC LIMIT 1), false) AS ocorrencia_aberta
          FROM trecho_via t
         ORDER BY t.nome_logradouro, t.numero_inicial NULLS LAST, t.id
        """
    ).fetchall()


@app.get("/alertas", response_model=list[Alerta])
def consultar_alertas(
    abertos: bool = True,
    limite: int = Query(100, ge=1, le=LIMITE_MAX),
    conn: psycopg.Connection = Conn,
) -> list[dict]:
    """Alertas de diagnostico do ponto de luz (RF11, 3.4.5)."""
    return conn.execute(
        """
        SELECT a.id, p.codigo AS ponto, a.tipo, a.razao, a.tolerancia, a.ciclos,
               a.aberto_em, a.encerrado_em
          FROM alerta_diagnostico a
          JOIN ponto_de_luz p ON p.id = a.ponto_de_luz_id
         WHERE (NOT %(abertos)s OR a.encerrado_em IS NULL)
         ORDER BY a.aberto_em DESC
         LIMIT %(limite)s
        """,
        {"abertos": abertos, "limite": limite},
    ).fetchall()


@app.get("/energia", response_model=Energia)
def consultar_energia(
    ponto: str | None = None,
    janela_min: float = Query(30, gt=0, le=1440),
    luminaria: str = "REF-40W",
    conn: psycopg.Connection = Conn,
) -> dict:
    """Consumo estimado na janela, projetado para a luminaria do Quadro 9.

    A serie vem da LUZ MEDIDA - fracao = iluminancia liquida / iluminancia da
    classe -, e a mesma janela e integrada tambem pelo COMANDO, pelo fluxo
    pleno constante e pela atenuacao por horario fixo (3.11). A potencia da
    bancada nao serve para essa leitura: o segmento de fita consome cerca de
    um watt, sem significado para quem raciocina em termos do parque.
    """
    ref = conn.execute(
        "SELECT codigo, potencia_nominal_w FROM luminaria_referencia WHERE codigo = %s",
        (luminaria,),
    ).fetchone()
    if ref is None:
        raise HTTPException(404, f"luminaria de referencia {luminaria!r} nao cadastrada")

    alvo = conn.execute(
        """
        SELECT p.id, p.codigo, c.iluminancia_media_min_lux,
               cm.iluminancia_media_min_lux / c.iluminancia_media_min_lux AS piso
          FROM ponto_de_luz p
          JOIN classe_iluminacao c       ON c.codigo = p.classe_codigo
          LEFT JOIN classe_iluminacao cm ON cm.codigo = c.classe_min_dimerizacao
         WHERE (%s::text IS NULL OR p.codigo = %s)
         -- Sem ponto indicado: o no real, nunca um simulado da visao de bairro.
         ORDER BY p.simulado, p.codigo LIMIT 1
        """,
        (ponto, ponto),
    ).fetchone()
    if alvo is None:
        raise HTTPException(404, "nenhum ponto de luz cadastrado")

    potencia = float(ref["potencia_nominal_w"])
    lux_pleno = float(alvo["iluminancia_media_min_lux"])
    piso = float(alvo["piso"] or 1.0)
    fim = datetime.now(timezone.utc)
    inicio = fim - timedelta(minutes=janela_min)

    linhas = conn.execute(
        """
        SELECT t.medido_em, t.recebido_em, t.duty, t.lux_medido,
               COALESCE(s.lux_residual, 0) AS residual, d.nivel_emitido
          FROM telemetria t
          JOIN decisao d ON d.id = t.decisao_id
          LEFT JOIN sessao_medicao s ON s.id = t.sessao_id
         WHERE t.ponto_de_luz_id = %(ponto)s AND t.recebido_em >= %(inicio)s
         ORDER BY t.recebido_em
        """,
        {"ponto": alvo["id"], "inicio": inicio},
    ).fetchall()

    amostras = []
    for l in linhas:
        # Fracao pela luz: quanto da iluminancia da classe esta sendo
        # entregue. E o que o texto chama de verificacao cruzada da
        # estimativa derivada do ciclo comandado.
        medida = max((float(l["lux_medido"]) - float(l["residual"])) / lux_pleno, 0.0)
        comandada = float(l["nivel_emitido"])
        amostras.append({
            "medido_em": l["recebido_em"],
            "fracao_medida": round(medida, 4),
            "fracao_comandada": round(comandada, 4),
            "potencia_medida_w": round(potencia * medida, 3),
            "potencia_comandada_w": round(potencia * comandada, 3),
        })

    serie_luz = [(a["medido_em"], a["fracao_medida"]) for a in amostras]
    pela_luz = energia_por_fracao(serie_luz, potencia, fim=fim)

    decisoes = conn.execute(
        """
        SELECT criado_em, nivel_anterior, nivel_emitido FROM decisao
         WHERE ponto_de_luz_id = %(ponto)s AND criado_em >= %(inicio)s
         ORDER BY criado_em
        """,
        {"ponto": alvo["id"], "inicio": inicio},
    ).fetchall()
    pelo_comando = energia_decisoes(
        [(d["criado_em"],
          float(d["nivel_anterior"]) if d["nivel_anterior"] is not None else None,
          float(d["nivel_emitido"])) for d in decisoes],
        potencia, fim=fim,
    )

    pleno = energia_pleno_constante(potencia, janela_min)
    fixo = energia_decisoes(
        trajetoria_horario_fixo(
            inicio, fim, piso,
            hora_inicio_atenuacao=HORA_INICIO_ATENUACAO,
            hora_fim_atenuacao=HORA_FIM_ATENUACAO,
            fuso=config.FUSO,
        ),
        potencia, fim=fim,
    )
    return {
        "ponto": alvo["codigo"],
        "luminaria": ref["codigo"],
        "potencia_nominal_w": potencia,
        "janela_min": janela_min,
        "inicio": inicio,
        "fim": fim,
        "amostras": amostras,
        "potencia_agora_w": amostras[-1]["potencia_medida_w"] if amostras else None,
        "energia_pela_luz_wh": round(pela_luz, 4),
        "energia_pelo_comando_wh": round(pelo_comando, 4),
        "energia_pleno_wh": round(pleno, 4),
        "energia_horario_fixo_wh": round(fixo, 4),
        "razao_pleno": round(pela_luz / pleno, 4) if pleno else None,
        "razao_horario_fixo": round(pela_luz / fixo, 4) if fixo else None,
        "divergencia_entre_estimativas": (
            round(pela_luz / pelo_comando - 1, 4) if pelo_comando else None
        ),
    }


@app.get("/telemetria", response_model=list[Telemetria])
def consultar_telemetria(
    ponto: str | None = None,
    inicio: datetime | None = None,
    fim: datetime | None = None,
    limite: int = Query(500, ge=1, le=LIMITE_MAX),
    conn: psycopg.Connection = Conn,
) -> list[dict]:
    return conn.execute(
        """
        SELECT t.decisao_id, p.codigo AS ponto, t.medido_em, t.recebido_em,
               t.duty, t.lux_medido, t.nivel_aplicado, t.nivel_antes, t.lux_antes
          FROM telemetria t
          JOIN ponto_de_luz p ON p.id = t.ponto_de_luz_id
         WHERE (%(ponto)s::text         IS NULL OR p.codigo = %(ponto)s)
           AND (%(inicio)s::timestamptz IS NULL OR t.medido_em >= %(inicio)s)
           AND (%(fim)s::timestamptz    IS NULL OR t.medido_em <  %(fim)s)
         ORDER BY t.medido_em DESC
         LIMIT %(limite)s
        """,
        {"ponto": ponto, "inicio": inicio, "fim": fim, "limite": limite},
    ).fetchall()


# ---------------------------------------------------------------------------
# Bancada (DIVERGENCIAS 65)
# ---------------------------------------------------------------------------
@app.post("/bancada/sessoes", response_model=SessaoBancada, status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(exigir_chave_secreta)])
def gravar_sessao_bancada(corpo: SessaoBancadaEntrada, conn: psycopg.Connection = Conn) -> dict:
    """Conferencia do no (bancada/conferir.py --vm). Aprovada: a sessao fica
    aberta e a telemetria seguinte e descontada da residual medida agora."""
    try:
        sid, descartada = registrar_conferencia(
            conn, corpo.ponto, corpo.lux_residual, corpo.aprovada, corpo.observacao)
    except PontoNaoCadastrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ponto nao cadastrado") from None
    log.info("bancada conferencia ponto=%s sessao=%s aprovada=%s residual=%s descartada=%s",
             corpo.ponto, sid, corpo.aprovada, corpo.lux_residual, descartada)
    return {"sessao_id": sid, "descartada": descartada}


@app.post("/bancada/calibracoes", response_model=SessaoBancada,
          status_code=status.HTTP_201_CREATED, dependencies=[Depends(exigir_chave_secreta)])
def gravar_calibracao_bancada(corpo: CalibracaoEntrada, conn: psycopg.Connection = Conn) -> dict:
    """Varredura de calibracao (bancada/calibrar.py --vm): sessao + linhas."""
    try:
        sid = registrar_calibracao(
            conn, corpo.ponto, corpo.lux_residual,
            [(l.serie, l.duty, l.lux_medido) for l in corpo.linhas],
            corpo.observacao, corpo.potencia_plena_w)
    except PontoNaoCadastrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ponto nao cadastrado") from None
    log.info("bancada calibracao ponto=%s sessao=%s pontos_da_curva=%s", corpo.ponto, sid,
             len(corpo.linhas))
    return {"sessao_id": sid, "descartada": False}
