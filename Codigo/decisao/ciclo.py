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
from typing import Callable

import psycopg
from psycopg.types.json import Jsonb

from . import config
from .inferencia import BaseRegras, Entrada, horas_desde_18h, inferir
from .previsao import Historico, Previsor
from .rampa import Comando
from .verificacao import PLENO, Criterio, verificar

log = logging.getLogger(__name__)



class BaseRegrasAlterada(RuntimeError):
    """O arquivo de regras mudou sem nova versao: quebraria o RNF04."""


@dataclass(frozen=True)
class Ponto:
    id: int
    codigo: str
    classe_codigo: str
    # Grupo de controle (DIVERGENCIAS 76); None = decide sozinho.
    grupo_id: int | None = None


@dataclass(frozen=True)
class EstadoVia:
    """Publicacoes vigentes dos trechos de um ponto (DIVERGENCIAS 56)."""

    ocorrencia: bool  # alguma ocorrencia aberta em algum trecho do ponto
    # Media de pessoas do volume vigente de cada trecho; vazio = sem dado.
    volumes: dict[int, float] = field(default_factory=dict)
    evento_ids: list[int] = field(default_factory=list)
    # Quando vence o volume vigente que vence por ultimo (None sem dado): a
    # validade do comando nao passa dele (DIVERGENCIAS 71).
    volume_vence_em: datetime | None = None

    @property
    def sem_dado(self) -> bool:
        return not self.volumes


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
    # Volume observado normalizado (None sem dado) e degrau defuzificado.
    observada: float | None = None
    degrau: float | None = None
    validade_s: int = 0
    criterio: Criterio | None = None

    def comando(self) -> dict:
        """Carga do topico iluminacao/{ponto}/comando (Quadro 14, item 71):
        alvo verificado, validade e os limites que o controlador tambem impoe."""
        return self.comando_obj().carga()

    def comando_obj(self) -> Comando:
        return Comando(str(self.id), self.nivel_emitido, self.validade_s,
                       self.criterio.piso, self.criterio.taxa_max_decrescimo_min)


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
            "SELECT id, codigo, classe_codigo, grupo_id FROM ponto_de_luz"
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


