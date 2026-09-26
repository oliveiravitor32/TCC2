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

from . import config
from .inferencia import BaseRegras, Entrada, inferir
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
    observada: float | None  # None = sem dado de movimentacao vigente
    ocorrencia: bool
    evento_ids: list[int] = field(default_factory=list)


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
def estado_via(
    conn: psycopg.Connection, agora: datetime, desde: datetime | None = None
) -> EstadoVia:
    """Ultimo evento vigente de cada tipo.

    - movimentacao sem vigente_ate vale VALIDADE_MOVIMENTACAO_S; vencida, nao
      ha dado (e o ciclo decide 1,0);
    - ocorrencia sem vigente_ate vale ate o proximo evento do mesmo tipo
      ('encerrada'): na duvida, a condicao de risco permanece.

    `desde` limita a janela de eventos considerada. Em operacao e None (o
    estado da via nao "recomeca"). O executor de cenarios passa o inicio da
    execucao: uma chuva declarada em outro cenario, e nunca encerrada, ficaria
    vigente para sempre e contaminaria os cenarios seguintes.
    """
    linhas = conn.execute(
        """
        SELECT DISTINCT ON (tipo) id, tipo, valor, rotulo
          FROM evento_urbano
         WHERE ocorrido_em <= %(agora)s
           AND (%(desde)s::timestamptz IS NULL OR ocorrido_em >= %(desde)s)
           AND COALESCE(vigente_ate,
                        CASE WHEN tipo = 'movimentacao'
                             THEN ocorrido_em + %(validade)s
                        END,
                        'infinity') > %(agora)s
         ORDER BY tipo, ocorrido_em DESC, id DESC
        """,
        {"agora": agora, "desde": desde,
         "validade": timedelta(seconds=config.VALIDADE_MOVIMENTACAO_S)},
    ).fetchall()
    por_tipo = {tipo: (eid, valor, rotulo) for eid, tipo, valor, rotulo in linhas}

    mov = por_tipo.get("movimentacao")
    oco = por_tipo.get("ocorrencia")
    return EstadoVia(
        observada=None if mov is None else float(mov[1]),
        ocorrencia=oco is not None and oco[2] != "encerrada",
        evento_ids=sorted(e[0] for e in por_tipo.values()),
    )


def historico_horario(conn: psycopg.Connection, agora: datetime, horas: int) -> dict[int, float]:
    """Nivel medio de movimentacao por hora CHEIA DE RELOGIO anterior a `agora`.

    Chave = atraso em horas (1 = hora de relogio anterior). O modelo foi
    treinado sobre janelas horarias fechadas (3.6), entao o agrupamento
    precisa ser por hora do relogio, e nao por diferenca corrida: a hora em
    curso e incompleta e nao entra.
    """
    linhas = conn.execute(
        """
        SELECT (extract(epoch FROM (date_trunc('hour', %(agora)s)
                                    - date_trunc('hour', ocorrido_em))) / 3600)::int AS atraso,
               avg(valor) AS nivel
          FROM evento_urbano
         WHERE tipo = 'movimentacao'
           AND ocorrido_em <= %(agora)s
           AND ocorrido_em > %(agora)s - make_interval(hours => %(horas)s)
         GROUP BY 1
        """,
        {"agora": agora, "horas": horas + 1},
    ).fetchall()
    return {int(a): float(n) for a, n in linhas if a >= 1 and n is not None}


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
    estado = estado_via(conn, agora, desde)

    previsao: float | None = None
    if estado.observada is None:
        # Sem dado de movimentacao nao se dimeriza (DIVERGENCIAS 23).
        pretendido = PLENO
    else:
        if reativo:
            previsao = None
        else:
            horas = getattr(previsor, "horas_necessarias", lambda: 24)()
            previsao = previsor.prever(
                Historico(
                    momento=agora.astimezone(config.FUSO),
                    observada=estado.observada,
                    serie=historico_horario(conn, agora, horas),
                )
            )
        pretendido = inferir(
            base,
            Entrada(
                observada=estado.observada,
                prevista=previsao,
                ocorrencia=estado.ocorrencia,
                momento=agora.astimezone(config.FUSO),
            ),
        ).nivel_pretendido

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
             nivel_emitido, restricao_aplicada, nivel_anterior)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (did, agora, ponto.id, versao_regras_id, versao_modelo_id, execucao_id,
         ponto.classe_codigo, previsao, pretendido, r.nivel_emitido,
         r.restricao_aplicada, anterior),
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
