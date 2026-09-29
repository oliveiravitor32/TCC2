"""Inferencia Mamdani (TCC 3.7): comportamento da base vigente (v4-volume)
e integracao com a camada de verificacao. A inferencia pode produzir qualquer
nivel entre os degraus da classe; o que nunca pode acontecer e o nivel
EMITIDO violar a norma.

Movimentacao com os tercis reais (0,1038 e 0,4053): baixa = 0,02; media =
0,25; alta = 0,70. Niveis da classe P3 como o servico le do banco: P3, P4 e
P5 = 1, 0,75 e 0,5 do pleno.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from decisao.inferencia import (
    Entrada, _hash, carregar, em_degraus, fracao_do_degrau, horas_desde_18h, inferir,
)
from decisao.verificacao import Criterio, verificar

BASE = carregar()
P3 = Criterio(piso=Decimal("0.500"), taxa_max_decrescimo_min=Decimal("0.100"))
NIVEIS_P3 = (Decimal("1"), Decimal("0.75"), Decimal("0.5"))
NIVEIS_P4 = (Decimal("1"), Decimal("5") / Decimal("7.5"), Decimal("3") / Decimal("7.5"))
NIVEIS_FIXA = (Decimal("1"), Decimal("1"), Decimal("1"))

MADRUGADA = datetime(2026, 9, 21, 1, 0)
INICIO_NOITE = datetime(2026, 9, 21, 19, 0)
BAIXA, MEDIA, ALTA = 0.02, 0.25, 0.70


def resultado(obs, prev, *, oc=False, momento=MADRUGADA, base=BASE, niveis=NIVEIS_P3):
    return inferir(base, Entrada(obs, prev, oc, momento), niveis)


def nivel(obs, prev, **kw) -> Decimal:
    return resultado(obs, prev, **kw).nivel_pretendido


# --------------------------------------------------------------------------
# Base de regras (RNF05)
# --------------------------------------------------------------------------
def test_base_vigente_tem_sete_regras_todas_com_origem():
    assert BASE.rotulo == "v4-volume"
    assert len(BASE.regras) == 7
    assert all(r.origem for r in BASE.regras)


def test_base_nao_usa_meteorologia_nem_presenca():
    assert all("meteorologia" not in r.se and "presenca" not in r.se for r in BASE.regras)


def test_saida_em_tres_degraus_de_classe():
    # Tres degraus porque a norma admite descer no maximo duas classes (6.10.2).
    assert BASE.saida_tipo == "degrau_de_classe"
    assert set(BASE.saida) == {"classe_da_via", "uma_classe_abaixo", "classe_minima"}


def test_base_legivel_em_linguagem_natural():
    linhas = BASE.texto().splitlines()
    assert len(linhas) == 7
    assert linhas[1] == "R2: SE observada = alta ENTAO nivel = classe_da_via"


def test_hash_independe_do_fim_de_linha():
    assert _hash(b"a = 1\r\nb = 2\r\n") == _hash(b"a = 1\nb = 2\n")


def test_nenhuma_regra_atenua_com_ocorrencia():
    # Garantia estrutural: toda regra que desce de classe exige ocorrencia = nao.
    for r in BASE.regras:
        if r.entao != "classe_da_via":
            assert r.se.get("ocorrencia") == "nao", r.id


def test_bases_antigas_ainda_carregam_para_o_historico():
    regras = Path(__file__).resolve().parent.parent / "decisao" / "regras"
    for nome in ("v2-sem-meteorologia", "v3-presenca"):
        base = carregar(regras / f"{nome}.toml")
        assert base.rotulo == nome
        with pytest.raises(ValueError):
            inferir(base, Entrada(BAIXA, BAIXA, False, MADRUGADA), NIVEIS_P3)


# --------------------------------------------------------------------------
# Cada degrau e uma classe da norma
# --------------------------------------------------------------------------
def test_volume_alto_fica_na_classe_da_via():
    assert nivel(ALTA, BAIXA) == Decimal("1.000")


def test_volume_medio_desce_uma_classe_p4():
    assert nivel(MEDIA, MEDIA) == Decimal("0.750")


def test_volume_baixo_de_madrugada_vai_a_classe_minima_p5():
    assert nivel(BAIXA, BAIXA) == Decimal("0.500")


def test_uma_pessoa_na_rua_vazia_nao_forca_o_pleno():
    # Uma pessoa numa via de referencia 5 = volume 0,2 (medio): P4, e nao P3.
    assert nivel(0.2, BAIXA) == Decimal("0.750")


@pytest.mark.parametrize("hora", [19, 1, 5])
def test_ocorrencia_leva_a_classe_da_via(hora):
    assert nivel(BAIXA, BAIXA, oc=True, momento=datetime(2026, 9, 21, hora, 0)) == Decimal("1.000")


def test_ocorrencia_nao_e_diluida_com_volume_medio():
    assert nivel(MEDIA, MEDIA, oc=True) == Decimal("1.000")


def test_previsao_alta_antecipa_a_classe_da_via():
    assert nivel(BAIXA, ALTA) == Decimal("1.000")


def test_previsao_media_segura_uma_classe_acima_da_minima():
    # A previsao como segunda opiniao: a contagem diz "vazio", o historico
    # diz "costuma ter movimento" -> nao vai ao minimo.
    assert nivel(BAIXA, MEDIA) == Decimal("0.750")


def test_inicio_da_noite_segura_a_descida():
    assert Decimal("0.5") < nivel(BAIXA, BAIXA, momento=INICIO_NOITE) < Decimal("0.75")


def test_fronteira_do_tercil_da_meio_termo():
    r = resultado(0.1038, 0.1038)
    assert r.degrau == pytest.approx(1.5, abs=0.02)
    assert Decimal("0.6") < r.nivel_pretendido < Decimal("0.65")


# --------------------------------------------------------------------------
# Niveis lidos da classe (RF09)
# --------------------------------------------------------------------------
def test_classe_p4_desce_ate_p6():
    assert nivel(BAIXA, BAIXA, niveis=NIVEIS_P4) == Decimal("0.400")
    assert nivel(MEDIA, MEDIA, niveis=NIVEIS_P4) == Decimal("0.667")


def test_classe_nao_dimerizavel_fica_sempre_no_pleno():
    for obs in (BAIXA, MEDIA, ALTA):
        assert nivel(obs, BAIXA, niveis=NIVEIS_FIXA) == Decimal("1.000")


def test_degrau_vira_fracao_por_interpolacao_arredondada_para_cima():
    assert fracao_do_degrau(0.0, NIVEIS_P3) == Decimal("1.000")
    assert fracao_do_degrau(1.0, NIVEIS_P3) == Decimal("0.750")
    assert fracao_do_degrau(1.5, NIVEIS_P3) == Decimal("0.625")
    assert fracao_do_degrau(2.0, NIVEIS_P3) == Decimal("0.500")
    assert fracao_do_degrau(1.0, NIVEIS_P4) == Decimal("0.667")  # 0,6666... para cima


def test_niveis_incoerentes_sao_recusados():
    with pytest.raises(ValueError):
        nivel(BAIXA, BAIXA, niveis=(Decimal("1"), Decimal("0.5"), Decimal("0.75")))


# --------------------------------------------------------------------------
# Sem previsao / sem dado
# --------------------------------------------------------------------------
def test_modo_reativo_usa_a_observada_no_lugar_da_previsao():
    for x in (BAIXA, 0.2, MEDIA, ALTA):
        assert nivel(x, None) == nivel(x, x)


def test_sem_movimentacao_nao_atenua():
    r = resultado(None, None)
    assert r.sem_regra_ativa and r.nivel_pretendido == Decimal("1")


def test_rastreabilidade_devolve_grau_de_cada_regra():
    r = resultado(BAIXA, BAIXA, oc=True)
    assert set(r.ativacoes) == {f"R{i}" for i in range(1, 8)}
    assert r.ativacoes["R1"] == 1.0
    assert r.ativacoes["R5"] == 0.0  # atenuacao bloqueada pela ocorrencia


def test_entrada_fora_do_universo_e_recusada():
    with pytest.raises(ValueError):
        nivel(1.2, BAIXA)


@pytest.mark.parametrize(
    "hora,esperado", [(18, 0.0), (21, 3.0), (0, 6.0), (6, 12.0), (11, 12.0), (13, 0.0), (15, 0.0)]
)
def test_faixa_horaria(hora, esperado):
    assert horas_desde_18h(datetime(2026, 9, 21, hora, 0)) == esperado


def test_alguma_regra_sempre_ativa_com_movimentacao():
    for i in range(0, 101, 5):
        for j in range(0, 101, 5):
            for h in range(24):
                r = resultado(i / 100, j / 100, momento=datetime(2026, 9, 21, h))
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
            observada=rng.choice([None, rng.random()]),
            prevista=rng.choice([None, rng.random()]),
            ocorrencia=rng.random() < 0.1,
            momento=momento,
        )
        pretendido = inferir(BASE, e, NIVEIS_P3).nivel_pretendido
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
    assert DEGRAUS.rotulo == "v4-volume-degraus"
    assert DEGRAUS.hash_regras == BASE.hash_regras


def test_degraus_e_uma_tabela_com_poucos_niveis():
    niveis = {
        nivel(i / 100, j / 100, oc=oc, momento=datetime(2026, 9, 21, h), base=DEGRAUS)
        for i in range(0, 101, 4) for j in range(0, 101, 4) for h in range(0, 24, 3)
        for oc in (False, True)
    }
    assert len(niveis) <= 6


def test_degraus_coincide_com_mamdani_longe_das_fronteiras():
    for obs, prev in ((BAIXA, BAIXA), (MEDIA, MEDIA), (ALTA, BAIXA), (BAIXA, ALTA)):
        assert nivel(obs, prev, base=DEGRAUS) == nivel(obs, prev)


def test_degraus_salta_na_fronteira_e_mamdani_nao():
    salto_degraus = nivel(0.1039, 0.1039, base=DEGRAUS) - nivel(0.1037, 0.1037, base=DEGRAUS)
    salto_mamdani = nivel(0.1039, 0.1039) - nivel(0.1037, 0.1037)
    assert salto_degraus >= Decimal("0.2")
    assert abs(salto_mamdani) < Decimal("0.01")