def niveis_classe(conn: psycopg.Connection, classe: str) -> tuple[Decimal, Decimal, Decimal]:
    """Os tres degraus da saida da inferencia, como fracao do pleno (RF09).

    (classe da via, uma classe abaixo, classe minima admitida), lidos de
    classe_iluminacao: "uma abaixo" e a classe de maior iluminancia menor que
    a da via e nao menor que a minima. Com menos degraus, os valores se
    repetem (ex.: P3 -> 1, 0,75, 0,5; nao dimerizavel -> 1, 1, 1). A norma
    admite descer no maximo duas classes (6.10.2): tres degraus bastam.
    """
    lux, lux_min = conn.execute(
        """
        SELECT c.iluminancia_media_min_lux, cm.iluminancia_media_min_lux
          FROM classe_iluminacao c
          LEFT JOIN classe_iluminacao cm ON cm.codigo = c.classe_min_dimerizacao
         WHERE c.codigo = %s
        """,
        (classe,),
    ).fetchone()
    if lux_min is None:
        return PLENO, PLENO, PLENO
    (lux_meio,) = conn.execute(
        """
        SELECT max(iluminancia_media_min_lux) FROM classe_iluminacao
         WHERE iluminancia_media_min_lux < %(lux)s AND iluminancia_media_min_lux >= %(min)s
        """,
        {"lux": lux, "min": lux_min},
    ).fetchone()
    lux, lux_min = Decimal(lux), Decimal(lux_min)
    meio = Decimal(lux_meio) if lux_meio is not None else lux_min
    return PLENO, meio / lux, lux_min / lux


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

    Dois tipos de publicacao por trecho (DIVERGENCIAS 56): o VOLUME - media
    de pessoas na area num periodo de 5 min - e a OCORRENCIA, publicada na
    hora. O ponto enxerga os trechos associados a ele em trecho_ponto
    (DIVERGENCIAS 54).

    - Volume: em cada trecho vale o mais recente ainda vigente (sem
      vigente_ate, VALIDADE_VOLUME_S). Sem volume vigente em nenhum trecho,
      nao ha dado (e o ciclo decide o pleno).
    - Ocorrencia: em cada trecho vale a publicacao mais recente; esta aberta
      se nao for 'encerrada' e ainda estiver vigente (sem vigente_ate,
      VALIDADE_OCORRENCIA_S) - encerra o que vier primeiro. Ha ocorrencia se
      QUALQUER trecho tiver uma aberta (lado seguro).

    `desde` limita a janela de eventos considerada. Em operacao e None. O
    executor de cenarios passa o inicio da execucao, para que um cenario nao
    enxergue as publicacoes de outro.
    """
    filtro = {"agora": agora, "desde": desde, "origens": origens, "ponto": ponto_id}
    volumes = conn.execute(
        """
        SELECT DISTINCT ON (e.trecho_id) e.id, e.trecho_id, e.pessoas_media,
               COALESCE(e.vigente_ate, e.ocorrido_em + %(validade)s) AS vence
          FROM evento_urbano e
          JOIN trecho_ponto tp ON tp.trecho_id = e.trecho_id
         WHERE tp.ponto_de_luz_id = %(ponto)s
           AND e.tipo = 'volume'
           AND e.ocorrido_em <= %(agora)s
           AND (%(desde)s::timestamptz IS NULL OR e.ocorrido_em >= %(desde)s)
           AND (%(origens)s::text[] IS NULL OR e.origem = ANY(%(origens)s))
           AND COALESCE(e.vigente_ate, e.ocorrido_em + %(validade)s) > %(agora)s
         ORDER BY e.trecho_id, e.ocorrido_em DESC, e.id DESC
        """,
        {**filtro, "validade": timedelta(seconds=config.VALIDADE_VOLUME_S)},
    ).fetchall()
    ocorrencias = conn.execute(
        """
        SELECT o.id FROM (
            SELECT DISTINCT ON (e.trecho_id) e.id, e.ocorrencia, e.ocorrido_em, e.vigente_ate
              FROM evento_urbano e
              JOIN trecho_ponto tp ON tp.trecho_id = e.trecho_id
             WHERE tp.ponto_de_luz_id = %(ponto)s
               AND e.tipo = 'ocorrencia'
               AND e.ocorrido_em <= %(agora)s
               AND (%(desde)s::timestamptz IS NULL OR e.ocorrido_em >= %(desde)s)
               AND (%(origens)s::text[] IS NULL OR e.origem = ANY(%(origens)s))
             ORDER BY e.trecho_id, e.ocorrido_em DESC, e.id DESC
        ) o
         WHERE o.ocorrencia <> 'encerrada'
           AND COALESCE(o.vigente_ate, o.ocorrido_em + %(validade)s) > %(agora)s
        """,
        {**filtro, "validade": timedelta(seconds=config.VALIDADE_OCORRENCIA_S)},
    ).fetchall()
    return EstadoVia(
        ocorrencia=bool(ocorrencias),
        volumes={trecho: float(media) for _, trecho, media, _ in volumes},
        evento_ids=sorted([eid for eid, *_ in volumes] + [eid for (eid,) in ocorrencias]),
        volume_vence_em=max((v for *_, v in volumes), default=None),
    )


def observada(estado: EstadoVia, refs: dict[int, float]) -> float | None:
    """Volume observado do ponto, na escala do treino (3.6): media de cada
    trecho dividida pela referencia dele (limitada a 1); entre os trechos, a
    maior - o lado seguro."""
    niveis = [min(m / refs[t], 1.0) for t, m in estado.volumes.items() if t in refs]
    return max(niveis) if niveis else None


def referencias(
    conn: psycopg.Connection, agora: datetime, ponto_id: int, origens: list[str] | None = None
) -> dict[int, float]:
    """Regua de cada trecho do ponto, como a decisao a usa.

    Em operacao (origens None), a gravada pela rotina diaria
    (`atualizar_referencias`, DIVERGENCIAS 71): a aprendida, se ja houver;
    senao, o valor inicial. Numa execucao de cenario, calculada sobre os
    eventos da propria execucao (`calcular_referencias`).
    """
    if origens is not None:
        return calcular_referencias(conn, agora, ponto_id, origens)
    linhas = conn.execute(
        """
        SELECT t.id, COALESCE(t.referencia_aprendida, t.referencia_pessoas)
          FROM trecho_via t
          JOIN trecho_ponto tp ON tp.trecho_id = t.id AND tp.ponto_de_luz_id = %s
        """,
        (ponto_id,),
    ).fetchall()
    return {t: float(v) for t, v in linhas}


_SQL_P99 = """
    (SELECT percentile_cont(0.99) WITHIN GROUP (ORDER BY h.media)
       FROM (SELECT avg(e.pessoas_media) AS media
               FROM evento_urbano e
              WHERE e.trecho_id = t.id AND e.tipo = 'volume'
                AND e.ocorrido_em <= %(agora)s
                AND e.ocorrido_em > %(agora)s - make_interval(days => %(dias)s)
                AND (%(origens)s::text[] IS NULL OR e.origem = ANY(%(origens)s))
              GROUP BY date_bin(make_interval(mins => %(bloco)s), e.ocorrido_em,
                                TIMESTAMPTZ '2000-01-01 00:00+00')) h
     HAVING count(*) >= %(minimo)s)
