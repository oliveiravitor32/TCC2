"""Ciclo de decisao (TCC 3.2, 4.6.1): estado da via -> previsao -> inferencia
-> verificacao -> registro. A publicacao MQTT fica em `decisao.servico`.

As funcoes recebem a conexao e NAO fazem commit: quem chama decide quando
confirmar. O servico confirma a decisao ANTES de publica-la, porque a
telemetria do no referencia a decisao por chave estrangeira.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

import psycopg
from psycopg.types.json import Jsonb

from . import config
from .inferencia import BaseRegras, Entrada, horas_desde_18h, inferir
from .previsao import Historico, Previsor
from .verificacao import PLENO, Criterio, verificar

log = logging.getLogger(__name__)



class BaseRegrasAlterada(RuntimeError):
    """O arquivo de regras mudou sem nova versao: quebraria o RNF04."""


@dataclass(frozen=True)
class Ponto:
    id: int
    codigo: str
    classe_codigo: str


@dataclass(frozen=True)
class EstadoVia:
    """Leituras vigentes dos trechos de um ponto (DIVERGENCIAS 55)."""

    presenca: bool  # alguma pessoa em algum trecho do ponto
    ocorrencia: bool
    # Pessoas na leitura vigente de cada trecho; vazio = sem dado vigente.
    pessoas: dict[int, int] = field(default_factory=dict)
    evento_ids: list[int] = field(default_factory=list)

    @property
    def sem_dado(self) -> bool:
        return not self.pessoas


@dataclass(frozen=True)
class DecisaoTomada:
    id: uuid.UUID
    ponto: Ponto
    criado_em: datetime
    nivel_pretendido: Decimal
    nivel_emitido: Decimal
    restricao_aplicada: str
    nivel_anterior: Decimal | None
    estado: EstadoVia

    def comando(self) -> dict:
        """Carga do topico iluminacao/{ponto}/comando (Quadro 14)."""
        return {"decisao_id": str(self.id), "nivel": float(self.nivel_emitido)}


# ---------------------------------------------------------------------------
# Referencias
# ---------------------------------------------------------------------------
def registrar_versao_regras(conn: psycopg.Connection, base: BaseRegras) -> int:
    """Liga a base carregada a sua linha em versao_base_regras (RNF04)."""
    linha = conn.execute(
        "SELECT id, hash_regras, qtd_regras FROM versao_base_regras WHERE rotulo = %s",
        (base.rotulo,),
    ).fetchone()
    if linha is None:
        raise BaseRegrasAlterada(f"versao {base.rotulo!r} nao cadastrada no banco")
    vid, hash_banco, qtd = linha
    if qtd != len(base.regras):
        raise BaseRegrasAlterada(f"{base.rotulo}: banco diz {qtd} regras, arquivo tem {len(base.regras)}")
    if hash_banco is None:
        conn.execute(
            "UPDATE versao_base_regras SET hash_regras = %s WHERE id = %s", (base.hash_regras, vid)
        )
    elif hash_banco != base.hash_regras:
        raise BaseRegrasAlterada(
            f"{base.rotulo}: arquivo de regras alterado sem nova versao (hash diferente)"
        )
    return vid


def id_modelo(conn: psycopg.Connection, rotulo: str) -> int:
    linha = conn.execute(
        "SELECT id FROM versao_modelo_previsao WHERE rotulo = %s", (rotulo,)
    ).fetchone()
    if linha is None:
        raise LookupError(f"modelo de previsao {rotulo!r} nao cadastrado")
    return linha[0]


def pontos(conn: psycopg.Connection) -> list[Ponto]:
    """Todos os pontos cadastrados: novo no = nova linha, sem codigo (RNF09)."""
    return [
        Ponto(*l)
        for l in conn.execute(
            "SELECT id, codigo, classe_codigo FROM ponto_de_luz"
            " WHERE estado_operacional <> 'manutencao' ORDER BY id"
        ).fetchall()
    ]


def criterio(conn: psycopg.Connection, classe: str) -> Criterio:
    """Monta o criterio da verificacao a partir da tabela (RF09)."""
    lux, lux_min_dim, taxa = conn.execute(
        """
        SELECT c.iluminancia_media_min_lux, cm.iluminancia_media_min_lux,
               c.taxa_max_decrescimo_min
          FROM classe_iluminacao c
          LEFT JOIN classe_iluminacao cm ON cm.codigo = c.classe_min_dimerizacao
         WHERE c.codigo = %s
        """,
        (classe,),
    ).fetchone()
    # Classe nao dimerizavel: o piso e o proprio fluxo pleno.
    piso = PLENO if lux_min_dim is None else Decimal(lux_min_dim) / Decimal(lux)
    return Criterio(piso=piso, taxa_max_decrescimo_min=Decimal(taxa))


# ---------------------------------------------------------------------------
# Estado da via
# ---------------------------------------------------------------------------
def origens_da_execucao(execucao_id: int | None) -> list[str] | None:
    """Origens de evento que uma execucao de cenario enxerga (DIVERGENCIAS 51).

    Em operacao (None) todas as origens valem. Na suite, cada execucao so
    enxerga os eventos que ela mesma gravou: o historico sintetico de um
    cenario cai no horario de outro, e sem esse filtro uma rodada contamina a
    seguinte.
    """
    if execucao_id is None:
        return None
    return [f"cenario:{execucao_id}", f"cenario-historico:{execucao_id}"]


def estado_via(
    conn: psycopg.Connection, agora: datetime, desde: datetime | None = None,
    origens: list[str] | None = None, *, ponto_id: int,
) -> EstadoVia:
    """Estado da via para UM ponto de luz, a partir dos trechos dele.

    Cada evento e a leitura de um trecho: pessoas na area e ocorrencia em
    curso (DIVERGENCIAS 55). O ponto enxerga os trechos associados a ele em
    trecho_ponto (DIVERGENCIAS 54). Em cada trecho vale a leitura mais recente
    ainda vigente (sem vigente_ate, VALIDADE_LEITURA_S); entre os trechos,
    pelo lado seguro: ha presenca se houver alguem em QUALQUER trecho, e
    ocorrencia se QUALQUER trecho a reportar. Sem leitura vigente em nenhum
    trecho, nao ha dado (e o ciclo decide 1,0).

    `desde` limita a janela de eventos considerada. Em operacao e None. O
    executor de cenarios passa o inicio da execucao, para que um cenario nao
    enxergue as leituras de outro.
    """
    linhas = conn.execute(
        """
        SELECT DISTINCT ON (e.trecho_id) e.id, e.trecho_id, e.pessoas, e.ocorrencia
          FROM evento_urbano e
          JOIN trecho_ponto tp ON tp.trecho_id = e.trecho_id
         WHERE tp.ponto_de_luz_id = %(ponto)s
           AND e.ocorrido_em <= %(agora)s
           AND (%(desde)s::timestamptz IS NULL OR e.ocorrido_em >= %(desde)s)
           AND (%(origens)s::text[] IS NULL OR e.origem = ANY(%(origens)s))
           AND COALESCE(e.vigente_ate, e.ocorrido_em + %(validade)s) > %(agora)s
         ORDER BY e.trecho_id, e.ocorrido_em DESC, e.id DESC
        """,
        {"agora": agora, "desde": desde, "origens": origens, "ponto": ponto_id,
         "validade": timedelta(seconds=config.VALIDADE_LEITURA_S)},
    ).fetchall()
    return EstadoVia(
        presenca=any(pessoas >= 1 for _, _, pessoas, _ in linhas),
        ocorrencia=any(oc is not None for *_, oc in linhas),
        pessoas={trecho: pessoas for _, trecho, pessoas, _ in linhas},
        evento_ids=sorted(eid for eid, *_ in linhas),
    )


def referencias(
    conn: psycopg.Connection, agora: datetime, ponto_id: int, origens: list[str] | None = None
) -> dict[int, float]:
    """Referencia de cada trecho do ponto: o "cheio" tipico daquela via.

    Percentil 99 da media horaria de pessoas nos ultimos DIAS_REFERENCIA dias
    - o mesmo criterio da normalizacao do treino (3.6) -, quando ha ao menos
    HORAS_MINIMAS_REFERENCIA horas com leitura; antes disso, o valor inicial
    declarado em trecho_via.referencia_pessoas.
    """
    linhas = conn.execute(
        """
        SELECT t.id, t.referencia_pessoas,
               (SELECT percentile_cont(0.99) WITHIN GROUP (ORDER BY h.media)
                  FROM (SELECT avg(e.pessoas) AS media
                          FROM evento_urbano e
                         WHERE e.trecho_id = t.id
                           AND e.ocorrido_em <= %(agora)s
                           AND e.ocorrido_em > %(agora)s - make_interval(days => %(dias)s)
                           AND (%(origens)s::text[] IS NULL OR e.origem = ANY(%(origens)s))
                         GROUP BY date_trunc('hour', e.ocorrido_em)) h
                HAVING count(*) >= %(minimo)s) AS aprendida
          FROM trecho_via t
          JOIN trecho_ponto tp ON tp.trecho_id = t.id AND tp.ponto_de_luz_id = %(ponto)s
        """,
        {"agora": agora, "dias": config.DIAS_REFERENCIA, "minimo": config.HORAS_MINIMAS_REFERENCIA,
         "origens": origens, "ponto": ponto_id},
    ).fetchall()
    return {t: float(aprendida) if aprendida and aprendida > 0 else float(inicial)
            for t, inicial, aprendida in linhas}


def historico_horario(
    conn: psycopg.Connection, agora: datetime, horas: int, origens: list[str] | None = None,
    *, ponto_id: int, refs: dict[int, float] | None = None,
) -> dict[int, float]:
    """Nivel de movimentacao por hora CHEIA DE RELOGIO anterior a `agora`,
    para um ponto de luz - a serie que alimenta a previsao.

    Chave = atraso em horas (1 = hora de relogio anterior); a hora em curso,
    incompleta, nao entra. Em cada hora e trecho, media de pessoas das
    leituras dividida pela referencia do trecho (limitada a 1); entre os
    trechos do ponto, a maior. E a mesma escala do treino (3.6).
    """
    refs = refs if refs is not None else referencias(conn, agora, ponto_id, origens)
    linhas = conn.execute(
        """
        SELECT e.trecho_id,
               (extract(epoch FROM (date_trunc('hour', %(agora)s)
                                    - date_trunc('hour', e.ocorrido_em))) / 3600)::int AS atraso,
               avg(e.pessoas) AS media
          FROM evento_urbano e
          JOIN trecho_ponto tp ON tp.trecho_id = e.trecho_id
         WHERE tp.ponto_de_luz_id = %(ponto)s
           AND e.ocorrido_em <= %(agora)s
           AND e.ocorrido_em > %(agora)s - make_interval(hours => %(horas)s)
           AND (%(origens)s::text[] IS NULL OR e.origem = ANY(%(origens)s))
         GROUP BY 1, 2
        """,
        {"agora": agora, "horas": horas + 1, "origens": origens, "ponto": ponto_id},
    ).fetchall()
    serie: dict[int, float] = {}
    for trecho, atraso, media in linhas:
        if atraso < 1 or media is None or trecho not in refs:
            continue
        nivel = min(float(media) / refs[trecho], 1.0)
        serie[atraso] = max(serie.get(atraso, 0.0), nivel)
    return serie


def nivel_recente(
    conn: psycopg.Connection, agora: datetime, origens: list[str] | None = None,
    *, ponto_id: int, refs: dict[int, float] | None = None, minutos: int = 60,
) -> float | None:
    """Nivel normalizado da ultima hora corrida: entra no lugar da previsao no
    modo reativo (H3) e quando o modelo nao tem historico. None sem leitura."""
    refs = refs if refs is not None else referencias(conn, agora, ponto_id, origens)
    linhas = conn.execute(
        """
        SELECT e.trecho_id, avg(e.pessoas)
          FROM evento_urbano e
          JOIN trecho_ponto tp ON tp.trecho_id = e.trecho_id
         WHERE tp.ponto_de_luz_id = %(ponto)s
           AND e.ocorrido_em <= %(agora)s
           AND e.ocorrido_em > %(agora)s - make_interval(mins => %(minutos)s)
           AND (%(origens)s::text[] IS NULL OR e.origem = ANY(%(origens)s))
         GROUP BY 1
        """,
        {"agora": agora, "minutos": minutos, "origens": origens, "ponto": ponto_id},
    ).fetchall()
    niveis = [min(float(m) / refs[tr], 1.0) for tr, m in linhas if m is not None and tr in refs]
    return max(niveis) if niveis else None


# ---------------------------------------------------------------------------
# Decisao
# ---------------------------------------------------------------------------
def _referencia_de_taxa(
    conn: psycopg.Connection, ponto: Ponto, agora: datetime, execucao_id: int | None = None
) -> tuple[Decimal | None, Decimal | None]:
    """Nivel anterior e intervalo para o limite de taxa.

    E a ultima decisao ANTERIOR a `agora` - decisao com carimbo futuro nao e
    "nivel corrente" e travaria a rampa (o intervalo daria zero). Dentro de
    um cenario, a referencia e a da propria execucao: duas execucoes com
    relogios virtuais distintos nao sao uma sequencia fisica.

    Se a ultima decisao e mais velha que o timeout do failsafe, o no ja
    voltou sozinho a 1,0 (RNF07): a rampa recomeca do pleno, e nao do ultimo
    valor gravado - senao a luz cairia de 1,0 ao nivel antigo num passo so.
    """
    ultima = conn.execute(
        """
        SELECT nivel_emitido, criado_em FROM decisao
         WHERE ponto_de_luz_id = %(ponto)s
           AND criado_em <= %(agora)s
           AND (%(execucao)s::bigint IS NULL OR execucao_id = %(execucao)s)
         ORDER BY criado_em DESC LIMIT 1
        """,
        {"ponto": ponto.id, "agora": agora, "execucao": execucao_id},
    ).fetchone()
    if ultima is None:
        return None, None
    nivel, quando = ultima
    segundos = Decimal(str(max((agora - quando).total_seconds(), 0)))
    if segundos > Decimal(str(config.TIMEOUT_FAILSAFE_S)):
        return PLENO, Decimal(str(config.PERIODO_S))
    return Decimal(nivel), segundos


def decidir(
    conn: psycopg.Connection,
    *,
    base: BaseRegras,
    previsor: Previsor,
    ponto: Ponto,
    agora: datetime,
    versao_regras_id: int,
    versao_modelo_id: int,
    execucao_id: int | None = None,
    reativo: bool = False,
    desde: datetime | None = None,
) -> DecisaoTomada:
    origens = origens_da_execucao(execucao_id)
    estado = estado_via(conn, agora, desde, origens, ponto_id=ponto.id)
    local = agora.astimezone(config.FUSO)

    previsao: float | None = None
    recente: float | None = None
    ativacoes: dict[str, float] = {}
    if estado.sem_dado:
        # Sem leitura vigente nao se dimeriza (DIVERGENCIAS 23).
        pretendido = PLENO
    else:
        refs = referencias(conn, agora, ponto.id, origens)
        recente = nivel_recente(conn, agora, origens, ponto_id=ponto.id, refs=refs)
        if not reativo and recente is not None:
            horas = getattr(previsor, "horas_necessarias", lambda: 24)()
            previsao = previsor.prever(
                Historico(
                    momento=local,
                    observada=recente,
                    serie=historico_horario(conn, agora, horas, origens, ponto_id=ponto.id, refs=refs),
                )
            )
        resultado = inferir(
            base,
            Entrada(presenca=estado.presenca, prevista=previsao, ocorrencia=estado.ocorrencia,
                    momento=local, recente=recente),
        )
        pretendido = resultado.nivel_pretendido
        ativacoes = {k: round(v, 4) for k, v in resultado.ativacoes.items()}

    # O porque da decisao, gravado junto dela (painel e RNF04).
    entrada = {
        "presenca": estado.presenca,
        "ocorrencia": estado.ocorrencia,
        "pessoas_por_trecho": {str(k): v for k, v in estado.pessoas.items()},
        "prevista": None if previsao is None else round(previsao, 4),
        "recente": None if recente is None else round(recente, 4),
        "horas_desde_18h": horas_desde_18h(local),
        "modo": "reativo" if reativo else "antecipado",
        "sem_dado": estado.sem_dado,
    }

    anterior, segundos = _referencia_de_taxa(conn, ponto, agora, execucao_id)
    r = verificar(
        pretendido,
        criterio(conn, ponto.classe_codigo),
        nivel_anterior=anterior,
        segundos_desde_anterior=segundos,
    )

    did = uuid.uuid4()
    conn.execute(
        """
        INSERT INTO decisao
            (id, criado_em, ponto_de_luz_id, versao_base_regras_id, versao_modelo_id,
             execucao_id, classe_codigo, previsao_movimentacao, nivel_pretendido,
             nivel_emitido, restricao_aplicada, nivel_anterior, entrada, ativacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (did, agora, ponto.id, versao_regras_id, versao_modelo_id, execucao_id,
         ponto.classe_codigo, previsao, pretendido, r.nivel_emitido,
         r.restricao_aplicada, anterior, Jsonb(entrada), Jsonb(ativacoes) if ativacoes else None),
    )
    for eid in estado.evento_ids:
        conn.execute("INSERT INTO decisao_evento VALUES (%s, %s)", (did, eid))

    return DecisaoTomada(
        id=did,
        ponto=ponto,
        criado_em=agora,
        nivel_pretendido=pretendido,
        nivel_emitido=r.nivel_emitido,
        restricao_aplicada=r.restricao_aplicada,
        nivel_anterior=anterior,
        estado=estado,
    )


