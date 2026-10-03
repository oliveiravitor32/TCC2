"""Conferencia da calibracao (bancada/conferir.py) sobre a bancada simulada.

Nao testa o hardware - testa que a conferencia aprova uma tabela que casa
com a bancada, reprova a que nao casa ou a residual alta, e que a tolerancia
sem banco segue a mesma regra do diagnostico.
"""

from __future__ import annotations

from bancada.calibrar import BancadaSimulada, Relatorio, buscar_duty, duties_varredura, media, tabela_firmware
from bancada.conferir import Conferencia, conferir, niveis_a_conferir, tolerancia_do_relatorio
from decisao import config


def _calibrada(b: BancadaSimulada) -> list[tuple[float, int]]:
    r = Relatorio("P", "P3", 10.0, 5.0, b.residual, 18.0, None)
    for s in (1, 2, 3):
        r.series[s] = [(d, media(b, d) - b.residual) for d in duties_varredura(33)]
    r.duty_pleno = buscar_duty(b, 10.0, b.residual)
    r.duty_piso = buscar_duty(b, 5.0, b.residual, hi=r.duty_pleno)
    return tabela_firmware(r)


def _conf(tol: float = 0.05) -> Conferencia:
    return Conferencia("P", "P3", 10.0, 5.0, 1, tol, "teste")


def test_niveis_sao_os_tres_degraus_de_classe():
    assert niveis_a_conferir(10.0, 5.0) == [1.0, 0.75, 0.5]


def test_aprova_tabela_que_casa_com_a_bancada():
    b = BancadaSimulada(residual=0.2)
    b.enviar_tabela(_calibrada(b), 1)
    c = conferir(b, _conf())
    assert c.aprovada and len(c.niveis) == 3


def test_reprova_quando_a_bancada_mudou():
    b = BancadaSimulada(residual=0.2)
    b.enviar_tabela(_calibrada(b), 1)
    b.teto = 14.0  # sensor afastado / fita trocada depois da calibracao
    c = conferir(b, _conf())
    assert not c.aprovada and "recalibre" in c.motivo


def test_reprova_fita_apagada_com_motivo_proprio():
    b = BancadaSimulada(residual=0.2)
    b.enviar_tabela(_calibrada(b), 1)
    b.teto = 0.0
    c = conferir(b, _conf())
    assert not c.aprovada and "nao acende" in c.motivo


def test_residual_alta_para_antes_de_medir():
    b = BancadaSimulada(residual=0.8)  # > 5 % de 10 lx
    b.enviar_tabela(_calibrada(BancadaSimulada(residual=0.8)), 1)
    c = conferir(b, _conf())
    assert not c.residual_ok and not c.niveis and not c.aprovada


def test_tolerancia_sem_banco_tem_piso_de_resolucao():
    # Sessao 72: tres repeticoes identicas (dispersao zero) -> vale o piso de
    # resolucao do sensor, como em diagnostico.tolerancia_do_ponto.
    rel = {"lux_piso": 5.0, "duty_pleno": 2352, "duty_piso": 1217,
           "repeticoes_pleno_lux": [9.96, 9.96, 9.96], "repeticoes_piso_lux": [4.98, 4.98, 4.98],
           "series": {}}
    esperado = config.DEGRAUS_TOLERANCIA * config.RESOLUCAO_SENSOR_LUX / 5.0
    assert abs(tolerancia_do_relatorio(rel) - esperado) < 1e-9


def test_tolerancia_sem_banco_usa_a_dispersao_quando_maior():
    rel = {"lux_piso": 5.0, "duty_pleno": 2352, "duty_piso": 1217,
           "repeticoes_pleno_lux": [9.0, 10.0, 11.0], "repeticoes_piso_lux": [5.0, 5.0, 5.0],
           "series": {}}
    assert tolerancia_do_relatorio(rel) > 0.25  # 3 x 10 % de dispersao
