"""Estimativa de consumo de energia (TCC 3.11, RF12).

NAO e medicao eletrica: e integral da trajetoria de nivel que o sistema ja
registra, sob a hipotese de proporcionalidade entre nivel comandado e
potencia media (declarada como limite superior otimista em 3.11).

Duas fontes, como o texto pede:

  - bancada: potencia plena do segmento x ciclo de trabalho medido x tempo,
    a partir da telemetria (`energia_bancada`);
  - luminaria de referencia do Quadro 9: a partir do REGISTRO DE DECISOES,
    integrando a trajetoria linear por partes que a camada de verificacao
    impoe - elevacao imediata, atenuacao rampeada a taxa maxima
    (`energia_decisoes`).

Linhas de base de comparacao (3.11): fluxo pleno constante e atenuacao por
horario fixo (a programacao agendada prevista no Caderno de Encargos).

Este modulo e puro: nao le banco, nao faz rede.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

__all__ = [
    "Passo", "energia_passo", "energia_decisoes", "energia_bancada",
    "energia_pleno_constante", "trajetoria_horario_fixo", "TAXA_PADRAO",
]

TAXA_PADRAO = 0.1  # fracao do fluxo pleno por minuto (NBR 5101, 6.10.2)
MIN_POR_H = 60.0


@dataclass(frozen=True)
class Passo:
    """Um trecho da trajetoria: sai de `anterior`, vai a `nivel`, dura `minutos`."""

    anterior: float
    nivel: float
    minutos: float


def energia_passo(p: Passo, potencia_w: float, taxa: float = TAXA_PADRAO) -> float:
    """Energia (Wh) de um passo, integrando a trajetoria imposta em 3.7.

    Elevacao: imediata, o intervalo inteiro no nivel novo.
    Atenuacao: rampa de d = (a - b) / taxa minutos e o restante no nivel novo.
    Se o passo acaba antes do fim da rampa, integra so o trecho percorrido.
    """
    a, b, dt = p.anterior, p.nivel, p.minutos
    if dt <= 0 or potencia_w <= 0:
        return 0.0
    if b >= a:  # elevacao (ou nivel mantido)
        return potencia_w * b * dt / MIN_POR_H

    duracao_rampa = (a - b) / taxa
    if dt < duracao_rampa:  # a proxima decisao chegou antes do fim da rampa
        final = a - taxa * dt
        return potencia_w * (a + final) / 2 * dt / MIN_POR_H
    return potencia_w * ((a + b) / 2 * duracao_rampa + b * (dt - duracao_rampa)) / MIN_POR_H


def energia_decisoes(
    decisoes: list[tuple[datetime, float, float]],
    potencia_w: float,
    fim: datetime | None = None,
    taxa: float = TAXA_PADRAO,
) -> float:
    """Energia (Wh) de uma sequencia (instante, nivel_anterior, nivel_emitido).

    O intervalo de cada decisao vai ate a decisao seguinte; o da ultima vai
    ate `fim`, se informado.
    """
    if not decisoes:
        return 0.0
    ordenadas = sorted(decisoes, key=lambda d: d[0])
    total = 0.0
    for i, (quando, anterior, nivel) in enumerate(ordenadas):
        seguinte = ordenadas[i + 1][0] if i + 1 < len(ordenadas) else fim
        if seguinte is None:
            break
        minutos = (seguinte - quando).total_seconds() / 60
        # Sem nivel anterior (primeira decisao do ponto), nao ha rampa a integrar.
        total += energia_passo(Passo(anterior if anterior is not None else nivel, nivel, minutos),
                               potencia_w, taxa)
    return total


def energia_bancada(
    telemetria: list[tuple[datetime, float]],
    potencia_plena_w: float,
    fim: datetime | None = None,
) -> float:
    """Energia (Wh) do segmento de fita: potencia plena x duty x tempo (3.11).

    `telemetria` e a sequencia (instante, ciclo de trabalho aplicado). Cada
    duty vale ate a leitura seguinte - e a trajetoria efetivamente aplicada,
    nao a decidida.
    """
    if not telemetria:
        return 0.0
    ordenada = sorted(telemetria, key=lambda t: t[0])
    total = 0.0
    for i, (quando, duty) in enumerate(ordenada):
        seguinte = ordenada[i + 1][0] if i + 1 < len(ordenada) else fim
        if seguinte is None:
            break
        total += potencia_plena_w * duty * (seguinte - quando).total_seconds() / 3600
    return total


def energia_pleno_constante(potencia_w: float, minutos: float) -> float:
    """Linha de base 1: o regime praticamente invariante de hoje (2.3)."""
    return potencia_w * minutos / MIN_POR_H


def trajetoria_horario_fixo(
    inicio: datetime,
    fim: datetime,
    piso: float,
    *,
    hora_inicio_atenuacao: time,
    hora_fim_atenuacao: time,
    passo_s: float = 5.0,
    taxa: float = TAXA_PADRAO,
) -> list[tuple[datetime, float, float]]:
    """Linha de base 2: programacao agendada, sem dado urbano.

    Devolve a mesma estrutura de `energia_decisoes` - (instante, anterior,
    nivel) - para que os dois regimes sejam integrados pela MESMA conta. A
    atenuacao tambem obedece a taxa normativa: a programacao agendada nao
    esta dispensada do limite de 0,1/min.
    """
    passos: list[tuple[datetime, float, float]] = []
    atual = 1.0
    quando = inicio
    delta = timedelta(seconds=passo_s)
    while quando < fim:
        h = quando.time()
        if hora_inicio_atenuacao <= hora_fim_atenuacao:
            atenuando = hora_inicio_atenuacao <= h < hora_fim_atenuacao
        else:  # janela que cruza a meia-noite
            atenuando = h >= hora_inicio_atenuacao or h < hora_fim_atenuacao
        alvo = piso if atenuando else 1.0
        # Descida limitada pela taxa; subida livre, como na verificacao.
        if alvo < atual:
            novo = max(alvo, atual - taxa * passo_s / 60)
        else:
            novo = alvo
        passos.append((quando, atual, novo))
        atual = novo
        quando += delta
    return passos