"""


def _param_p99(agora: datetime, origens: list[str] | None) -> dict:
    return {"agora": agora, "dias": config.DIAS_REFERENCIA, "minimo": config.BLOCOS_MINIMOS_REFERENCIA,
            "bloco": config.BLOCO_PREVISAO_MIN, "origens": origens}


def atualizar_referencias(conn: psycopg.Connection, agora: datetime) -> int:
    """Rotina diaria (DIVERGENCIAS 71): grava a regua aprendida de todos os
    trechos. A regua muda devagar (percentil 99 de 28 dias); recalcula-la a
    cada decisao seria repetir a mesma conta. Devolve quantos trechos tem
    regua aprendida."""
    n = conn.execute(
        f"""
        UPDATE trecho_via t
           SET referencia_aprendida = NULLIF(GREATEST(COALESCE({_SQL_P99}, 0), 0), 0),
               referencia_calculada_em = %(agora)s
        """,
        _param_p99(agora, None),
    ).rowcount
    (com,) = conn.execute(
        "SELECT count(*) FROM trecho_via WHERE referencia_aprendida IS NOT NULL").fetchone()
    log.info("regua recalculada em %s trechos (%s com historico suficiente)", n, com)
    return com


def referencias_vencidas(conn: psycopg.Connection, agora: datetime) -> bool:
    (ultima,) = conn.execute("SELECT min(referencia_calculada_em) FROM trecho_via").fetchone()
    return ultima is None or (agora - ultima).total_seconds() >= config.REFERENCIA_A_CADA_S


def calcular_referencias(
    conn: psycopg.Connection, agora: datetime, ponto_id: int, origens: list[str] | None = None
) -> dict[int, float]:
    """Referencia de cada trecho do ponto: o "cheio" tipico daquela via.

    Percentil 99 da media de pessoas por bloco de BLOCO_PREVISAO_MIN minutos
    nos ultimos DIAS_REFERENCIA dias - o mesmo criterio da normalizacao do
    treino (3.6) -, quando ha ao menos BLOCOS_MINIMOS_REFERENCIA blocos com
    leitura; antes disso, o valor inicial declarado em
    trecho_via.referencia_pessoas.
    """
    linhas = conn.execute(
        f"""
        SELECT t.id, t.referencia_pessoas, {_SQL_P99} AS aprendida
          FROM trecho_via t
          JOIN trecho_ponto tp ON tp.trecho_id = t.id AND tp.ponto_de_luz_id = %(ponto)s
        """,
        {**_param_p99(agora, origens), "ponto": ponto_id},
    ).fetchall()
    return {t: float(aprendida) if aprendida and aprendida > 0 else float(inicial)
            for t, inicial, aprendida in linhas}


def historico_horario(
    conn: psycopg.Connection, agora: datetime, horas: int, origens: list[str] | None = None,
    *, ponto_id: int, refs: dict[int, float] | None = None,
) -> dict[int, float]:
    """Serie por hora cheia (o modelo horario de Melbourne, item 30)."""
    return historico(conn, agora, horas, origens, ponto_id=ponto_id, refs=refs, bloco_min=60)


def historico(
    conn: psycopg.Connection, agora: datetime, blocos: int, origens: list[str] | None = None,
    *, ponto_id: int, refs: dict[int, float] | None = None, bloco_min: int | None = None,
) -> dict[int, float]:
    """Nivel de movimentacao por BLOCO de relogio anterior a `agora`, para um
    ponto de luz - a serie que alimenta a previsao (DIVERGENCIAS 69: blocos
    de 15 min; 60 para o modelo horario).

    Chave = atraso em blocos (1 = bloco de relogio anterior); o bloco em
    curso, incompleto, nao entra. Em cada bloco e trecho, media de pessoas
    das leituras dividida pela referencia do trecho (limitada a 1); entre os
    trechos do ponto, a maior. E a mesma escala do treino (3.6).
    """
    bloco_min = bloco_min or config.BLOCO_PREVISAO_MIN
    refs = refs if refs is not None else referencias(conn, agora, ponto_id, origens)
    linhas = conn.execute(
        """
        SELECT e.trecho_id,
               (extract(epoch FROM (date_bin(make_interval(mins => %(bloco)s), %(agora)s,
                                             TIMESTAMPTZ '2000-01-01 00:00+00')
                                    - date_bin(make_interval(mins => %(bloco)s), e.ocorrido_em,
                                               TIMESTAMPTZ '2000-01-01 00:00+00')))
                / (60 * %(bloco)s))::int AS atraso,
               avg(e.pessoas_media) AS media
          FROM evento_urbano e
          JOIN trecho_ponto tp ON tp.trecho_id = e.trecho_id
         WHERE tp.ponto_de_luz_id = %(ponto)s AND e.tipo = 'volume'
           AND e.ocorrido_em <= %(agora)s
           AND e.ocorrido_em > %(agora)s - make_interval(mins => %(janela)s)
           AND (%(origens)s::text[] IS NULL OR e.origem = ANY(%(origens)s))
         GROUP BY 1, 2
        """,
        {"agora": agora, "janela": (blocos + 1) * bloco_min, "bloco": bloco_min,
         "origens": origens, "ponto": ponto_id},
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
    """Nivel normalizado da ultima hora corrida (media dos volumes), para
    consulta e auditoria. None sem volume na janela."""
    refs = refs if refs is not None else referencias(conn, agora, ponto_id, origens)
    linhas = conn.execute(
        """
        SELECT e.trecho_id, avg(e.pessoas_media)
          FROM evento_urbano e
          JOIN trecho_ponto tp ON tp.trecho_id = e.trecho_id
         WHERE tp.ponto_de_luz_id = %(ponto)s AND e.tipo = 'volume'
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
def _ultima_decisao(
    conn: psycopg.Connection, ponto: Ponto, agora: datetime, execucao_id: int | None = None
) -> Decimal | None:
    """Alvo da ultima decisao anterior a `agora`, so para registro.

    Desde o item 71 a taxa nao limita o alvo na central: quem desce em rampa
    e o controlador, a partir da luz que ele estiver aplicando.
    """
    ultima = conn.execute(
        """
        SELECT nivel_emitido FROM decisao
         WHERE ponto_de_luz_id = %(ponto)s
           AND criado_em <= %(agora)s
           AND (%(execucao)s::bigint IS NULL OR execucao_id = %(execucao)s)
         ORDER BY criado_em DESC LIMIT 1
        """,
        {"ponto": ponto.id, "agora": agora, "execucao": execucao_id},
    ).fetchone()
    return None if ultima is None else Decimal(ultima[0])


