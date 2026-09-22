"""Logica da calibracao (bancada/calibrar.py) sobre a bancada simulada.

Nao testa o hardware - testa que o procedimento encontra o duty por
medicao, que a tabela do firmware e monotona e que os pontos de 1,0 e do
piso sao exatamente os medidos (3.4.2).
"""

from __future__ import annotations

from bancada.calibrar import (
    DUTY_MAX,
    BancadaSimulada,
    Relatorio,
    buscar_duty,
    duties_varredura,
    media,
    tabela_firmware,
)


def test_busca_encontra_o_duty_do_alvo_por_medicao():
    b = BancadaSimulada(residual=0.3)
    d = buscar_duty(b, 10.0, residual=0.3)
    assert abs(media(b, d) - 0.3 - 10.0) < 0.1


def test_varredura_cobre_extremos():
    ds = duties_varredura(33)
    assert ds[0] == 0 and ds[-1] == DUTY_MAX and len(ds) == 33


def _relatorio(b: BancadaSimulada) -> Relatorio:
    r = Relatorio("P", "P3", 10.0, 5.0, 0.3, 18.0, None)
    for s in (1, 2, 3):
        r.series[s] = [(d, media(b, d) - 0.3) for d in duties_varredura(33)]
    r.duty_pleno = buscar_duty(b, 10.0, 0.3)
    r.duty_piso = buscar_duty(b, 5.0, 0.3, hi=r.duty_pleno)
    return r


def test_tabela_do_firmware_monotona_com_pontos_medidos():
    r = _relatorio(BancadaSimulada())
    t = tabela_firmware(r)
    assert t[0] == (0.0, 0)
    assert t[-1] == (1.0, r.duty_pleno)
    assert (0.5, r.duty_piso) in t
    assert all(n2 > n1 and d2 > d1 for (n1, d1), (n2, d2) in zip(t, t[1:]))
