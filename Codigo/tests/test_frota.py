"""Visao de bairro (DIVERGENCIAS 76): frota simulada, ACL e cadastro do mapa."""

from __future__ import annotations

import json
from datetime import timedelta
from types import SimpleNamespace

from cadastro import mapa
from simulador.frota import Frota


class CliFalso:
    def __init__(self):
        self.publicados = []

    def publish(self, topico, carga, **_):
        self.publicados.append((topico, carga))


def _cmd(nivel, validade_s=900, did="d-1"):
    return SimpleNamespace(topic="", payload=json.dumps(
        {"decisao_id": did, "nivel": nivel, "validade_s": validade_s, "piso": 0.5, "taxa_min": 0.1}))


def test_frota_responde_so_aos_proprios_postes_e_desce_em_rampa():
    f = Frota(["JH-A", "JH-B"])
    cli = CliFalso()
    msg = _cmd(0.5)
    msg.topic = "iluminacao/JH-A/comando"
    f._ao_receber(cli, None, msg)
    assert cli.publicados and cli.publicados[0][0] == "iluminacao/JH-A/telemetria"
    tel = json.loads(cli.publicados[0][1])
    assert tel["decisao_id"] == "d-1" and tel["nivel_antes"] == 1.0
    estranho = _cmd(0.5)
    estranho.topic = "iluminacao/BANCADA-01/comando"
    f._ao_receber(cli, None, estranho)
    assert len(cli.publicados) == 1  # nao responde por poste que nao e da frota
    ctl = f.ctl["JH-A"]
    from datetime import datetime, timezone
    agora = datetime.now(timezone.utc)
    niveis = [float(ctl.passo(agora + timedelta(seconds=5 * i), 5)) for i in range(1, 80)]
    assert all(a - b <= 0.1 / 12 + 1e-9 for a, b in zip([1.0] + niveis, niveis))  # taxa
    assert min(niveis) >= 0.5  # piso
    assert float(f.ctl["JH-B"].luz) == 1.0  # o outro poste nao foi tocado


def test_frota_volta_ao_pleno_quando_a_validade_vence():
    from datetime import datetime, timezone

    f = Frota(["JH-A"])
    msg = _cmd(0.5, validade_s=60)
    msg.topic = "iluminacao/JH-A/comando"
    f._ao_receber(CliFalso(), None, msg)
    ctl = f.ctl["JH-A"]
    agora = datetime.now(timezone.utc)
    ctl.passo(agora + timedelta(seconds=30), 30)
    assert float(ctl.luz) < 1.0
    assert float(ctl.passo(agora + timedelta(seconds=61), 5)) == 1.0  # RNF07


def test_acl_da_frota_nao_alcanca_os_nos_reais():
    bloco = mapa.bloco_acl()
    assert "BANCADA-01" not in bloco and "SIMULADO-02" not in bloco
    assert bloco.count("topic read iluminacao/JH-") == len(mapa.codigos_simulados()) == 33


def test_conversao_utm_cai_no_jardim_helena():
    lat, lon = mapa.utm23s_para_wgs84(354624.63, 7401981.80)  # BANCADA-01
    assert -23.50 < lat < -23.47 and -46.44 < lon < -46.41


def test_seed_do_mapa_marca_os_postes_como_simulados():
    sql = mapa.gerar_sql()
    assert sql.count("INSERT INTO ponto_de_luz") == 33
    assert sql.count(", true)\n") == 33
