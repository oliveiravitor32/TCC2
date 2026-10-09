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
REGRAS = Path(__file__).resolve().parent / "regras" / os.environ.get("REGRAS", "v6-zurique.toml")

# Arquitetura de implantacao (DIVERGENCIAS 71; Caderno de Encargos 7.1.1 e
# 7.2.1): a central decide quando chega volume ou ocorrencia e so publica
# quando o alvo muda ou falta RENOVAR_ANTES_S para o comando vencer; a rampa
# e a validade ficam no controlador.
#
# PERIODO_S = passo da rampa no no (DIVERGENCIAS 1) e amostragem da luz nos
# cenarios. Com a taxa de 0,1/min e 3 casas, 5 s da a rampa P3 -> P5 em 5,2
# min; um passo de 1 s arredondaria a queda para 0,001 e alongaria a rampa.
PERIODO_S = float(os.environ.get("PERIODO_S", "5"))
# Varredura da central: comandos perto de vencer e regua diaria. Nao publica
# nada sozinha; so decide de novo os pontos cujo comando esta vencendo.
VARREDURA_S = float(os.environ.get("VARREDURA_S", "60"))
# RNF03 (DIVERGENCIAS 71): comando efetivado no no em ate 180 s, o prazo da
# rede de conectividade do Caderno de Encargos (7.2.1). Referencia para a
# medicao; o servico nao depende dele.
LATENCIA_MAX_S = float(os.environ.get("LATENCIA_MAX_S", "180"))

# Volume (DIVERGENCIAS 56): a plataforma publica a media de pessoas de cada
# trecho a cada PERIODO_VOLUME_S - 5 min, o tempo minimo que a norma impoe
# para descer do pleno ao piso. A media vale 3 periodos (a logica do
# failsafe do no: tolera duas publicacoes perdidas); vencida sem renovacao, o
# ciclo considera que nao ha dado e decide o pleno (DIVERGENCIAS 23).
PERIODO_VOLUME_S = int(os.environ.get("PERIODO_VOLUME_S", "300"))
VALIDADE_VOLUME_S = float(os.environ.get("VALIDADE_VOLUME_S", str(3 * PERIODO_VOLUME_S)))
# Validade do comando no no: no maximo a do volume (DIVERGENCIAS 71), e no
# caso geral ate vencer o volume que sustenta a decisao - sem dado vigente, o
# no volta ao pleno na mesma hora em que a central decidiria o pleno.
VALIDADE_COMANDO_MAX_S = int(os.environ.get("VALIDADE_COMANDO_MAX_S", str(int(VALIDADE_VOLUME_S))))
RENOVAR_ANTES_S = float(os.environ.get("RENOVAR_ANTES_S", str(PERIODO_VOLUME_S)))
# Regua do trecho recalculada uma vez por dia (DIVERGENCIAS 71).
REFERENCIA_A_CADA_S = float(os.environ.get("REFERENCIA_A_CADA_S", str(24 * 3600)))
# Ocorrencia: vale ate a plataforma publicar o encerramento ou ate vencer a
# vigencia informada, o que vier primeiro; sem vigencia, este prazo.
VALIDADE_OCORRENCIA_S = float(os.environ.get("VALIDADE_OCORRENCIA_S", "900"))
# Um POST pode trazer um trecho ou um pacote (envio por regiao).
MAX_ITENS_PACOTE = int(os.environ.get("MAX_ITENS_PACOTE", "500"))

# Serie da previsao em BLOCOS de BLOCO_PREVISAO_MIN minutos (DIVERGENCIAS 69:
# 15 min, a resolucao do modelo de Zurique). Referencia do trecho = percentil
# 99 das medias de pessoas por bloco nos ultimos DIAS_REFERENCIA dias, quando
# ha ao menos BLOCOS_MINIMOS_REFERENCIA blocos com leitura (672 x 15 min = 7
# dias); antes disso, o valor inicial de trecho_via.referencia_pessoas
# (DIVERGENCIAS 55).
BLOCO_PREVISAO_MIN = int(os.environ.get("BLOCO_PREVISAO_MIN", "15"))
DIAS_REFERENCIA = int(os.environ.get("DIAS_REFERENCIA", "28"))
BLOCOS_MINIMOS_REFERENCIA = int(os.environ.get("BLOCOS_MINIMOS_REFERENCIA", "672"))

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
