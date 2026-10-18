"""Frota de nos simulados da visao de bairro (DIVERGENCIAS 76).

Um processo e UMA conexao MQTT (usuario FROTA-SIM) para todos os postes
simulados do recorte (cadastro/mapa.py). Cada poste tem o seu controlador
(decisao.rampa.Controlador), com a mesma regra do no de bancada: sobe na hora,
desce em rampa sem passar da taxa nem do piso recebidos e volta ao pleno
quando a validade vence (RNF07). Lux SINTETICO: instrumento de demonstracao,
nunca fonte de resultado.

A last will e uma so por conexao: fica em iluminacao/FROTA-SIM/estado. Ao
sair normalmente, a frota publica "offline" (retido) no estado de cada poste.

Execucao:  MQTT_USUARIO=FROTA-SIM MQTT_SENHA=... python -m simulador.frota
"""

from __future__ import annotations

import json
import logging
import random
import signal
import ssl
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from cadastro.mapa import USUARIO_FROTA, codigos_simulados
from decisao import config
from decisao.rampa import Comando, Controlador

LUX_PLENO_CLASSE = 10.0
DUTY_PLENO_CLASSE = 0.5
LUX_RESIDUAL = 0.3
RUIDO_LUX = 0.1

log = logging.getLogger("frota")


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Frota:
    def __init__(self, codigos: list[str]) -> None:
        self.ctl = {c: Controlador() for c in codigos}
        self._trava = threading.Lock()
        self._parar = threading.Event()
        self.cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="frota-sim",
                               protocol=mqtt.MQTTv5)
        if config.MQTT_USUARIO:
            self.cli.username_pw_set(config.MQTT_USUARIO, config.MQTT_SENHA)
        if config.MQTT_CA:
            self.cli.tls_set(ca_certs=config.MQTT_CA, tls_version=ssl.PROTOCOL_TLS_CLIENT)
        self.cli.will_set(f"iluminacao/{USUARIO_FROTA}/estado", "offline", qos=1, retain=True)
        self.cli.on_connect = self._ao_conectar
        self.cli.on_message = self._ao_receber

    @staticmethod
    def _lux(nivel: float) -> float:
        return round(max(0.0, nivel * LUX_PLENO_CLASSE + LUX_RESIDUAL + random.gauss(0, RUIDO_LUX)), 2)

    def _ao_conectar(self, cli, *_):
        for c in self.ctl:
            cli.subscribe(f"iluminacao/{c}/comando", qos=1)
            cli.publish(f"iluminacao/{c}/estado", "online", qos=1, retain=True)
        cli.publish(f"iluminacao/{USUARIO_FROTA}/estado", "online", qos=1, retain=True)
        log.info("frota conectada: %s postes simulados", len(self.ctl))

    def _ao_receber(self, cli, _u, msg):
        partes = msg.topic.split("/")
        codigo = partes[1] if len(partes) == 3 else None
        if codigo not in self.ctl:
            return
        try:
            cmd = Comando.de_carga(json.loads(msg.payload))
        except (ValueError, KeyError, TypeError):
            log.warning("comando malformado para %s: %r", codigo, msg.payload)
            return
        with self._trava:
            ctl = self.ctl[codigo]
            nivel_antes = float(ctl.luz)
            ctl.receber(cmd, _agora())
            nivel = float(ctl.luz)
        carga = {
            "decisao_id": cmd.decisao_id,
            "duty": round(min(1.0, nivel * DUTY_PLENO_CLASSE), 4),
            "lux": self._lux(nivel),
            "nivel": nivel,
            "nivel_antes": nivel_antes,
            "lux_antes": self._lux(nivel_antes),
            "medido_em": _agora().isoformat(),
        }
        cli.publish(f"iluminacao/{codigo}/telemetria", json.dumps(carga), qos=1)

    def _rampa(self):
        while not self._parar.wait(config.PERIODO_S):
            with self._trava:
                agora = _agora()
                for ctl in self.ctl.values():
                    ctl.passo(agora, config.PERIODO_S)

    def parar(self, *_):
        self._parar.set()

    def executar(self):
        threading.Thread(target=self._rampa, daemon=True).start()
        self.cli.connect(config.MQTT_HOST, config.MQTT_PORTA, keepalive=30)
        self.cli.loop_start()
        try:
            while not self._parar.wait(1):
                pass
        finally:
            for c in self.ctl:
                self.cli.publish(f"iluminacao/{c}/estado", "offline", qos=1, retain=True)
            self.cli.publish(f"iluminacao/{USUARIO_FROTA}/estado", "offline", qos=1, retain=True)
            time.sleep(1)
            self.cli.loop_stop()
            self.cli.disconnect()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    frota = Frota(sorted(codigos_simulados()))
    signal.signal(signal.SIGTERM, frota.parar)
    signal.signal(signal.SIGINT, frota.parar)
    frota.executar()


if __name__ == "__main__":
    main()
