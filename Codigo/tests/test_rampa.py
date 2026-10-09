"""Controlador da luminaria (DIVERGENCIAS 71): rampa, piso, validade e a
regra de publicacao da central. Puro: sem banco e sem rede.

A taxa e o piso sao conferidos por SEQUENCIAS aleatorias de comandos (como
os 100 mil casos de test_verificacao.py): seja qual for a ordem de alvos,
validades e intervalos, a luz nunca desce mais que a taxa por passo nem fica
abaixo do piso enquanto ha comando, e volta ao pleno quando ele vence.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from decisao.rampa import Comando, Controlador, deve_publicar

T0 = datetime(2031, 3, 10, 4, 0, tzinfo=timezone.utc)
PISO, TAXA, PASSO = Decimal("0.5"), Decimal("0.1"), 5


def cmd(nivel, validade_s=900, piso=PISO, taxa=TAXA, did="d"):
    return Comando(did, Decimal(str(nivel)), validade_s, piso, taxa)


def test_liga_no_pleno_ate_o_primeiro_comando():
    c = Controlador()
    assert c.passo(T0, PASSO) == Decimal("1.000")


def test_desce_na_taxa_e_chega_ao_alvo_em_pelo_menos_cinco_minutos():
    c = Controlador()
    c.receber(cmd(0.5), T0)
    niveis, agora = [], T0
    for _ in range(80):
        agora += timedelta(seconds=PASSO)
        niveis.append(c.passo(agora, PASSO))
    assert niveis[0] == Decimal("0.992")
    assert (niveis.index(Decimal("0.500")) + 1) * PASSO >= 300
    assert niveis[-1] == Decimal("0.500")


def test_sobe_na_hora():
    c = Controlador()
    c.receber(cmd(0.5), T0)
    for k in range(1, 80):
        c.passo(T0 + timedelta(seconds=PASSO * k), PASSO)
    c.receber(cmd(0.75), T0 + timedelta(seconds=400))
    assert c.passo(T0 + timedelta(seconds=405), PASSO) == Decimal("0.750")


def test_alvo_abaixo_do_piso_para_no_piso():
    # Segunda barreira: mesmo um comando errado nao leva a luz abaixo do piso.
    c = Controlador()
    c.receber(cmd(0.1, validade_s=1200), T0)
    for k in range(1, 200):
        luz = c.passo(T0 + timedelta(seconds=PASSO * k), PASSO)
    assert luz == Decimal("0.500")


def test_comando_vencido_volta_ao_pleno():
    c = Controlador()
    c.receber(cmd(0.5, validade_s=600), T0)
    for k in range(1, 119):
        c.passo(T0 + timedelta(seconds=PASSO * k), PASSO)
    assert c.luz == Decimal("0.500")
    assert c.passo(T0 + timedelta(seconds=600), PASSO) == Decimal("1.000")


def test_comando_novo_renova_a_validade():
    c = Controlador()
    c.receber(cmd(0.5, validade_s=600), T0)
    c.receber(cmd(0.5, validade_s=600), T0 + timedelta(seconds=500))
    assert not c.vencido(T0 + timedelta(seconds=1000))
    assert c.vencido(T0 + timedelta(seconds=1100))


@pytest.mark.parametrize("carga", [
    {"decisao_id": "x", "nivel": 0.5, "validade_s": 0, "piso": 0.5, "taxa_min": 0.1},
    {"decisao_id": "x", "nivel": 1.5, "validade_s": 60, "piso": 0.5, "taxa_min": 0.1},
    {"decisao_id": "x", "nivel": 0.5, "piso": 0.5, "taxa_min": 0.1},
])
def test_comando_malformado_e_recusado(carga):
    with pytest.raises((ValueError, KeyError)):
        Comando.de_carga(carga)


def test_carga_ida_e_volta():
    c = cmd(0.75, 840)
    assert Comando.de_carga(c.carga()) == c


def test_sequencias_aleatorias_nunca_violam_taxa_nem_piso():
    rng = random.Random(71)
    passo_max = TAXA * PASSO / 60
    for _ in range(2000):
        c, agora, luz_ant = Controlador(), T0, Decimal("1.000")
        for _ in range(60):
            if rng.random() < 0.3:
                c.receber(cmd(round(rng.uniform(0, 1), 3), rng.randint(1, 1200)), agora)
            agora += timedelta(seconds=PASSO)
            luz = c.passo(agora, PASSO)
            if c.vencido(agora):
                assert luz == Decimal("1.000")
            else:
                assert luz >= PISO
                assert luz_ant - luz <= passo_max + Decimal("0.0005")
            luz_ant = luz


# --------------------------------------------------------------------------
# Regra de publicacao da central
# --------------------------------------------------------------------------
V = timedelta(minutes=15)


def test_publica_o_primeiro_comando():
    assert deve_publicar(None, Decimal("1"), T0 + V, T0, 300)


def test_publica_quando_o_alvo_muda():
    assert deve_publicar((Decimal("1"), T0 + V), Decimal("0.5"), T0 + V, T0, 300)


def test_alvo_igual_longe_do_vencimento_nao_publica():
    ultimo = (Decimal("0.5"), T0 + V)
    assert not deve_publicar(ultimo, Decimal("0.5"), T0 + timedelta(minutes=20),
                             T0 + timedelta(minutes=5), 300)


def test_renova_perto_do_vencimento_se_estender():
    ultimo = (Decimal("0.5"), T0 + V)
    agora = T0 + timedelta(minutes=10)
    assert deve_publicar(ultimo, Decimal("0.5"), agora + V, agora, 300)
    # Com o dado acabando, o comando novo venceria junto: nada a renovar.
    assert not deve_publicar(ultimo, Decimal("0.5"), T0 + V, agora, 300)