def validade(estado: EstadoVia, agora: datetime) -> int:
    """Validade do comando (DIVERGENCIAS 71): ate vencer o volume que o
    sustenta, no maximo VALIDADE_COMANDO_MAX_S; sem dado, o maximo (o alvo ja
    e o pleno)."""
    maximo = config.VALIDADE_COMANDO_MAX_S
    if estado.volume_vence_em is None:
        return maximo
    resta = int((estado.volume_vence_em - agora).total_seconds())
    return max(1, min(maximo, resta))


def ultimo_publicado(conn: psycopg.Connection, ponto_id: int) -> tuple[Decimal, datetime] | None:
    """(alvo, vence_em) do ultimo comando publicado ao ponto em operacao."""
    linha = conn.execute(
        """
        SELECT nivel_emitido, publicado_em + make_interval(secs => validade_s)
          FROM decisao
         WHERE ponto_de_luz_id = %s AND publicado_em IS NOT NULL AND validade_s IS NOT NULL
           AND execucao_id IS NULL
         ORDER BY publicado_em DESC LIMIT 1
        """,
        (ponto_id,),
    ).fetchone()
    return None if linha is None else (Decimal(linha[0]), linha[1])


def pontos_do_evento(conn: psycopg.Connection, evento_id: int) -> list[Ponto]:
    """Pontos de luz dos trechos de um evento: so eles decidem de novo."""
    return [Ponto(*l) for l in conn.execute(
        """
        SELECT p.id, p.codigo, p.classe_codigo, p.grupo_id
          FROM evento_urbano e
          JOIN trecho_ponto tp ON tp.trecho_id = e.trecho_id
          JOIN ponto_de_luz p ON p.id = tp.ponto_de_luz_id
         WHERE e.id = %s AND p.estado_operacional <> 'manutencao'
         ORDER BY p.id
        """,
        (evento_id,),
    ).fetchall()]


