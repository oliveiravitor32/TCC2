"""Diagnostico do ponto de luz (TCC 3.4.5, RF11).

O sensor de iluminancia existe para verificar a execucao da decisao; a mesma
grandeza sustenta a funcao de gestao do ativo que a telegestao contratada
exerce (2.3). Tres diagnosticos, todos derivados da comparacao entre o nivel
COMANDADO e a iluminancia MEDIDA:

  1. falha total     - comando nao nulo e leitura equivalente a residual:
                       luminaria apagada;
  2. divergencia     - razao entre o entregue e o esperado, a cada ciclo;
  3. perda de controle - divergencia acima da tolerancia por N ciclos.

Duas propriedades do arranjo (3.4.4) tornam isso exequivel com a cadeia de
medicao disponivel:

  - o diagnostico opera sobre RAZAO, e um erro sistematico de escala do
    sensor cancela-se na razao;
  - a tolerancia nao e arbitrada: e a dispersao do ensaio de repetibilidade
    multiplicada por K_SIGMA, de modo que o alerta nao seja disparado pelo
    proprio instrumento.

O alerta REGISTRA, nao atua: nada aqui altera o nivel de iluminacao. Quem
protege a via contra falha de comando e o failsafe do no (RNF07).
"""

from __future__ import annotations

import logging
import statistics
import uuid
from dataclasses import dataclass, field
from typing import Literal

import psycopg

from . import config

__all__ = ["Limiares", "Leitura", "classificar", "Monitor", "tolerancia_do_ponto"]

log = logging.getLogger(__name__)

Diagnostico = Literal["normal", "falha_total", "divergente"]

# Abaixo desta fracao do esperado, a leitura e equivalente a residual: a
# luminaria esta apagada, nao "bem abaixo do comandado".
FRACAO_APAGADA = 0.1


@dataclass(frozen=True)
class Limiares:
    tolerancia: float  # fracao: 0,15 = 15 % de divergencia admitida
    ciclos_falha: int = config.CICLOS_FALHA_TOTAL
    ciclos_perda: int = config.CICLOS_PERDA_CONTROLE


@dataclass(frozen=True)
class Leitura:
    """Uma telemetria ja descontada da residual da sessao."""

    nivel_emitido: float
    lux_esperado: float  # nivel_emitido x iluminancia da classe
    lux_liquido: float   # lux medido - residual da sessao

    @property
    def razao(self) -> float | None:
        if self.lux_esperado <= 0:
            return None
        return self.lux_liquido / self.lux_esperado


def classificar(l: Leitura, lim: Limiares) -> Diagnostico:
    """Diagnostico de UMA leitura (os contadores ficam no Monitor)."""
    if l.nivel_emitido <= 0 or l.lux_esperado <= 0:
        return "normal"  # nada foi comandado: nada a verificar
    if l.lux_liquido <= FRACAO_APAGADA * l.lux_esperado:
        return "falha_total"
    razao = l.razao
    if razao is not None and abs(razao - 1.0) > lim.tolerancia:
        return "divergente"
    return "normal"


# ---------------------------------------------------------------------------
# Tolerancia vinda da bancada
# ---------------------------------------------------------------------------
def tolerancia_do_ponto(conn: psycopg.Connection, ponto_de_luz_id: int) -> float:
    """Tolerancia do diagnostico, derivada da bancada (3.4.4, 3.4.5).

    E o MAIOR entre dois valores:

      - K_SIGMA x a maior dispersao relativa entre series, considerando so a
        sessao de calibracao MAIS RECENTE e so os pontos da FAIXA DE OPERACAO
        (iluminancia media no piso ou acima). Fora dela a conta nao tem
        sentido: a 0,3 lx um unico degrau do sensor ja vale 38 %, e esse
        ponto inflaria a tolerancia para dezenas de por cento;
      - o piso de resolucao: DEGRAUS_TOLERANCIA degraus do sensor divididos
        pela iluminancia do piso. Abaixo disso o alerta seria disparado pela
        quantizacao do proprio instrumento.

    Sem calibracao gravada, devolve a tolerancia provisoria e avisa.
    """
    piso = conn.execute(
        """
        SELECT COALESCE(cm.iluminancia_media_min_lux, c.iluminancia_media_min_lux)
          FROM ponto_de_luz p
          JOIN classe_iluminacao c       ON c.codigo = p.classe_codigo
          LEFT JOIN classe_iluminacao cm ON cm.codigo = c.classe_min_dimerizacao
         WHERE p.id = %s
        """,
        (ponto_de_luz_id,),
    ).fetchone()
    lux_piso = float(piso[0]) if piso else None

    linhas = conn.execute(
        """
        WITH ultima AS (
            SELECT s.id, s.lux_residual FROM sessao_medicao s
             WHERE s.ponto_de_luz_id = %s AND NOT s.descartada
               AND EXISTS (SELECT 1 FROM calibracao c WHERE c.sessao_id = s.id)
             ORDER BY s.iniciada_em DESC LIMIT 1
        )
        SELECT c.duty, array_agg(c.lux_medido - u.lux_residual)
          FROM calibracao c JOIN ultima u ON u.id = c.sessao_id
         GROUP BY c.duty
        HAVING count(*) > 1
        """,
        (ponto_de_luz_id,),
    ).fetchall()
    if not linhas or not lux_piso:
        log.info("sem ensaio de repetibilidade; tolerancia provisoria de %.0f %%",
                 config.TOLERANCIA_PROVISORIA * 100)
        return config.TOLERANCIA_PROVISORIA

    dispersoes = []
    for _duty, valores in linhas:
        v = [float(x) for x in valores]
        media = statistics.fmean(v)
        if media >= lux_piso * 0.98:  # faixa de operacao (folga de meio degrau)
            dispersoes.append(statistics.stdev(v) / media)

    pela_dispersao = config.K_SIGMA * max(dispersoes, default=0.0)
    pela_resolucao = config.DEGRAUS_TOLERANCIA * config.RESOLUCAO_SENSOR_LUX / lux_piso
    return max(pela_dispersao, pela_resolucao)


