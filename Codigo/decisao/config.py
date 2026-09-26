"""Parametros de OPERACAO do servico de decisao (nao normativos).

Os limites da NBR 5101 ficam na tabela classe_iluminacao (RF09). Aqui ficam
so as escolhas de projeto do ciclo, cada uma com a origem registrada em
DIVERGENCIAS_TCC.txt. Podem ser trocadas por variavel de ambiente.
"""

from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://iluminacao:iluminacao@localhost:5432/iluminacao"
)

# Base de regras vigente (3.7): tercis reais da serie (item 31), sem a
# condicao meteorologica (item 49). As versoes v0 e v1 ficam no historico do
# git e registradas em versao_base_regras.
REGRAS = Path(__file__).resolve().parent / "regras" / os.environ.get("REGRAS", "v2-sem-meteorologia.toml")

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

# Diagnostico do ponto de luz (RF11, 3.4.5).
# A tolerancia NAO e arbitrada: sai da dispersao medida no ensaio de
# repetibilidade (3.4.4), multiplicada por K_SIGMA. Os contadores sao
# diferentes porque os fenomenos sao diferentes: falha total e condicao
# inequivoca; perda de controle e gradual e o alerta so registra.
K_SIGMA = float(os.environ.get("K_SIGMA", "3"))
CICLOS_FALHA_TOTAL = int(os.environ.get("CICLOS_FALHA_TOTAL", "3"))
CICLOS_PERDA_CONTROLE = int(os.environ.get("CICLOS_PERDA_CONTROLE", "12"))
# Enquanto nao houver ensaio de repetibilidade, esta tolerancia provisoria
# evita alarme falso; o valor definitivo vem da bancada.
TOLERANCIA_PROVISORIA = float(os.environ.get("TOLERANCIA_PROVISORIA", "0.15"))
# Resolucao do BH1750 em alta resolucao 2 com MTreg = 254: cada contagem vale
# (1/1,2) x (69/254) / 2 = 0,113 lx. A tolerancia nao pode ficar abaixo do que
# o instrumento distingue, senao o proprio sensor dispara o alerta (3.4.5).
RESOLUCAO_SENSOR_LUX = float(os.environ.get("RESOLUCAO_SENSOR_LUX", "0.113"))
# Piso da tolerancia em degraus do sensor, no menor nivel operado: meio degrau
# porque o valor esperado cai entre dois degraus, mais um degrau de oscilacao
# entre series (na sessao 72, 15 de 33 pontos diferiram em exatamente um).
DEGRAUS_TOLERANCIA = float(os.environ.get("DEGRAUS_TOLERANCIA", "1.5"))
