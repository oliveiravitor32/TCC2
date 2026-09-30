"""Camada de previsao (TCC 3.6): persistencia, modelo treinado e o que
acontece quando falta historico.

O modelo treinado so existe depois de  python -m modelo.treinar; sem ele os
testes do XGBoost sao pulados.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from decisao.previsao import Historico, Persistencia, PrevisorXGBoost, carregar_previsor, feriado_nacional

MOMENTO = datetime(2026, 9, 22, 1, 0)  # terca, madrugada


def historico(valor: float, horas: int = 168) -> Historico:
    return Historico(momento=MOMENTO, observada=valor, serie={k: valor for k in range(1, horas + 1)})


def test_persistencia_devolve_a_observada():
    assert Persistencia().prever(historico(0.42)) == 0.42


# --------------------------------------------------------------------------
# Calendario
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "dia,esperado",
    [
        (date(2026, 1, 1), True),    # Ano-Novo
        (date(2026, 4, 3), True),    # Sexta-feira Santa (Pascoa em 5/4/2026)
        (date(2026, 2, 17), True),   # Carnaval
        (date(2026, 9, 7), True),    # Independencia
        (date(2026, 12, 25), True),  # Natal
        (date(2026, 9, 22), False),  # terca comum
    ],
)
def test_feriado_nacional(dia, esperado):
    assert feriado_nacional(dia) is esperado


# --------------------------------------------------------------------------
# Modelo treinado
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def xgb():
    try:
        return PrevisorXGBoost()
    except FileNotFoundError:
        pytest.skip("modelo ausente (rode: python -m modelo.treinar)")


def test_rotulo_do_modelo(xgb):
    assert xgb.rotulo == "xgboost-v1"
    assert xgb.horas_necessarias() >= 24


def test_sem_historico_cai_para_persistencia(xgb):
    # Nao inventa dado sobre buraco: devolve a observada.
    assert xgb.prever(Historico(MOMENTO, 0.37, {})) == 0.37
    assert xgb.prever(Historico(MOMENTO, 0.37, {1: 0.4, 2: 0.4})) == 0.37


def test_previsao_fica_no_universo(xgb):
    for v in (0.0, 0.1, 0.5, 1.0):
        assert 0.0 <= xgb.prever(historico(v)) <= 1.0


def test_previsao_acompanha_o_patamar_do_historico(xgb):
    assert xgb.prever(historico(0.05)) < xgb.prever(historico(0.6))


def test_carregar_previsor_escolhe_persistencia_quando_pedido():
    assert carregar_previsor("persistencia").rotulo == "persistencia"


def test_media_sazonal_usa_a_mesma_hora_das_semanas_anteriores():
    from datetime import datetime
    from decisao.previsao import Historico, MediaSazonal
    m = MediaSazonal()
    h = Historico(momento=datetime(2026, 9, 23, 1), observada=0.9, serie={167: 0.2, 335: 0.4, 1: 0.9})
    assert abs(m.prever(h) - 0.3) < 1e-9
    assert m.prever(Historico(momento=datetime(2026, 9, 23, 1), observada=0.7, serie={})) == 0.7
