"""Inferencia Mamdani (TCC 3.7): comportamento da base vigente (v3-presenca)
e integracao com a camada de verificacao. A inferencia pode produzir qualquer
nivel em [0,1]; o que nunca pode acontecer e o nivel EMITIDO violar a norma.

Previsao com os tercis reais (0,1038 e 0,4053): baixa = 0,02; media = 0,25;
alta = 0,70.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from decisao.inferencia import Entrada, _hash, carregar, em_degraus, horas_desde_18h, inferir
from decisao.verificacao import Criterio, verificar

BASE = carregar()
P3 = Criterio(piso=Decimal("0.500"), taxa_max_decrescimo_min=Decimal("0.100"))

MADRUGADA = datetime(2026, 9, 21, 1, 0)
INICIO_NOITE = datetime(2026, 9, 21, 19, 0)
BAIXA, MEDIA, ALTA = 0.02, 0.25, 0.70


def nivel(prev, *, pessoa=False, oc=False, momento=MADRUGADA, recente=None, base=BASE) -> Decimal:
    return inferir(base, Entrada(pessoa, prev, oc, momento, recente)).nivel_pretendido


# --------------------------------------------------------------------------
# Base de regras (RNF05)
# --------------------------------------------------------------------------
def test_base_vigente_tem_seis_regras_todas_com_origem():
    assert BASE.rotulo == "v3-presenca"
    assert len(BASE.regras) == 6
    assert all(r.origem for r in BASE.regras)


def test_base_nao_usa_meteorologia_nem_volume_observado():
    assert all("meteorologia" not in r.se and "observada" not in r.se for r in BASE.regras)


def test_base_legivel_em_linguagem_natural():
    linhas = BASE.texto().splitlines()
    assert len(linhas) == 6
    assert linhas[1] == "R2: SE presenca = sim ENTAO nivel = pleno"


def test_hash_independe_do_fim_de_linha():
    assert _hash(b"a = 1\r\nb = 2\r\n") == _hash(b"a = 1\nb = 2\n")


def test_nenhuma_regra_atenua_com_pedestre_ou_ocorrencia():
    # Garantia estrutural da v3: toda regra que leva a "reduzido" ou
    # "intermediario" exige presenca = nao e ocorrencia = nao.
    for r in BASE.regras:
        if r.entao != "pleno":
            assert r.se.get("presenca") == "nao" and r.se.get("ocorrencia") == "nao", r.id


# --------------------------------------------------------------------------
# Presenca e ocorrencia
# --------------------------------------------------------------------------
@pytest.mark.parametrize("hora", [18, 19, 21, 23, 0, 2, 4, 5])
def test_uma_pessoa_na_via_leva_ao_pleno_a_qualquer_hora(hora):
    momento = datetime(2026, 9, 21, hora, 30)
    assert nivel(BAIXA, pessoa=True, momento=momento) > Decimal("0.9")


@pytest.mark.parametrize("hora", [19, 1, 5])
def test_ocorrencia_leva_ao_pleno(hora):
    assert nivel(BAIXA, oc=True, momento=datetime(2026, 9, 21, hora, 0)) > Decimal("0.9")


def test_pedestre_nao_e_diluido_no_inicio_da_noite():
    assert nivel(BAIXA, pessoa=True, momento=INICIO_NOITE) > Decimal("0.9")


# --------------------------------------------------------------------------
# Via vazia: a previsao decide ate onde descer
# --------------------------------------------------------------------------
def test_via_vazia_de_madrugada_com_previsao_baixa_reduz():
    assert nivel(BAIXA) < Decimal("0.5")


def test_via_vazia_com_previsao_media_fica_no_intermediario():
    assert Decimal("0.5") <= nivel(MEDIA) <= Decimal("0.6")


def test_via_vazia_com_previsao_alta_antecipa_o_pleno():
    assert nivel(ALTA) > Decimal("0.9")


def test_inicio_da_noite_segura_a_descida():
    assert nivel(BAIXA, momento=INICIO_NOITE) > nivel(BAIXA)


def test_particoes_cruzam_em_meio_no_tercil():
    r = inferir(BASE, Entrada(False, 0.1038, False, MADRUGADA))
    assert r.ativacoes["R4"] == pytest.approx(0.5, abs=0.01)  # prevista baixa
    assert r.ativacoes["R5"] == pytest.approx(0.5, abs=0.01)  # prevista media


# --------------------------------------------------------------------------
# Sem previsao
# --------------------------------------------------------------------------
def test_modo_reativo_usa_o_nivel_recente_no_lugar_da_previsao():
    for x in (BAIXA, 0.2, MEDIA, ALTA):
        assert nivel(None, recente=x) == nivel(x)


def test_sem_previsao_e_sem_historico_nao_atenua_de_madrugada():
    r = inferir(BASE, Entrada(False, None, False, MADRUGADA))
    assert r.sem_regra_ativa and r.nivel_pretendido == Decimal("1.000")


def test_rastreabilidade_devolve_grau_de_cada_regra():
    r = inferir(BASE, Entrada(True, BAIXA, False, MADRUGADA))
    assert set(r.ativacoes) == {f"R{i}" for i in range(1, 7)}
    assert r.ativacoes["R2"] == 1.0
    assert r.ativacoes["R4"] == 0.0  # atenuacao bloqueada pela presenca


def test_entrada_fora_do_universo_e_recusada():
    with pytest.raises(ValueError):
        nivel(1.2)


@pytest.mark.parametrize(
    "hora,esperado", [(18, 0.0), (21, 3.0), (0, 6.0), (6, 12.0), (11, 12.0), (13, 0.0), (15, 0.0)]
)
def test_faixa_horaria(hora, esperado):
    assert horas_desde_18h(datetime(2026, 9, 21, hora, 0)) == esperado


def test_alguma_regra_sempre_ativa_com_previsao():
    for j in range(0, 101, 5):
        for h in range(24):
            for pessoa in (False, True):
                r = inferir(BASE, Entrada(pessoa, j / 100, False, datetime(2026, 9, 21, h)))
                assert not r.sem_regra_ativa, (j, h, pessoa)


# --------------------------------------------------------------------------
# Integracao com a verificacao: zero violacoes na cadeia inferencia -> emitido
# --------------------------------------------------------------------------
def test_cadeia_inferencia_verificacao_nunca_viola():
    rng = random.Random(3_7)
    anterior: Decimal | None = None
    momento = datetime(2026, 9, 21, 18, 0)
    for _ in range(5_000):
        e = Entrada(
            presenca=rng.random() < 0.3,
            prevista=rng.choice([None, rng.random()]),
            ocorrencia=rng.random() < 0.1,
            momento=momento,
            recente=rng.choice([None, rng.random()]),
        )
        pretendido = inferir(BASE, e).nivel_pretendido
        r = verificar(
            pretendido, P3, nivel_anterior=anterior,
            segundos_desde_anterior=None if anterior is None else 5,
        )
        assert r.nivel_emitido >= P3.piso
        if anterior is not None:
            assert anterior - r.nivel_emitido <= P3.taxa_max_decrescimo_min * 5 / 60
        anterior = r.nivel_emitido
        momento += timedelta(seconds=5)


# --------------------------------------------------------------------------
# Variante em degraus (item 51): mesma base, sem logica nebulosa
# --------------------------------------------------------------------------
DEGRAUS = em_degraus(BASE)


def test_degraus_tem_rotulo_proprio_e_mesmo_hash():
    assert DEGRAUS.rotulo == "v3-presenca-degraus"
    assert DEGRAUS.hash_regras == BASE.hash_regras


def test_degraus_e_uma_tabela_com_poucos_niveis():
    niveis = {
        inferir(DEGRAUS, Entrada(p, j / 100, oc, datetime(2026, 9, 21, h))).nivel_pretendido
        for j in range(0, 101, 2) for h in range(24) for p in (False, True) for oc in (False, True)
    }
    assert len(niveis) <= 6


def test_degraus_coincide_com_mamdani_longe_das_fronteiras():
    for prev in (BAIXA, MEDIA, ALTA):
        e = Entrada(False, prev, False, MADRUGADA)
        assert inferir(DEGRAUS, e).nivel_pretendido == inferir(BASE, e).nivel_pretendido


def test_degraus_salta_na_fronteira():
    antes = nivel(0.1037, base=DEGRAUS)
    depois = nivel(0.1039, base=DEGRAUS)
    assert depois - antes > Decimal("0.2")
