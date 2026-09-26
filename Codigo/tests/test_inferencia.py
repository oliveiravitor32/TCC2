"""Inferencia Mamdani (TCC 3.7): comportamento da base vigente
(v2-sem-meteorologia) e integracao com a camada de verificacao. A inferencia
pode produzir qualquer nivel em [0,1]; o que nunca pode acontecer e o nivel
EMITIDO violar a norma.

Com os tercis reais (0,1038 e 0,4053), os valores tipicos usados aqui sao:
movimentacao baixa = 0,02; media = 0,25; alta = 0,70.
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
BAIXA, MEDIA, ALTA = 0.02, 0.25, 0.70


def nivel(obs, prev, *, oc=False, momento=MADRUGADA) -> Decimal:
    return inferir(BASE, Entrada(obs, prev, oc, momento)).nivel_pretendido


# --------------------------------------------------------------------------
# Base de regras (RNF05)
# --------------------------------------------------------------------------
def test_base_vigente_tem_oito_regras_todas_com_origem():
    assert BASE.rotulo == "v2-sem-meteorologia"
    assert len(BASE.regras) == 8
    assert all(r.origem for r in BASE.regras)


def test_base_nao_usa_meteorologia():
    # DIVERGENCIAS 49: a plataforma de monitoramento nao produz esse dado.
    assert all("meteorologia" not in r.se for r in BASE.regras)


def test_base_legivel_em_linguagem_natural():
    linhas = BASE.texto().splitlines()
    assert len(linhas) == 8
    assert linhas[0] == "R1: SE ocorrencia = sim ENTAO nivel = pleno"


def test_hash_independe_do_fim_de_linha():
    assert _hash(b"a = 1\r\nb = 2\r\n") == _hash(b"a = 1\nb = 2\n")


def test_particoes_cruzam_em_meio_no_tercil():
    # No tercil inferior (0,1038), o valor pertence 0,5 a "baixa" e a "media".
    r = inferir(BASE, Entrada(0.1038, 0.1038, False, MADRUGADA))
    assert r.ativacoes["R4"] == pytest.approx(0.5, abs=0.01)  # observada media
    assert r.ativacoes["R5"] == pytest.approx(0.5, abs=0.01)  # baixa e baixa


# --------------------------------------------------------------------------
# Comportamento esperado
# --------------------------------------------------------------------------
def test_movimentacao_baixa_na_madrugada_reduz():
    assert nivel(BAIXA, BAIXA) < Decimal("0.5")


def test_movimentacao_alta_eleva():
    assert nivel(ALTA, ALTA) > Decimal("0.9")


def test_movimentacao_media_fica_no_intermediario():
    assert Decimal("0.5") <= nivel(MEDIA, MEDIA) <= Decimal("0.6")


def test_ocorrencia_nao_e_diluida_pela_regra_de_reducao():
    # Com movimento baixo, uma ocorrencia nao pode cair para o piso por media
    # com as regras de atenuacao (itens 18 e 27).
    assert nivel(BAIXA, BAIXA, oc=True) > Decimal("0.9")


@pytest.mark.parametrize("hora", [19, 21, 22, 23])
def test_ocorrencia_no_inicio_da_noite_nao_e_diluida(hora):
    momento = datetime(2026, 9, 21, hora, 49)
    assert nivel(BAIXA, BAIXA, oc=True, momento=momento) > Decimal("0.9")


def test_previsao_alta_antecipa_elevacao():
    assert nivel(BAIXA, ALTA) > Decimal("0.9")


def test_previsao_media_segura_a_reducao():
    assert nivel(BAIXA, MEDIA) > nivel(BAIXA, BAIXA)


def test_inicio_da_noite_nao_reduz_tanto_quanto_a_madrugada():
    assert nivel(BAIXA, BAIXA, momento=INICIO_NOITE) > nivel(BAIXA, BAIXA)


def test_inicio_da_noite_nao_dilui_movimento_alto():
    assert nivel(ALTA, ALTA, momento=INICIO_NOITE) > Decimal("0.9")


def test_modo_reativo_usa_a_observada_como_prevista():
    for obs in (BAIXA, 0.2, MEDIA, ALTA):
        assert nivel(obs, None) == nivel(obs, obs)


def test_rastreabilidade_devolve_grau_de_cada_regra():
    r = inferir(BASE, Entrada(BAIXA, BAIXA, True, MADRUGADA))
    assert set(r.ativacoes) == {f"R{i}" for i in range(1, 9)}
    assert r.ativacoes["R1"] == 1.0
    assert r.ativacoes["R5"] == 0.0  # atenuacao bloqueada pela ocorrencia


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
                r = inferir(BASE, Entrada(i / 100, j / 100, False, datetime(2026, 9, 21, h)))
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
            momento=momento,
        )
        pretendido = inferir(BASE, e).nivel_pretendido
        r = verificar(
            pretendido,
            P3,
            nivel_anterior=anterior,
            segundos_desde_anterior=None if anterior is None else 5,
        )
        assert r.nivel_emitido >= P3.piso
        if anterior is not None:
            assert anterior - r.nivel_emitido <= P3.taxa_max_decrescimo_min * 5 / 60
        anterior = r.nivel_emitido
        momento += timedelta(seconds=5)
