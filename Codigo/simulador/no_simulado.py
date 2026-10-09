"""No de bancada simulado: substitui o ESP32 enquanto o firmware nao existe.

Instrumento de desenvolvimento, NAO componente da proposta nem fonte de
resultado: os valores de lux aqui sao sinteticos. Reproduz o contrato do no
(Quadro 14) e o controlador da arquitetura de implantacao (DIVERGENCIAS 71),
pela mesma classe que o executor de cenarios usa (decisao.rampa):

- assina iluminacao/{ponto}/comando e responde em iluminacao/{ponto}/telemetria
  com o mesmo decisao_id e o nivel que aplicava ao receber;
- desce ate o alvo em rampa, a cada PERIODO_S, sem passar da taxa nem do piso
  recebidos; sobe na hora;
- vencida a validade do comando, volta sozinho a 1,0 (RNF07);
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
from decisao.rampa import Comando, Controlador

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
        self.ctl = Controlador()
        self.em_failsafe = True  # liga no pleno, ate o primeiro comando
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

    @staticmethod
    def _agora() -> datetime:
        return datetime.now(timezone.utc)

    def _ao_receber(self, cli, _u, msg):
        try:
            cmd = Comando.de_carga(json.loads(msg.payload))
        except (ValueError, KeyError, TypeError):
            log.warning("comando malformado: %r", msg.payload)
            return
        with self._trava:
            self.ctl.receber(cmd, self._agora())
            self.em_failsafe = False
            nivel = float(self.ctl.luz)  # a rampa anda no passo; agora e o nivel atual
        telemetria = {
            "decisao_id": cmd.decisao_id,
            "duty": self._duty(nivel),
            "lux": self._lux(nivel),
            "nivel": nivel,
            "medido_em": self._agora().isoformat(),
        }
        cli.publish(f"iluminacao/{self.ponto}/telemetria", json.dumps(telemetria), qos=1)
        log.info("alvo=%.3f validade=%ss nivel=%.3f lux=%.2f", float(cmd.nivel), cmd.validade_s,
                 nivel, telemetria["lux"])

    def _rampa(self):
        """Passo da rampa e vigia da validade, no relogio do proprio no."""
        while True:
            time.sleep(config.PERIODO_S)
            with self._trava:
                agora = self._agora()
                vencido = self.ctl.comando is not None and self.ctl.vencido(agora)
                self.ctl.passo(agora, config.PERIODO_S)
                if vencido and not self.em_failsafe:
                    self.em_failsafe = True
                    log.warning("FAILSAFE: comando vencido sem renovacao -> nivel 1,0")

    def executar(self):
        threading.Thread(target=self._rampa, daemon=True).start()
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
