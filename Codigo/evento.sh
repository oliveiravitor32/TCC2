#!/usr/bin/env bash
# Publica um evento urbano na API, com o carimbo de tempo de agora.
#
#   ./evento.sh 0.05          movimentacao de 5 % (luz desce em rampa)
#   ./evento.sh 0.8           movimentacao alta (luz sobe na hora)
#   ./evento.sh chuva         condicao adversa: fluxo pleno obrigatorio
#   ./evento.sh limpo         encerra a condicao adversa
#   ./evento.sh seguranca     ocorrencia reportada: elevacao imediata
#   ./evento.sh encerrada     encerra a ocorrencia
#
# A movimentacao vale 15 min; as demais valem ate o evento que as encerra.

set -u
cd "$(dirname "$0")"

API=${API:-http://localhost:8000}
AGORA=$(date -u +%Y-%m-%dT%H:%M:%SZ)
VALOR=${1:-}

case "$VALOR" in
  "")
    echo "uso: ./evento.sh <0..1 | chuva | neblina | nevoeiro | limpo | seguranca | transito | encerrada>"
    exit 2 ;;
  chuva|neblina|nevoeiro|limpo)
    CORPO="{\"ocorrido_em\":\"$AGORA\",\"tipo\":\"meteorologia\",\"rotulo\":\"$VALOR\",\"origem\":\"evento.sh\"}" ;;
  seguranca|transito|encerrada)
    CORPO="{\"ocorrido_em\":\"$AGORA\",\"tipo\":\"ocorrencia\",\"rotulo\":\"$VALOR\",\"origem\":\"evento.sh\"}" ;;
  *)
    case "$VALOR" in
      0|1|0.*|1.0|.[0-9]*) ;;
      *) echo "valor invalido: $VALOR (use um numero de 0 a 1, ou um rotulo)"; exit 2 ;;
    esac
    CORPO="{\"ocorrido_em\":\"$AGORA\",\"tipo\":\"movimentacao\",\"valor\":$VALOR,\"origem\":\"evento.sh\"}" ;;
esac

RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/eventos" \
       -H "content-type: application/json" -d "$CORPO")
CODIGO=$(echo "$RESP" | tail -1)
CORPO_RESP=$(echo "$RESP" | sed '$d')

if [ "$CODIGO" = "201" ]; then
  echo "publicado: $CORPO_RESP"
  echo "(o servico decide na hora; acompanhe no painel ou em .logs/servico.log)"
else
  echo "falhou (HTTP $CODIGO): $CORPO_RESP"
  [ -z "$CODIGO" ] && echo "a API esta no ar? rode ./subir.sh"
  exit 1
fi