def pontos_vencendo(conn: psycopg.Connection, agora: datetime, antes_s: float) -> list[Ponto]:
    """Pontos cujo ultimo comando vence em ate `antes_s` (ou que nunca
    receberam comando): a varredura decide de novo so esses."""
    return [Ponto(*l) for l in conn.execute(
        """
        SELECT p.id, p.codigo, p.classe_codigo, p.grupo_id
          FROM ponto_de_luz p
          LEFT JOIN LATERAL (
                SELECT d.publicado_em + make_interval(secs => d.validade_s) AS vence
                  FROM decisao d
                 WHERE d.ponto_de_luz_id = p.id AND d.publicado_em IS NOT NULL
                   AND d.validade_s IS NOT NULL AND d.execucao_id IS NULL
                 ORDER BY d.publicado_em DESC LIMIT 1) u ON true
         WHERE p.estado_operacional <> 'manutencao'
           AND (u.vence IS NULL OR u.vence <= %(agora)s + make_interval(secs => %(antes)s))
         ORDER BY p.id
        """,
        {"agora": agora, "antes": antes_s},
    ).fetchall()]


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
    filtro_observada: Callable[[float], float] | None = None,
    refs: dict[int, float] | None = None,
) -> DecisaoTomada:
    av = _avaliar(conn, base=base, previsor=previsor, ponto=ponto, agora=agora,
                  execucao_id=execucao_id, reativo=reativo, desde=desde,
                  filtro_observada=filtro_observada, refs=refs)
    return _registrar(conn, av, ponto, agora, versao_regras_id, versao_modelo_id, execucao_id)


def decidir_grupo(
    conn: psycopg.Connection,
    pontos_do_grupo: list[Ponto],
    *,
    base: BaseRegras,
    previsor: Previsor,
    agora: datetime,
    versao_regras_id: int,
    versao_modelo_id: int,
    execucao_id: int | None = None,
    reativo: bool = False,
) -> list[DecisaoTomada]:
    """Uma decisao por grupo de controle (DIVERGENCIAS 76): a avaliacao
    (estado da via, previsao e inferencia) e feita uma vez, pelo primeiro ponto,
    e registrada para cada ponto do grupo. Pontos do grupo tem os mesmos trechos
    e a mesma classe, de modo que o resultado e identico ao de decidir ponto a
    ponto; muda so o custo. O nivel anterior e a publicacao continuam por ponto."""
    if not pontos_do_grupo:
        return []
    classes = {p.classe_codigo for p in pontos_do_grupo}
    if len(classes) != 1:
        raise ValueError(f"grupo com classes diferentes: {sorted(classes)}")
    av = _avaliar(conn, base=base, previsor=previsor, ponto=pontos_do_grupo[0], agora=agora,
                  execucao_id=execucao_id, reativo=reativo)
    return [_registrar(conn, av, p, agora, versao_regras_id, versao_modelo_id, execucao_id)
            for p in pontos_do_grupo]