# ---------------------------------------------------------------------------
# Monitor: contadores por ponto e escrita dos alertas
# ---------------------------------------------------------------------------
@dataclass
class _Contadores:
    falha: int = 0
    perda: int = 0


@dataclass
class Monitor:
    """Acompanha os ciclos consecutivos e mantem os alertas abertos/fechados."""

    limiares: dict[int, Limiares] = field(default_factory=dict)
    _cont: dict[int, _Contadores] = field(default_factory=dict)

    def limiar(self, conn: psycopg.Connection, ponto_id: int) -> Limiares:
        if ponto_id not in self.limiares:
            self.limiares[ponto_id] = Limiares(tolerancia_do_ponto(conn, ponto_id))
        return self.limiares[ponto_id]

    def avaliar(self, conn: psycopg.Connection, decisao_id: uuid.UUID) -> Diagnostico | None:
        """Avalia a telemetria de uma decisao e atualiza alertas.

        Devolve o diagnostico da leitura, ou None se ainda nao ha telemetria
        (ou se a decisao nao existe).
        """
        linha = conn.execute(
            """
            SELECT d.ponto_de_luz_id, d.nivel_emitido,
                   d.nivel_emitido * c.iluminancia_media_min_lux AS lux_esperado,
                   t.lux_medido - COALESCE(s.lux_residual, 0)     AS lux_liquido
              FROM decisao d
              JOIN classe_iluminacao c ON c.codigo = d.classe_codigo
              JOIN telemetria t        ON t.decisao_id = d.id
              LEFT JOIN sessao_medicao s ON s.id = t.sessao_id
             WHERE d.id = %s
            """,
            (decisao_id,),
        ).fetchone()
        if linha is None:
            return None
        ponto_id, nivel, esperado, liquido = linha
        leitura = Leitura(float(nivel), float(esperado), float(liquido))
        lim = self.limiar(conn, ponto_id)
        diag = classificar(leitura, lim)

        c = self._cont.setdefault(ponto_id, _Contadores())
        c.falha = c.falha + 1 if diag == "falha_total" else 0
        c.perda = c.perda + 1 if diag in ("falha_total", "divergente") else 0

        if diag == "falha_total" and c.falha == lim.ciclos_falha:
            self._abrir(conn, ponto_id, decisao_id, "falha_total", leitura, lim, c.falha)
        elif diag == "divergente" and c.perda == lim.ciclos_perda:
            self._abrir(conn, ponto_id, decisao_id, "perda_controle", leitura, lim, c.perda)
        elif diag == "normal":
            self._fechar(conn, ponto_id)
        return diag

    def _abrir(self, conn, ponto_id, decisao_id, tipo, leitura, lim, ciclos) -> None:
        # Um alerta aberto por tipo e por ponto: o segundo seria ruido.
        aberto = conn.execute(
            "SELECT 1 FROM alerta_diagnostico"
            " WHERE ponto_de_luz_id = %s AND tipo = %s AND encerrado_em IS NULL",
            (ponto_id, tipo),
        ).fetchone()
        if aberto:
            return
        conn.execute(
            "INSERT INTO alerta_diagnostico"
            " (ponto_de_luz_id, decisao_id, tipo, razao, tolerancia, ciclos)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            (ponto_id, decisao_id, tipo, leitura.razao, lim.tolerancia, ciclos),
        )
        if tipo == "falha_total":
            # Se a telemetria chegou, o no comunica: a falha da luminaria
            # prevalece sobre 'sem_comunicacao'. 'manutencao' e estado
            # declarado por pessoa e nao e sobrescrito.
            conn.execute(
                "UPDATE ponto_de_luz SET estado_operacional = 'falha'"
                " WHERE id = %s AND estado_operacional IN ('operante', 'sem_comunicacao')",
                (ponto_id,),
            )
        log.warning("alerta %s no ponto %s: razao=%.3f tolerancia=%.3f apos %d ciclos",
                    tipo, ponto_id, leitura.razao or -1, lim.tolerancia, ciclos)

    def _fechar(self, conn, ponto_id: int) -> None:
        fechados = conn.execute(
            "UPDATE alerta_diagnostico SET encerrado_em = now()"
            " WHERE ponto_de_luz_id = %s AND encerrado_em IS NULL RETURNING tipo",
            (ponto_id,),
        ).fetchall()
        if fechados:
            conn.execute(
                "UPDATE ponto_de_luz SET estado_operacional = 'operante'"
                " WHERE id = %s AND estado_operacional = 'falha'",
                (ponto_id,),
            )
            log.info("ponto %s normalizado; alertas encerrados: %s",
                     ponto_id, [t for (t,) in fechados])
