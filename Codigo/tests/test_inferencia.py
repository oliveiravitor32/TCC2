"""Inferencia Mamdani (TCC 3.7): comportamento da base v0 e integracao com a
camada de verificacao. A inferencia pode produzir qualquer nivel em [0,1];
o que nunca pode acontecer e o nivel EMITIDO violar a norma.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from decisao.inferencia import Entrada, _hash, carregar, horas_desde_18h, inferir
from decisao.verificacao import Criterio, verificar

BASE = carregar()
P3 = Criterio(piso=Decimal("0.500"), taxa_max_decrescimo_min=Decimal("0.100"))

MADRUGADA = datetime(2026, 9, 21, 1, 0)
INICIO_NOITE = datetime(2026, 9, 21, 19, 0)


def nivel(obs, prev, *, oc=False, met=False, momento=MADRUGADA) -> Decimal:
    return inferir(BASE, Entrada(obs, prev, oc, met, momento)).nivel_pretendido


# --------------------------------------------------------------------------
# Base de regras (RNF05)
# --------------------------------------------------------------------------
def test_base_tem_nove_regras_todas_com_origem():
    assert BASE.rotulo == "v0-provisoria"
    assert len(BASE.regras) == 9
    assert all(r.origem for r in BASE.regras)


def test_base_legivel_em_linguagem_natural():
    linhas = BASE.texto().splitlines()
    assert len(linhas) == 9
    assert linhas[0] == "R1: SE ocorrencia = sim ENTAO nivel = pleno"


def test_hash_independe_do_fim_de_linha():
    assert _hash(b"a = 1\r\nb = 2\r\n") == _hash(b"a = 1\nb = 2\n")


def test_particoes_cruzam_em_meio_na_fronteira():
    # Na fronteira do tercil, o valor pertence 0,5 a cada conjunto vizinho.
    r = inferir(BASE, Entrada(0.3333, 0.3333, False, False, MADRUGADA))
    assert r.ativacoes["R5"] == pytest.approx(0.5, abs=0.01)
    assert r.ativacoes["R6"] == pytest.approx(0.5, abs=0.01)


# --------------------------------------------------------------------------
# Comportamento esperado
# --------------------------------------------------------------------------
def test_movimentacao_baixa_na_madrugada_reduz():
    assert nivel(0.1, 0.1) < Decimal("0.5")


def test_movimentacao_alta_eleva():
    assert nivel(0.9, 0.9) > Decimal("0.9")


def test_movimentacao_media_fica_no_intermediario():
    assert Decimal("0.5") <= nivel(0.5, 0.5) <= Decimal("0.6")


@pytest.mark.parametrize("oc,met", [(True, False), (False, True)])
def test_risco_nao_e_diluido_pela_regra_de_reducao(oc, met):
    # Correcao da v0: com movimento baixo, ocorrencia ou chuva nao podem cair
    # para o piso por media com as regras de atenuacao.
    assert nivel(0.1, 0.1, oc=oc, met=met) > Decimal("0.9")


@pytest.mark.parametrize("oc,met", [(True, False), (False, True)])
@pytest.mark.parametrize("hora", [19, 21, 22, 23])
def test_risco_no_inicio_da_noite_nao_e_diluido_pela_r9(oc, met, hora):
    # Achado do teste ponta a ponta: as 22h49 com chuva a R9 puxava para 0,837.
    momento = datetime(2026, 9, 21, hora, 49)
    assert nivel(0.1, 0.1, oc=oc, met=met, momento=momento) > Decimal("0.9")


def test_previsao_alta_antecipa_elevacao():
    assert nivel(0.1, 0.9) > Decimal("0.9")


def test_previsao_media_segura_a_reducao():
    assert nivel(0.1, 0.5) > nivel(0.1, 0.1)


def test_inicio_da_noite_nao_reduz_tanto_quanto_a_madrugada():
    assert nivel(0.1, 0.1, momento=INICIO_NOITE) > nivel(0.1, 0.1)


def test_inicio_da_noite_nao_dilui_movimento_alto():
    assert nivel(0.9, 0.9, momento=INICIO_NOITE) > Decimal("0.9")


def test_modo_reativo_usa_a_observada_como_prevista():
    for obs in (0.1, 0.4, 0.6, 0.9):
        assert nivel(obs, None) == nivel(obs, obs)


def test_rastreabilidade_devolve_grau_de_cada_regra():
    r = inferir(BASE, Entrada(0.1, 0.1, True, False, MADRUGADA))
    assert set(r.ativacoes) == {f"R{i}" for i in range(1, 10)}
    assert r.ativacoes["R1"] == 1.0
    assert r.ativacoes["R6"] == 0.0


def test_entrada_fora_do_universo_e_recusada():
    with pytest.raises(ValueError):
        nivel(1.2, 0.5)


@pytest.mark.parametrize(
    "hora,esperado", [(18, 0.0), (21, 3.0), (0, 6.0), (6, 12.0), (11, 12.0), (13, 0.0), (15, 0.0)]
)
def test_faixa_horaria(hora, esperado):
    assert horas_desde_18h(datetime(2026, 9, 21, hora, 0)) == esperado


def test_alguma_regra_sempre_ativa():
    # Varredura do espaco de entrada: a base cobre todo o universo.
    for i in range(0, 101, 5):
        for j in range(0, 101, 5):
            for h in range(24):
                r = inferir(
                    BASE, Entrada(i / 100, j / 100, False, False, datetime(2026, 9, 21, h))
                )
                assert not r.sem_regra_ativa, (i, j, h)


# --------------------------------------------------------------------------
# Integracao com a verificacao: zero violacoes na cadeia inferencia -> emitido
# --------------------------------------------------------------------------
def test_cadeia_inferencia_verificacao_nunca_viola():
    rng = random.Random(3_7)
    anterior: Decimal | None = None
    momento = datetime(2026, 9, 21, 18, 0)
    for _ in range(5_000):
        e = Entrada(
            observada=rng.random(),
            prevista=rng.choice([None, rng.random()]),
            ocorrencia=rng.random() < 0.1,
            meteorologia_adversa=rng.random() < 0.1,
            momento=momento,
        )
        pretendido = inferir(BASE, e).nivel_pretendido
        r = verificar(
            pretendido,
            P3,
            nivel_anterior=anterior,
            segundos_desde_anterior=None if anterior is None else 5,
            meteorologia_adversa=e.meteorologia_adversa,
        )
        assert r.nivel_emitido >= P3.piso
        if anterior is not None:
            assert anterior - r.nivel_emitido <= P3.taxa_max_decrescimo_min * 5 / 60
        anterior = r.nivel_emitido
        momento += timedelta(seconds=5)