@dataclass(frozen=True)
class _Avaliacao:
    estado: EstadoVia
    pretendido: Decimal
    previsao: float | None
    obs: float | None
    degrau: float | None
    ativacoes: dict
    entrada: dict


def _avaliar(
    conn: psycopg.Connection,
    *,
    base: BaseRegras,
    previsor: Previsor,
    ponto: Ponto,
    agora: datetime,
    execucao_id: int | None = None,
    reativo: bool = False,
    desde: datetime | None = None,
    filtro_observada: Callable[[float], float] | None = None,
    refs: dict[int, float] | None = None,
) -> _Avaliacao:
    """Estado da via, previsao e inferencia: depende so dos trechos e da
    classe do ponto, nada do ponto em si."""
    origens = origens_da_execucao(execucao_id)
    estado = estado_via(conn, agora, desde, origens, ponto_id=ponto.id)
    local = agora.astimezone(config.FUSO)

    niveis = niveis_classe(conn, ponto.classe_codigo)
    previsao: float | None = None
    obs: float | None = None
    degrau: float | None = None
    ativacoes: dict[str, float] = {}
    if estado.sem_dado:
        # Sem volume vigente nao se dimeriza (DIVERGENCIAS 23); ocorrencia
        # aberta, com ou sem volume, tambem leva ao pleno.
        pretendido = PLENO
    else:
        if refs is None:
            refs = referencias(conn, agora, ponto.id, origens)
        obs = observada(estado, refs)
        if filtro_observada is not None and obs is not None:
            # So na avaliacao (DIVERGENCIAS 61): alternativa simples com histerese.
            obs = filtro_observada(obs)
        if not reativo and obs is not None:
            bloco = getattr(previsor, "bloco_min", 60)
            blocos = getattr(previsor, "blocos_necessarios", lambda: 24)()
            previsao = previsor.prever(
                Historico(
                    momento=local,
                    observada=obs,
                    serie=historico(conn, agora, blocos, origens, ponto_id=ponto.id, refs=refs,
                                    bloco_min=bloco),
                )
            )
        resultado = inferir(
            base,
            Entrada(observada=obs, prevista=previsao, ocorrencia=estado.ocorrencia, momento=local),
            niveis,
        )
        pretendido = resultado.nivel_pretendido
        degrau = resultado.degrau
        ativacoes = {k: round(v, 4) for k, v in resultado.ativacoes.items()}

    # O porque da decisao, gravado junto dela (painel e RNF04).
    entrada = {
        "ocorrencia": estado.ocorrencia,
        "pessoas_media_por_trecho": {str(k): v for k, v in estado.volumes.items()},
        "observada": None if obs is None else round(obs, 4),
        "prevista": None if previsao is None else round(previsao, 4),
        "horas_desde_18h": horas_desde_18h(local),
        "modo": "reativo" if reativo else "antecipado",
        "sem_dado": estado.sem_dado,
        "niveis_classe": [float(n) for n in niveis],
        "degrau": degrau,
    }
    return _Avaliacao(estado=estado, pretendido=pretendido, previsao=previsao, obs=obs,
                      degrau=degrau, ativacoes=ativacoes, entrada=entrada)


