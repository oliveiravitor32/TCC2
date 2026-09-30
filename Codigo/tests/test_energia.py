"""Estimativa de energia (TCC 3.11, RF12).

O caso de conferencia e o do proprio texto: a descida completa de P3 a P5,
que a norma obriga a durar ao menos cinco minutos, consome 2,50 Wh na
luminaria de referencia de 40 W, contra 3,33 Wh no mesmo intervalo em fluxo
pleno.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

import pytest

from decisao.energia import (
    Passo,
    energia_bancada,
    energia_decisoes,
    energia_passo,
    energia_pleno_constante,
    trajetoria_horario_fixo,
)

P40 = 40.0
T0 = datetime(2026, 9, 22, 0, 0)


# --------------------------------------------------------------------------
# Conferencia do texto
# --------------------------------------------------------------------------
def test_descida_de_p3_a_p5_em_cinco_minutos():
    e = energia_passo(Passo(anterior=1.0, nivel=0.5, minutos=5), P40)
    assert e == pytest.approx(2.50, abs=0.01)


def test_pleno_no_mesmo_intervalo():
    assert energia_pleno_constante(P40, 5) == pytest.approx(3.33, abs=0.01)


def test_razao_entre_regimes_nao_depende_da_potencia():
    # 3.11: a potencia nominal multiplica os dois regimes e cancela-se na
    # razao. Por isso os resultados sao reportados tambem a 440 W.
    for p in (40.0, 440.0):
        adaptativo = energia_passo(Passo(1.0, 0.5, 5), p)
        pleno = energia_pleno_constante(p, 5)
        assert adaptativo / pleno == pytest.approx(0.75, abs=0.001)


# --------------------------------------------------------------------------
# Forma da trajetoria
# --------------------------------------------------------------------------
def test_elevacao_e_imediata():
    # Subida nao tem rampa: o intervalo inteiro ja no nivel novo.
    assert energia_passo(Passo(0.5, 1.0, 5), P40) == pytest.approx(P40 * 5 / 60)


def test_nivel_mantido():
    assert energia_passo(Passo(0.5, 0.5, 10), P40) == pytest.approx(P40 * 0.5 * 10 / 60)


def test_passo_curto_integra_so_o_trecho_da_rampa():
    # 5 s de rampa a 0,1/min: cai 0,00833, media de 0,99583.
    e = energia_passo(Passo(1.0, 0.5, 5 / 60), P40)
    assert e == pytest.approx(P40 * 0.995833 * (5 / 60) / 60, rel=1e-4)


def test_rampa_em_passos_equivale_a_rampa_inteira():
    # A mesma descida, discretizada em passos de 5 s, da o mesmo total.
    inteira = energia_passo(Passo(1.0, 0.5, 5), P40)
    nivel, quando, passos = 1.0, T0, []
    while nivel > 0.5:
        novo = max(0.5, nivel - 0.1 * 5 / 60)
        passos.append((quando, nivel, novo))
        nivel, quando = novo, quando + timedelta(seconds=5)
    fim = T0 + timedelta(minutes=5)
    assert energia_decisoes(passos, P40, fim=fim) == pytest.approx(inteira, rel=1e-3)


def test_passo_sem_duracao_ou_sem_potencia_nao_consome():
    assert energia_passo(Passo(1.0, 0.5, 0), P40) == 0.0
    assert energia_passo(Passo(1.0, 0.5, 5), 0) == 0.0


# --------------------------------------------------------------------------
# Series
# --------------------------------------------------------------------------
def test_energia_de_sequencia_de_decisoes():
    # Uma hora no piso vale metade de uma hora no pleno.
    passos = [(T0, 0.5, 0.5)]
    assert energia_decisoes(passos, P40, fim=T0 + timedelta(hours=1)) == pytest.approx(20.0)


def test_sequencia_vazia_ou_sem_fim():
    assert energia_decisoes([], P40) == 0.0
    assert energia_decisoes([(T0, 1.0, 1.0)], P40) == 0.0  # sem fim, nada a integrar


def test_energia_de_bancada_usa_o_duty_medido():
    # Duty 0,25 por 1 h num segmento de 1,44 W.
    t = [(T0, 0.25)]
    assert energia_bancada(t, 1.44, fim=T0 + timedelta(hours=1)) == pytest.approx(0.36)


# --------------------------------------------------------------------------
# Linha de base por horario fixo
# --------------------------------------------------------------------------
def test_horario_fixo_atenua_na_janela_e_respeita_a_taxa():
    inicio = datetime(2026, 9, 22, 23, 0)
    fim = datetime(2026, 9, 23, 6, 0)
    passos = trajetoria_horario_fixo(
        inicio, fim, piso=0.5,
        hora_inicio_atenuacao=time(0, 0), hora_fim_atenuacao=time(5, 0),
    )
    niveis = {q: n for q, _, n in passos}
    assert niveis[datetime(2026, 9, 22, 23, 30)] == 1.0        # antes da janela
    assert niveis[datetime(2026, 9, 23, 0, 2)] == pytest.approx(0.8, abs=0.02)  # descendo
    assert niveis[datetime(2026, 9, 23, 3, 0)] == 0.5          # no piso
    assert niveis[datetime(2026, 9, 23, 5, 0)] == 1.0          # volta imediata
    # Nenhuma queda entre passos consecutivos excede a taxa normativa.
    assert all(a - n <= 0.1 * 5 / 60 + 1e-9 for _, a, n in passos)


def test_horario_fixo_gasta_menos_que_pleno_e_mais_que_so_o_piso():
    inicio, fim = datetime(2026, 9, 22, 18, 0), datetime(2026, 9, 23, 6, 0)
    passos = trajetoria_horario_fixo(
        inicio, fim, piso=0.5,
        hora_inicio_atenuacao=time(0, 0), hora_fim_atenuacao=time(5, 0),
    )
    e = energia_decisoes(passos, P40, fim=fim)
    minutos = (fim - inicio).total_seconds() / 60
    assert energia_pleno_constante(P40, minutos) * 0.5 < e < energia_pleno_constante(P40, minutos)


def test_horario_fixo_usa_o_horario_local_do_ponto():
    # DIVERGENCIAS 58: os instantes chegam em UTC; a programacao 0h-5h e de
    # Sao Paulo. 18h local = 21h UTC: a descida so pode comecar a 0h local.
    from zoneinfo import ZoneInfo
    sp = ZoneInfo("America/Sao_Paulo")
    inicio = datetime(2026, 9, 22, 18, 0, tzinfo=sp).astimezone(timezone.utc)
    passos = trajetoria_horario_fixo(
        inicio, inicio + timedelta(hours=12), piso=0.5,
        hora_inicio_atenuacao=time(0, 0), hora_fim_atenuacao=time(5, 0), fuso=sp,
    )
    primeira = next(q for q, _, n in passos if n < 1.0)
    assert primeira.astimezone(sp) == datetime(2026, 9, 23, 0, 0, tzinfo=sp)
