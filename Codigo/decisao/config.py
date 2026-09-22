"""Parametros de OPERACAO do servico de decisao (nao normativos).

Os limites da NBR 5101 ficam na tabela classe_iluminacao (RF09). Aqui ficam
so as escolhas de projeto do ciclo, cada uma com a origem registrada em
DIVERGENCIAS_TCC.txt. Podem ser trocadas por variavel de ambiente.
"""

from __future__ import annotations

import os
from zoneinfo import ZoneInfo

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://iluminacao:iluminacao@localhost:5432/iluminacao"
)

# Ciclo de decisao e failsafe do no (DIVERGENCIAS 1 e 2).
PERIODO_S = float(os.environ.get("PERIODO_S", "5"))
TIMEOUT_FAILSAFE_S = float(os.environ.get("TIMEOUT_FAILSAFE_S", "15"))

# Evento de movimentacao sem vigente_ate vale por este tempo; depois disso o
# ciclo considera que nao ha dado e decide 1,0 (DIVERGENCIAS 23).
VALIDADE_MOVIMENTACAO_S = float(os.environ.get("VALIDADE_MOVIMENTACAO_S", "900"))

# Horario local do ponto de luz: a faixa horaria da inferencia depende dele.
FUSO = ZoneInfo(os.environ.get("FUSO", "America/Sao_Paulo"))

# MQTT (LACUNA 2): QoS 1, sem retain.
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORTA = int(os.environ.get("MQTT_PORTA", "1883"))
MQTT_USUARIO = os.environ.get("MQTT_USUARIO") or None
MQTT_SENHA = os.environ.get("MQTT_SENHA") or None
MQTT_CA = os.environ.get("MQTT_CA") or None  # caminho do certificado da CA (TLS)
MQTT_QOS = 1

TOPICO_COMANDO = "iluminacao/{ponto}/comando"
TOPICO_TELEMETRIA = "iluminacao/+/telemetria"
TOPICO_ESTADO = "iluminacao/+/estado"