def _registrar(
    conn: psycopg.Connection,
    av: _Avaliacao,
    ponto: Ponto,
    agora: datetime,
    versao_regras_id: int,
    versao_modelo_id: int,
    execucao_id: int | None,
) -> DecisaoTomada:
    """Verificacao do piso e gravacao da decisao de um ponto."""
    estado, pretendido, previsao = av.estado, av.pretendido, av.previsao
    obs, degrau, ativacoes, entrada = av.obs, av.degrau, av.ativacoes, av.entrada

    # A central verifica o PISO do alvo; a taxa de descida e garantida no
    # controlador, pela mesma regra (decisao.rampa, DIVERGENCIAS 71).
    anterior = _ultima_decisao(conn, ponto, agora, execucao_id)
    crit = criterio(conn, ponto.classe_codigo)
    r = verificar(pretendido, crit)
    val = validade(estado, agora)

    did = uuid.uuid4()
    conn.execute(
        """
        INSERT INTO decisao
            (id, criado_em, ponto_de_luz_id, versao_base_regras_id, versao_modelo_id,
             execucao_id, classe_codigo, previsao_movimentacao, nivel_pretendido,
             nivel_emitido, restricao_aplicada, nivel_anterior, entrada, ativacoes, validade_s,
             grupo_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (did, agora, ponto.id, versao_regras_id, versao_modelo_id, execucao_id,
         ponto.classe_codigo, previsao, pretendido, r.nivel_emitido,
         r.restricao_aplicada, anterior, Jsonb(entrada), Jsonb(ativacoes) if ativacoes else None,
         val, ponto.grupo_id),
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
        observada=obs,
        degrau=degrau,
        validade_s=val,
        criterio=crit,
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
        # Nivel que o no aplicava ao responder (item 71); ausente nos nos antigos.
        nivel = float(carga["nivel"]) if carga.get("nivel") is not None else None
        # Estado quando o comando chegou, antes de aplica-lo (migracao 010);
        # ausente nos nos antigos e no primeiro comando sem leitura previa.
        nivel_antes = float(carga["nivel_antes"]) if carga.get("nivel_antes") is not None else None
        lux_antes = float(carga["lux_antes"]) if carga.get("lux_antes") is not None else None
    except (KeyError, ValueError, TypeError) as erro:
        log.warning("telemetria malformada de %s: %s", ponto_codigo, erro)
        return False
    if (not (0 <= duty <= 1) or lux < 0 or (nivel is not None and not 0 <= nivel <= 1)
            or (nivel_antes is not None and not 0 <= nivel_antes <= 1)
            or (lux_antes is not None and lux_antes < 0)):
        log.warning("telemetria fora do dominio de %s: duty=%s lux=%s", ponto_codigo, duty, lux)
        return False
    if medido_em is not None and medido_em.tzinfo is None:
        medido_em = None  # relogio do no sem fuso: nao confiavel

    linha = conn.execute(
        """
        INSERT INTO telemetria (decisao_id, ponto_de_luz_id, sessao_id, medido_em, duty, lux_medido,
                                nivel_aplicado, nivel_antes, lux_antes)
        SELECT d.id, d.ponto_de_luz_id,
               (SELECT s.id FROM sessao_medicao s
                 WHERE s.ponto_de_luz_id = d.ponto_de_luz_id AND s.encerrada_em IS NULL
                 ORDER BY s.iniciada_em DESC LIMIT 1),
               COALESCE(%(medido_em)s, now()), %(duty)s, %(lux)s, %(nivel)s,
               %(nivel_antes)s, %(lux_antes)s
          FROM decisao d
          JOIN ponto_de_luz p ON p.id = d.ponto_de_luz_id
         WHERE d.id = %(did)s AND p.codigo = %(ponto)s
        ON CONFLICT (decisao_id) DO NOTHING
        RETURNING id
        """,
        {"did": did, "ponto": ponto_codigo, "duty": duty, "lux": lux, "medido_em": medido_em,
         "nivel": nivel, "nivel_antes": nivel_antes, "lux_antes": lux_antes},
    ).fetchone()
    return linha is not None


def atualizar_estado_ponto(conn: psycopg.Connection, ponto_codigo: str, online: bool,
                           manutencao: bool = False) -> None:
    """Estado retido do no.

    Last will (LACUNA 2): sem conexao -> 'sem_comunicacao'. Conferencia ou
    recalibracao pela serial (bancada/conferir.py) -> 'manutencao', para o
    painel nao confundir a pausa com defeito. 'falha' e posta a mao e nao e
    sobrescrita aqui.
    """
    novo = "manutencao" if manutencao else ("operante" if online else "sem_comunicacao")
    conn.execute(
        """
        UPDATE ponto_de_luz
           SET estado_operacional = %(novo)s
         WHERE codigo = %(ponto)s
           AND estado_operacional IN ('operante', 'sem_comunicacao', 'manutencao')
        """,
        {"novo": novo, "ponto": ponto_codigo},
    )
