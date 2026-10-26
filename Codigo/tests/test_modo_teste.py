"""Modo de teste do painel (forcar evento imediato): so demonstracao."""

from datetime import datetime, timezone
from decimal import Decimal as D

from decisao.rampa import Comando, Controlador


def _cmd(nivel, imediato):
    return Comando("x", D(nivel), 900, D("0.5"), D("0.1"), imediato)


def test_comando_imediato_vai_direto_ao_alvo_sem_passar_do_piso():
    agora = datetime.now(timezone.utc)
    c = Controlador()
    c.receber(_cmd("0.5", True), agora)
    assert c.passo(agora, 0) == D("0.5")
    c.receber(_cmd("0.2", True), agora)  # abaixo do piso: fica no piso
    assert c.passo(agora, 0) == D("0.5")


def test_comando_normal_continua_em_rampa():
    agora = datetime.now(timezone.utc)
    c = Controlador()
    c.receber(_cmd("0.5", False), agora)
    assert c.passo(agora, 0) == D("1.000")
    assert c.passo(agora, 5) < D("1.000")


def test_carga_so_leva_imediato_quando_ligado():
    assert "imediato" not in _cmd("0.5", False).carga()
    c = _cmd("0.5", True)
    assert c.carga()["imediato"] is True
    assert Comando.de_carga(c.carga()).imediato is True
