"""No de bancada simulado: substitui o ESP32 enquanto o firmware nao existe.

Instrumento de desenvolvimento, NAO componente da proposta nem fonte de
resultado: os valores de lux aqui sao sinteticos. Reproduz o contrato do no
(Quadro 14) e o failsafe (RNF07):

- assina iluminacao/{ponto}/comando e responde em iluminacao/{ponto}/telemetria
  com o mesmo decisao_id;
- sem comando por TIMEOUT_FAILSAFE_S, vai sozinho a 1,0;
- last will em iluminacao/{ponto}/estado = "offline" (retido).

Execucao:  python -m simulador.no_simulado [--ponto BANCADA-01] [--falha]
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import ssl
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from decisao import config

# Suposicoes sinteticas, apenas para gerar numeros plausiveis (3.4.2):
DUTY_PLENO_CLASSE = 0.5   # iluminacao plena da classe em torno de metade do ciclo
LUX_PLENO_CLASSE = 10.0
LUX_RESIDUAL = 0.3
RUIDO_LUX = 0.1

log = logging.getLogger("no_simulado")


class NoSimulado:
    def __init__(self, ponto: str, falha: bool = False) -> None:
        self.ponto = ponto
        self.falha = falha  # simula ramo de potencia interrompido (3.4.5)
        self.nivel = 1.0
        self.ultimo_comando = time.monotonic()
        self.em_failsafe = False
        self._trava = threading.Lock()

        self.cli = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id=f"no-{ponto}", protocol=mqtt.MQTTv5
        )
        if config.MQTT_USUARIO:
            self.cli.username_pw_set(config.MQTT_USUARIO, config.MQTT_SENHA)
        if config.MQTT_CA:
            # Broker da VM (porta 8883): TLS com a CA propria (deploy/preparar.sh).
            self.cli.tls_set(ca_certs=config.MQTT_CA, tls_version=ssl.PROTOCOL_TLS_CLIENT)
        self.topico_estado = f"iluminacao/{ponto}/estado"
        self.cli.will_set(self.topico_estado, "offline", qos=1, retain=True)
        self.cli.on_connect = self._ao_conectar
        self.cli.on_message = self._ao_receber

    def _ao_conectar(self, cli, *_):
        cli.subscribe(f"iluminacao/{self.ponto}/comando", qos=1)
        cli.publish(self.topico_estado, "online", qos=1, retain=True)
        log.info("no %s conectado", self.ponto)

    def _duty(self, nivel: float) -> float:
        # A calibracao real e uma tabela medida (3.3); aqui, linear sintetica.
        return round(min(1.0, nivel * DUTY_PLENO_CLASSE), 4)

    def _lux(self, nivel: float) -> float:
        luz = 0.0 if self.falha else nivel * LUX_PLENO_CLASSE
        return round(max(0.0, luz + LUX_RESIDUAL + random.gauss(0, RUIDO_LUX)), 2)

    def _ao_receber(self, cli, _u, msg):
        try:
            cmd = json.loads(msg.payload)
            nivel = float(cmd["nivel"])
            did = str(cmd["decisao_id"])
        except (ValueError, KeyError, TypeError):
            log.warning("comando malformado: %r", msg.payload)
            return
        with self._trava:
            self.nivel = min(max(nivel, 0.0), 1.0)
            self.ultimo_comando = time.monotonic()
            self.em_failsafe = False
        telemetria = {
            "decisao_id": did,
            "duty": self._duty(self.nivel),
            "lux": self._lux(self.nivel),
            "medido_em": datetime.now(timezone.utc).isoformat(),
        }
        cli.publish(f"iluminacao/{self.ponto}/telemetria", json.dumps(telemetria), qos=1)
        log.info("nivel=%.3f duty=%.4f lux=%.2f", self.nivel, telemetria["duty"], telemetria["lux"])

    def _vigia_failsafe(self):
        while True:
            time.sleep(0.5)
            with self._trava:
                if (not self.em_failsafe
                        and time.monotonic() - self.ultimo_comando > config.TIMEOUT_FAILSAFE_S):
                    self.nivel, self.em_failsafe = 1.0, True
                    log.warning("FAILSAFE: sem comando ha %.0f s -> nivel 1,0",
                                config.TIMEOUT_FAILSAFE_S)

    def executar(self):
        threading.Thread(target=self._vigia_failsafe, daemon=True).start()
        self.cli.connect(config.MQTT_HOST, config.MQTT_PORTA, keepalive=30)
        self.cli.loop_forever()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ponto", default="BANCADA-01")
    p.add_argument("--falha", action="store_true", help="luminaria apagada (lux ~ residual)")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    NoSimulado(args.ponto, args.falha).executar()


if __name__ == "__main__":
    main()
