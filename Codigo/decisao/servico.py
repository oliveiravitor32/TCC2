"""Servico de decisao: processo sempre ligado (TCC 4.6.1).

Arquitetura de implantacao (DIVERGENCIAS 71; Caderno de Encargos 7.1.1 e
7.2.1): a decisao e POR EVENTO. Chegou volume ou ocorrencia de um trecho, o
servico decide para os pontos daquele trecho, confirma no banco e publica o
comando (QoS 1, sem retain) SO se o alvo mudou ou se o comando anterior esta
para vencer. Quem desce em rampa e volta ao pleno no vencimento e o
controlador (decisao.rampa; firmware/no/no.ino).

Uma varredura a cada VARREDURA_S decide de novo so os pontos cujo comando
esta vencendo (sem volume novo, o alvo vira o pleno) e recalcula a regua dos
trechos uma vez por dia. Em paralelo, recebe a telemetria e o estado (last
will) dos nos.

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
from datetime import datetime, timedelta, timezone

import paho.mqtt.client as mqtt
import psycopg

from . import config
from .ciclo import (
    Ponto,
    atualizar_estado_ponto,
    atualizar_referencias,
    decidir,
    decidir_grupo,
    id_modelo,
    marcar_publicada,
    pontos,
    pontos_do_evento,
    pontos_vencendo,
    referencias_vencidas,
    registrar_telemetria,
    registrar_versao_regras,
    ultimo_publicado,
)
from .diagnostico import Monitor
from .inferencia import carregar
from .previsao import carregar_previsor
from .rampa import deve_publicar

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
                estado = msg.payload.decode(errors="replace").strip()
                manutencao = estado == "manutencao"
                atualizar_estado_ponto(self.db_retorno, ponto, estado == "online", manutencao)
                log.info("no %s %s", ponto, "EM MANUTENCAO (serial)" if manutencao
                         else "online" if estado == "online" else "SEM COMUNICACAO")
        except (json.JSONDecodeError, psycopg.Error) as erro:
            log.warning("mensagem de %s ignorada: %s", msg.topic, erro)

    # -- Decisao ---------------------------------------------------------------
    def decidir_pontos(self, alvos: list[Ponto], motivo: str = "partida") -> int:
        """Decide para os pontos dados; publica so o necessario. Devolve
        quantos comandos foram publicados. `motivo` (evento=ID, varredura ou
        partida) vai para o log, para ligar a decisao ao evento da API."""
        publicados = 0
        # Uma avaliacao por grupo de controle (DIVERGENCIAS 76); ponto sem
        # grupo decide sozinho. A ordem dos pontos e preservada.
        grupos: dict[object, list[Ponto]] = {}
        for ponto in alvos:
            grupos.setdefault(ponto.grupo_id if ponto.grupo_id is not None else ("ponto", ponto.id),
                              []).append(ponto)
        for membros in grupos.values():
            try:
                agora = _agora()
                with self.db_ciclo.transaction():
                    decisoes = decidir_grupo(
                        self.db_ciclo,
                        membros,
                        base=self.base,
                        previsor=self.previsor,
                        agora=agora,
                        versao_regras_id=self.versao_regras_id,
                        versao_modelo_id=self.versao_modelo_id,
                        execucao_id=self.execucao_id,
                        reativo=self.reativo,
                    )
                    ultimos = [ultimo_publicado(self.db_ciclo, p.id) for p in membros]
            except psycopg.Error:
                log.exception("falha de banco na decisao do grupo de %s (motivo=%s)",
                              membros[0].codigo, motivo)
                continue
            for d, ultimo in zip(decisoes, ultimos):
                try:
                    publicados += self._publicar(d, ultimo, agora, motivo)
                except psycopg.Error:
                    log.exception("falha de banco ao publicar %s (motivo=%s)", d.ponto.codigo, motivo)
        return publicados

    def _publicar(self, d, ultimo, agora, motivo: str) -> int:
        """Publica o comando de uma decisao se o alvo mudou ou vai vencer."""
        ponto = d.ponto
        vence = agora + timedelta(seconds=d.validade_s)
        if not deve_publicar(ultimo, d.nivel_emitido, vence, agora, config.RENOVAR_ANTES_S):
            log.debug("decisao=%s ponto=%s motivo=%s alvo=%s mantido; nada publicado",
                      d.id, ponto.codigo, motivo, d.nivel_emitido)
            return 0
        publicado = 0
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
            publicado = 1
        else:
            log.warning("decisao=%s comando nao publicado (rc=%s)", d.id, info.rc)
        log.info(
            "decisao=%s ponto=%s grupo=%s motivo=%s pretendido=%s alvo=%s restricao=%s validade=%ss",
            d.id, ponto.codigo, ponto.grupo_id, motivo, d.nivel_pretendido, d.nivel_emitido,
            d.restricao_aplicada, d.validade_s,
        )
        # Eventos de seguranca em destaque (correcao da verificacao e
        # falta de dado), para nao se perderem entre as decisoes.
        if d.restricao_aplicada == "piso":
            log.warning("decisao=%s ponto=%s verificacao corrigiu o piso: %s -> %s",
                        d.id, ponto.codigo, d.nivel_pretendido, d.nivel_emitido)
        if d.observada is None:
            log.info("decisao=%s ponto=%s sem volume vigente: nivel pleno", d.id, ponto.codigo)
        return publicado

    def passo(self) -> int:
        """Decide para todos os pontos (partida do servico e testes)."""
        return self.decidir_pontos(pontos(self.db_ciclo))

    def varrer(self) -> int:
        """Regua diaria e renovacao dos comandos que estao vencendo."""
        agora = _agora()
        try:
            if referencias_vencidas(self.db_ciclo, agora):
                with self.db_ciclo.transaction():
                    atualizar_referencias(self.db_ciclo, agora)
            alvos = pontos_vencendo(self.db_ciclo, agora, config.RENOVAR_ANTES_S)
        except psycopg.Error:
            log.exception("falha de banco na varredura")
            return 0
        return self.decidir_pontos(alvos, "varredura")

    def ao_evento(self, evento_id: int) -> int:
        try:
            alvos = pontos_do_evento(self.db_ciclo, evento_id)
        except psycopg.Error:
            log.exception("falha de banco ao ler o evento %s", evento_id)
            return 0
        return self.decidir_pontos(alvos, f"evento={evento_id}")

    def executar(self, *, uma_vez: bool = False) -> None:
        aviso = psycopg.connect(config.DATABASE_URL, autocommit=True)
        aviso.execute("LISTEN evento_urbano")
        self.mqtt.connect_async(config.MQTT_HOST, config.MQTT_PORTA, keepalive=30)
        self.mqtt.loop_start()
        try:
            self.varrer()
            self.passo()
            proxima = time.monotonic() + config.VARREDURA_S
            while not uma_vez and not self._parar.is_set():
                # Fatias curtas para que o sinal de parada seja atendido.
                for n in aviso.notifies(timeout=0.5):
                    try:
                        self.ao_evento(int(n.payload))
                    except ValueError:
                        log.warning("aviso de evento malformado: %r", n.payload)
                if time.monotonic() >= proxima:
                    self.varrer()
                    proxima = time.monotonic() + config.VARREDURA_S
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
