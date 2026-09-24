"""Servico de decisao: processo sempre ligado (TCC 4.6.1).

A cada PERIODO_S, para cada ponto de luz: decide, confirma no banco, publica
o comando (QoS 1, sem retain) e marca o instante da publicacao. Em paralelo,
recebe a telemetria e o estado (last will) dos nos.

Execucao:  python -m decisao.servico [--reativo] [--execucao-id N]
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import ssl
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import psycopg

from . import config
from .ciclo import (
    atualizar_estado_ponto,
    decidir,
    id_modelo,
    marcar_publicada,
    pontos,
    registrar_telemetria,
    registrar_versao_regras,
)
from .diagnostico import Monitor
from .inferencia import carregar
from .previsao import carregar_previsor

log = logging.getLogger("decisao")


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _ponto_do_topico(topico: str) -> str:
    # iluminacao/{ponto}/telemetria
    return topico.split("/")[1]


class Servico:
    def __init__(self, *, reativo: bool = False, execucao_id: int | None = None,
                 previsao: str | None = None) -> None:
        self.reativo = reativo
        self.execucao_id = execucao_id
        self.base = carregar(config.REGRAS)
        # Sem argumento: o modelo treinado, se existir; senao, persistencia.
        self.previsor = carregar_previsor(previsao)
        self.monitor = Monitor()  # diagnostico do ponto de luz (RF11)
        self._parar = threading.Event()

        # Duas conexoes: o psycopg nao e seguro entre threads, e os callbacks
        # MQTT rodam na thread de rede do paho.
        # autocommit: cada `with transaction()` e uma transacao real e confirmada;
        # sem ele, vira savepoint de uma transacao que nunca se confirma.
        self.db_ciclo = psycopg.connect(config.DATABASE_URL, autocommit=True)
        self.db_retorno = psycopg.connect(config.DATABASE_URL, autocommit=True)
        with self.db_ciclo.transaction():
            self.versao_regras_id = registrar_versao_regras(self.db_ciclo, self.base)
            self.versao_modelo_id = id_modelo(self.db_ciclo, self.previsor.rotulo)

        log.info("previsao: %s", self.previsor.rotulo)
        self.mqtt = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="servico-decisao",
            protocol=mqtt.MQTTv5,
        )
        if config.MQTT_USUARIO:
            self.mqtt.username_pw_set(config.MQTT_USUARIO, config.MQTT_SENHA)
        if config.MQTT_CA:
            self.mqtt.tls_set(ca_certs=config.MQTT_CA, tls_version=ssl.PROTOCOL_TLS_CLIENT)
        self.mqtt.on_connect = self._ao_conectar
        self.mqtt.on_message = self._ao_receber
        self.mqtt.reconnect_delay_set(min_delay=1, max_delay=10)

    # -- MQTT ---------------------------------------------------------------
    def _ao_conectar(self, cliente, _userdata, _flags, codigo, _props) -> None:
        if codigo.is_failure:
            log.error("broker recusou a conexao: %s", codigo)
            return
        cliente.subscribe(
            [(config.TOPICO_TELEMETRIA, config.MQTT_QOS), (config.TOPICO_ESTADO, config.MQTT_QOS)]
        )
        log.info("conectado ao broker %s:%s", config.MQTT_HOST, config.MQTT_PORTA)

    def _ao_receber(self, _cliente, _userdata, msg: mqtt.MQTTMessage) -> None:
        ponto = _ponto_do_topico(msg.topic)
        try:
            if msg.topic.endswith("/telemetria"):
                carga = json.loads(msg.payload)
                if registrar_telemetria(self.db_retorno, ponto, carga):
                    # A telemetria acabou de ser gravada: diagnostica o ponto
                    # (RF11). O alerta so registra, nao altera o nivel.
                    diag = self.monitor.avaliar(self.db_retorno, carga["decisao_id"])
                    if diag and diag != "normal":
                        log.warning("%s: %s", ponto, diag)
                else:
                    log.debug("telemetria descartada ou duplicada: %s", carga)
            elif msg.topic.endswith("/estado"):
                online = msg.payload.decode(errors="replace").strip() == "online"
                atualizar_estado_ponto(self.db_retorno, ponto, online)
                log.info("no %s %s", ponto, "online" if online else "SEM COMUNICACAO")
        except (json.JSONDecodeError, psycopg.Error) as erro:
            log.warning("mensagem de %s ignorada: %s", msg.topic, erro)

    # -- Ciclo ---------------------------------------------------------------
    def passo(self) -> None:
        for ponto in pontos(self.db_ciclo):
            try:
                with self.db_ciclo.transaction():
                    d = decidir(
                        self.db_ciclo,
                        base=self.base,
                        previsor=self.previsor,
                        ponto=ponto,
                        agora=_agora(),
                        versao_regras_id=self.versao_regras_id,
                        versao_modelo_id=self.versao_modelo_id,
                        execucao_id=self.execucao_id,
                        reativo=self.reativo,
                    )
                # A decisao ja esta confirmada: a telemetria pode referencia-la.
                info = self.mqtt.publish(
                    config.TOPICO_COMANDO.format(ponto=ponto.codigo),
                    json.dumps(d.comando()),
                    qos=config.MQTT_QOS,
                    retain=False,
                )
                if info.rc == mqtt.MQTT_ERR_SUCCESS:
                    with self.db_ciclo.transaction():
                        marcar_publicada(self.db_ciclo, d.id, _agora())
                else:
                    log.warning("comando %s nao publicado (rc=%s)", d.id, info.rc)
                log.info(
                    "%s pretendido=%s emitido=%s restricao=%s",
                    ponto.codigo, d.nivel_pretendido, d.nivel_emitido, d.restricao_aplicada,
                )
            except psycopg.Error:
                log.exception("falha de banco no ciclo de %s", ponto.codigo)

    def _aguardar(self, aviso: psycopg.Connection, ate: float) -> None:
        """Espera o proximo ciclo; um evento novo antecipa a decisao (RNF03).

        O ciclo periodico continua existindo: ele conduz a rampa e mantem o
        no alimentado de comandos, longe do failsafe.
        """
        while not self._parar.is_set():
            restante = ate - time.monotonic()
            if restante <= 0:
                return
            # Fatias curtas para que o sinal de parada seja atendido.
            if list(aviso.notifies(timeout=min(restante, 0.5), stop_after=1)):
                self.passo()

    def executar(self, *, uma_vez: bool = False) -> None:
        aviso = psycopg.connect(config.DATABASE_URL, autocommit=True)
        aviso.execute("LISTEN evento_urbano")
        self.mqtt.connect_async(config.MQTT_HOST, config.MQTT_PORTA, keepalive=30)
        self.mqtt.loop_start()
        try:
            proximo = time.monotonic()
            while not self._parar.is_set():
                self.passo()
                if uma_vez:
                    break
                proximo += config.PERIODO_S
                self._aguardar(aviso, proximo)
        finally:
            self.mqtt.loop_stop()
            self.mqtt.disconnect()
            aviso.close()
            self.db_ciclo.close()
            self.db_retorno.close()

    def parar(self, *_: object) -> None:
        self._parar.set()


def main() -> None:
    p = argparse.ArgumentParser(description="Servico de decisao (TCC 4.6.1)")
    p.add_argument("--reativo", action="store_true", help="inferencia sem previsao (H3)")
    p.add_argument("--execucao-id", type=int, default=None, help="execucao_cenario em curso")
    p.add_argument("--previsao", choices=["persistencia", "xgboost"], default=None,
                   help="forca a camada de previsao (padrao: o modelo treinado, se houver)")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    s = Servico(reativo=args.reativo, execucao_id=args.execucao_id, previsao=args.previsao)
    signal.signal(signal.SIGINT, s.parar)
    signal.signal(signal.SIGTERM, s.parar)
    s.executar()


if __name__ == "__main__":
    main()