def marcar_publicada(conn: psycopg.Connection, decisao_id: uuid.UUID, quando: datetime) -> None:
    conn.execute("UPDATE decisao SET publicado_em = %s WHERE id = %s", (quando, decisao_id))


# ---------------------------------------------------------------------------
# Retorno do no
# ---------------------------------------------------------------------------
def registrar_telemetria(conn: psycopg.Connection, ponto_codigo: str, carga: dict) -> bool:
    """Grava a telemetria de uma decisao (1:1). Devolve False se descartada.

    QoS 1 pode reentregar a mesma mensagem: a duplicata e ignorada pela
    unicidade de decisao_id. A telemetria so e aceita do proprio ponto que
    recebeu a decisao, e e ligada a sessao de medicao aberta, se houver.
    """
    try:
        did = uuid.UUID(str(carga["decisao_id"]))
        duty = float(carga["duty"])
        lux = float(carga["lux"])
        medido_em = datetime.fromisoformat(carga["medido_em"]) if carga.get("medido_em") else None
    except (KeyError, ValueError, TypeError) as erro:
        log.warning("telemetria malformada de %s: %s", ponto_codigo, erro)
        return False
    if not (0 <= duty <= 1) or lux < 0:
        log.warning("telemetria fora do dominio de %s: duty=%s lux=%s", ponto_codigo, duty, lux)
        return False
    if medido_em is not None and medido_em.tzinfo is None:
        medido_em = None  # relogio do no sem fuso: nao confiavel

    linha = conn.execute(
        """
        INSERT INTO telemetria (decisao_id, ponto_de_luz_id, sessao_id, medido_em, duty, lux_medido)
        SELECT d.id, d.ponto_de_luz_id,
               (SELECT s.id FROM sessao_medicao s
                 WHERE s.ponto_de_luz_id = d.ponto_de_luz_id AND s.encerrada_em IS NULL
                 ORDER BY s.iniciada_em DESC LIMIT 1),
               COALESCE(%(medido_em)s, now()), %(duty)s, %(lux)s
          FROM decisao d
          JOIN ponto_de_luz p ON p.id = d.ponto_de_luz_id
         WHERE d.id = %(did)s AND p.codigo = %(ponto)s
        ON CONFLICT (decisao_id) DO NOTHING
        RETURNING id
        """,
        {"did": did, "ponto": ponto_codigo, "duty": duty, "lux": lux, "medido_em": medido_em},
    ).fetchone()
    return linha is not None


def atualizar_estado_ponto(conn: psycopg.Connection, ponto_codigo: str, online: bool) -> None:
    """Last will do no (LACUNA 2): sem conexao -> 'sem_comunicacao'."""
    conn.execute(
        """
        UPDATE ponto_de_luz
           SET estado_operacional = CASE WHEN %(online)s THEN 'operante' ELSE 'sem_comunicacao' END
         WHERE codigo = %(ponto)s AND estado_operacional IN ('operante', 'sem_comunicacao')
        """,
        {"online": online, "ponto": ponto_codigo},
    )
