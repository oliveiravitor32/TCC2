"""Camada de verificacao normativa (TCC 3.7).

Invariante de seguranca: nenhum nivel emitido pelo sistema pode violar os dois
limites abaixo, quaisquer que sejam a previsao e a inferencia nebulosa.

    1. piso  - o nivel emitido nunca fica abaixo do piso da classe minima de
               dimerizacao admitida (NBR 5101, 6.10);
    2. taxa  - o DECRESCIMO nunca excede a taxa maxima por minuto da classe;
               a elevacao do nivel e livre.

A recomendacao da 6.10 de nao dimerizar sob nevoeiro, neblina ou chuva nao e
verificada: a plataforma de monitoramento nao produz dado meteorologico, e o
trabalho nao integra uma terceira fonte (decisao do autor, DIVERGENCIAS 49).

Este modulo e puro: nao le banco, nao faz E/S, nao conhece MQTT. Os valores
normativos chegam prontos em `Criterio`, montado a partir da tabela
`classe_iluminacao` (RF09) - nenhum limite e escrito aqui.

Toda a aritmetica usa Decimal com 3 casas, a mesma precisao de NUMERIC(4,3)
no banco, para que o valor verificado seja identicamente o valor gravado.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from typing import Final

__all__ = ["Criterio", "Resultado", "verificar", "PASSO", "PLENO", "MINIMO"]

PASSO: Final[Decimal] = Decimal("0.001")  # resolucao de NUMERIC(4,3)
PLENO: Final[Decimal] = Decimal("1.000")
MINIMO: Final[Decimal] = Decimal("0.000")

SEGUNDOS_POR_MINUTO: Final[Decimal] = Decimal(60)

# Rotulos gravados em decisao.restricao_aplicada (CHECK do schema).
NENHUMA: Final[str] = "nenhuma"
PISO: Final[str] = "piso"
TAXA: Final[str] = "taxa"


class ViolacaoNormativa(AssertionError):
    """Levantada se o proprio resultado violar um limite - nunca deve ocorrer."""


@dataclass(frozen=True)
class Criterio:
    """Limites lidos da tabela `classe_iluminacao` para a classe do ponto."""

    # Fracao do fluxo pleno correspondente a classe minima de dimerizacao.
    # Ex.: P3 (10 lux) com piso P5 (5 lux) -> Decimal("0.500").
    piso: Decimal
    # Fracao do fluxo pleno por minuto admitida como decrescimo.
    taxa_max_decrescimo_min: Decimal

    def __post_init__(self) -> None:
        if not (MINIMO <= self.piso <= PLENO):
            raise ValueError(f"piso fora de [0,1]: {self.piso}")
        if not (Decimal(0) < self.taxa_max_decrescimo_min <= PLENO):
            raise ValueError(f"taxa invalida: {self.taxa_max_decrescimo_min}")


@dataclass(frozen=True)
class Resultado:
    nivel_emitido: Decimal
    restricao_aplicada: str
    # Limites efetivos desta decisao, uteis para o painel e para a auditoria.
    piso_efetivo: Decimal
    limite_taxa: Decimal | None


def _q(valor: Decimal, modo: str) -> Decimal:
    return Decimal(valor).quantize(PASSO, rounding=modo)


def verificar(
    nivel_pretendido: Decimal,
    criterio: Criterio,
    *,
    nivel_anterior: Decimal | None = None,
    segundos_desde_anterior: Decimal | float | int | None = None,
) -> Resultado:
    """Corrige `nivel_pretendido` para o maior nivel admissivel.

    `nivel_anterior` e `segundos_desde_anterior` sao None na primeira decisao
    do ponto (nao ha de onde medir taxa); nesse caso so o piso atua.
    """
    # Piso e arredondado para CIMA: a 3 casas, nunca fica abaixo do normativo.
    piso = _q(criterio.piso, ROUND_CEILING)
    pretendido = _q(Decimal(nivel_pretendido), ROUND_HALF_UP)

    if not (MINIMO <= pretendido <= PLENO):
        raise ValueError(f"nivel pretendido fora de [0,1]: {nivel_pretendido}")

    # 2. Taxa: limite inferior imposto pela decisao anterior.
    limite_taxa: Decimal | None = None
    if nivel_anterior is not None and segundos_desde_anterior is not None:
        anterior = _q(Decimal(nivel_anterior), ROUND_HALF_UP)
        segundos = Decimal(str(segundos_desde_anterior))
        if segundos < 0:
            raise ValueError(f"intervalo negativo: {segundos}")
        # Queda admitida no intervalo, arredondada para BAIXO: a 3 casas o
        # limite resultante fica igual ou acima do exato, nunca abaixo.
        queda = _q(
            criterio.taxa_max_decrescimo_min * segundos / SEGUNDOS_POR_MINUTO,
            ROUND_FLOOR,
        )
        limite_taxa = max(MINIMO, anterior - queda)

    # 1. Piso e 2. taxa sao ambos limites INFERIORES: vence o maior.
    emitido = pretendido
    restricao = NENHUMA
    if limite_taxa is not None and limite_taxa > emitido:
        emitido, restricao = limite_taxa, TAXA
    if piso > emitido:
        emitido, restricao = piso, PISO

    resultado = Resultado(
        nivel_emitido=emitido,
        restricao_aplicada=restricao,
        piso_efetivo=piso,
        limite_taxa=limite_taxa,
    )
    _conferir(resultado, pretendido)
    return resultado


def _conferir(r: Resultado, pretendido: Decimal) -> None:
    """Reconfere o proprio resultado: o invariante nao depende de revisao."""
    if r.nivel_emitido < r.piso_efetivo:
        raise ViolacaoNormativa(f"piso violado: {r.nivel_emitido} < {r.piso_efetivo}")
    if r.limite_taxa is not None and r.nivel_emitido < r.limite_taxa:
        raise ViolacaoNormativa(f"taxa violada: {r.nivel_emitido} < {r.limite_taxa}")
    if not (MINIMO <= r.nivel_emitido <= PLENO):
        raise ViolacaoNormativa(f"nivel fora de [0,1]: {r.nivel_emitido}")
    if (r.restricao_aplicada == NENHUMA) != (r.nivel_emitido == pretendido):
        raise ViolacaoNormativa(
            f"restricao {r.restricao_aplicada!r} incoerente com "
            f"{pretendido} -> {r.nivel_emitido}"
        )
    # A camada so corrige para CIMA: ela protege, nunca escurece.
    if r.nivel_emitido < pretendido:
        raise ViolacaoNormativa(f"correcao para baixo: {pretendido} -> {r.nivel_emitido}")
