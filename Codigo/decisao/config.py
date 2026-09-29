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

# Base de regras vigente (3.7): volume de movimento com saida em degraus de
# classe (DIVERGENCIAS 56). As anteriores ficam registradas em
# versao_base_regras.
REGRAS = Path(__file__).resolve().parent / "regras" / os.environ.get("REGRAS", "v4-volume.toml")

# Ciclo de decisao e failsafe do no (DIVERGENCIAS 1 e 2).
PERIODO_S = float(os.environ.get("PERIODO_S", "5"))
TIMEOUT_FAILSAFE_S = float(os.environ.get("TIMEOUT_FAILSAFE_S", "15"))

# Volume (DIVERGENCIAS 56): a plataforma publica a media de pessoas de cada
# trecho a cada PERIODO_VOLUME_S - 5 min, o tempo minimo que a norma impoe
# para descer do pleno ao piso. A media vale 3 periodos (a logica do
# failsafe do no: tolera duas publicacoes perdidas); vencida sem renovacao, o
# ciclo considera que nao ha dado e decide o pleno (DIVERGENCIAS 23).
PERIODO_VOLUME_S = int(os.environ.get("PERIODO_VOLUME_S", "300"))
VALIDADE_VOLUME_S = float(os.environ.get("VALIDADE_VOLUME_S", str(3 * PERIODO_VOLUME_S)))
# Ocorrencia: vale ate a plataforma publicar o encerramento ou ate vencer a
# vigencia informada, o que vier primeiro; sem vigencia, este prazo.
VALIDADE_OCORRENCIA_S = float(os.environ.get("VALIDADE_OCORRENCIA_S", "900"))
# Um POST pode trazer um trecho ou um pacote (envio por regiao).
MAX_ITENS_PACOTE = int(os.environ.get("MAX_ITENS_PACOTE", "500"))

# Referencia do trecho (media horaria de pessoas no percentil 99): aprendida
# das leituras dos ultimos DIAS_REFERENCIA dias quando ha ao menos
# HORAS_MINIMAS_REFERENCIA horas com leitura; antes disso, vale o valor
# inicial de trecho_via.referencia_pessoas (DIVERGENCIAS 55).
DIAS_REFERENCIA = int(os.environ.get("DIAS_REFERENCIA", "28"))
HORAS_MINIMAS_REFERENCIA = int(os.environ.get("HORAS_MINIMAS_REFERENCIA", "168"))

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
