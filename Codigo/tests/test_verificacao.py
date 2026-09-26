"""RNF01 / Etapa 4 do TCC: o invariante de seguranca nao admite violacao.

Alem dos casos nomeados, a suite sorteia 100 mil casos - inclusive
adversariais, construidos para induzir nivel inadmissivel - e exige zero
violacoes de piso e de taxa.
"""

from __future__ import annotations

import random
from decimal import Decimal

import pytest

from decisao.verificacao import (
    NENHUMA,
    PASSO,
    PISO,
    PLENO,
    TAXA,
    Criterio,
    verificar,
)

# Classe P3 com piso P5 e taxa do Quadro 8; espelha o que o seed grava.
P3 = Criterio(piso=Decimal("0.500"), taxa_max_decrescimo_min=Decimal("0.100"))

CASOS_TOTAL = 100_000


# --------------------------------------------------------------------------
# Casos nomeados
# --------------------------------------------------------------------------
def test_nivel_admissivel_passa_intacto():
    r = verificar(Decimal("0.800"), P3)
    assert r.nivel_emitido == Decimal("0.800")
    assert r.restricao_aplicada == NENHUMA


def test_piso_corrige_nivel_abaixo_de_p5():
    r = verificar(Decimal("0.100"), P3)
    assert r.nivel_emitido == Decimal("0.500")
    assert r.restricao_aplicada == PISO


def test_piso_atua_mesmo_em_zero():
    assert verificar(Decimal("0"), P3).nivel_emitido == Decimal("0.500")


def test_taxa_limita_decrescimo_em_um_ciclo_de_5s():
    # 0,100 por minuto durante 5 s => queda admitida de 0,008 (arredondada
    # para baixo a partir de 0,008333).
    r = verificar(
        Decimal("0.500"), P3, nivel_anterior=Decimal("1.000"), segundos_desde_anterior=5
    )
    assert r.nivel_emitido == Decimal("0.992")
    assert r.restricao_aplicada == TAXA


def test_elevacao_e_livre():
    r = verificar(
        Decimal("1.000"), P3, nivel_anterior=Decimal("0.500"), segundos_desde_anterior=1
    )
    assert r.nivel_emitido == PLENO
    assert r.restricao_aplicada == NENHUMA


def test_piso_vence_taxa_quando_ambos_atuam():
    # Taxa permitiria 0,492; o piso nao.
    r = verificar(
        Decimal("0.000"), P3, nivel_anterior=Decimal("0.500"), segundos_desde_anterior=5
    )
    assert r.nivel_emitido == Decimal("0.500")
    assert r.restricao_aplicada == PISO


def test_primeira_decisao_sem_anterior_nao_aplica_taxa():
    r = verificar(Decimal("0.600"), P3)
    assert r.limite_taxa is None
    assert r.restricao_aplicada == NENHUMA


def test_rampa_completa_de_pleno_ao_piso_nunca_viola():
    """Rampa real: passo de 5 s, de 1,0 ate o piso, pedindo sempre 0."""
    anterior = PLENO
    passos = 0
    while anterior > Decimal("0.500"):
        r = verificar(
            Decimal("0"), P3, nivel_anterior=anterior, segundos_desde_anterior=5
        )
        assert r.nivel_emitido >= Decimal("0.500")
        assert r.nivel_emitido <= anterior
        anterior = r.nivel_emitido
        passos += 1
        assert passos < 200, "rampa nao converge"
    assert anterior == Decimal("0.500")
    # 0,5 do pleno a 0,1/min => 5 min = 300 s = 60 passos, mais o arredondamento.
    assert 60 <= passos <= 66


@pytest.mark.parametrize("nivel", ["-0.001", "1.001", "2"])
def test_nivel_fora_da_faixa_e_rejeitado(nivel):
    with pytest.raises(ValueError):
        verificar(Decimal(nivel), P3)


def test_intervalo_negativo_e_rejeitado():
    with pytest.raises(ValueError):
        verificar(
            Decimal("0.5"),
            P3,
            nivel_anterior=Decimal("1.0"),
            segundos_desde_anterior=-1,
        )


# --------------------------------------------------------------------------
# Suite aleatoria (RNF01): 100 mil casos, zero violacoes
# --------------------------------------------------------------------------
def _sorteia_caso(rng: random.Random) -> dict:
    piso = Decimal(rng.randrange(0, 901)) / 1000  # 0,000 .. 0,900
    taxa = Decimal(rng.randrange(1, 1001)) / 1000
    criterio = Criterio(piso=piso, taxa_max_decrescimo_min=taxa)

    if rng.random() < 0.35:
        # Adversarial: pede o minimo, ou logo abaixo do piso, apos o pleno.
        pretendido = rng.choice(
            [Decimal("0"), max(Decimal("0"), piso - PASSO), Decimal("0.001")]
        )
    else:
        pretendido = Decimal(rng.randrange(0, 1001)) / 1000

    tem_anterior = rng.random() < 0.9
    anterior = Decimal(rng.randrange(0, 1001)) / 1000 if tem_anterior else None
    if tem_anterior:
        # Inclui intervalos degenerados: 0 s (dois comandos no mesmo instante)
        # e intervalos longos, alem do passo nominal de 5 s.
        segundos = rng.choice([0, 0.001, 1, 5, 5, 5, 17, 60, 3600])
    else:
        segundos = None

    return {
        "nivel_pretendido": pretendido,
        "criterio": criterio,
        "nivel_anterior": anterior,
        "segundos_desde_anterior": segundos,
    }


def test_cem_mil_casos_aleatorios_sem_violacao():
    rng = random.Random(20260920)  # semente fixa: a suite e reproduzivel
    violacoes: list[str] = []

    for i in range(CASOS_TOTAL):
        caso = _sorteia_caso(rng)
        criterio = caso["criterio"]
        r = verificar(
            caso["nivel_pretendido"],
            criterio,
            nivel_anterior=caso["nivel_anterior"],
            segundos_desde_anterior=caso["segundos_desde_anterior"],
        )

        # 1. piso
        if r.nivel_emitido < criterio.piso:
            violacoes.append(f"[{i}] piso: {r.nivel_emitido} < {criterio.piso} | {caso}")
        # 2. taxa, conferida contra o limite exato (sem arredondamento)
        if caso["nivel_anterior"] is not None and caso["segundos_desde_anterior"] is not None:
            queda_exata = (
                criterio.taxa_max_decrescimo_min
                * Decimal(str(caso["segundos_desde_anterior"]))
                / Decimal(60)
            )
            queda_real = Decimal(caso["nivel_anterior"]) - r.nivel_emitido
            if queda_real > queda_exata:
                violacoes.append(
                    f"[{i}] taxa: caiu {queda_real} > {queda_exata} | {caso}"
                )
        # faixa e resolucao
        if not (Decimal(0) <= r.nivel_emitido <= PLENO):
            violacoes.append(f"[{i}] faixa: {r.nivel_emitido}")
        if r.nivel_emitido != r.nivel_emitido.quantize(PASSO):
            violacoes.append(f"[{i}] resolucao: {r.nivel_emitido}")

    assert not violacoes, f"{len(violacoes)} violacoes; primeiras:\n" + "\n".join(
        violacoes[:5]
    )
