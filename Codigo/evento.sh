#!/usr/bin/env bash
# Publica um evento urbano na API, com o carimbo de tempo de agora.
#
#   ./evento.sh 0.05          movimentacao de 5 % (luz desce em rampa)
#   ./evento.sh 0.8           movimentacao alta (luz sobe na hora)
#   ./evento.sh seguranca     ocorrencia reportada: elevacao imediata
#   ./evento.sh encerrada     encerra a ocorrencia
#   ./evento.sh 0.05 19400    no trecho 19400 (R. Varzea da Palma, SIMULADO-02)
#
# O segundo argumento e o trecho de via (GET /trechos lista os validos). Sem
# ele, vale TRECHO do ambiente ou 20159 (R. Antonio Viana, BANCADA-01).
#
# A movimentacao vale 15 min; as demais valem ate o evento que as encerra.
#
# Na VM:  API=https://seu-dominio CHAVE_API=... ./evento.sh 0.05

set -u
cd "$(dirname "$0")"

API=${API:-http://localhost:8000}
AGORA=$(date -u +%Y-%m-%dT%H:%M:%SZ)
VALOR=${1:-}
TRECHO=${2:-${TRECHO:-20159}}
case "$TRECHO" in
  ''|*[!0-9]*) echo "trecho invalido: $TRECHO (use o numero do trecho; veja GET /trechos)"; exit 2 ;;
esac

case "$VALOR" in
  "")
    echo "uso: ./evento.sh <0..1 | seguranca | transito | encerrada> [trecho]"
    exit 2 ;;
  seguranca|transito|encerrada)
    CORPO="{\"ocorrido_em\":\"$AGORA\",\"tipo\":\"ocorrencia\",\"rotulo\":\"$VALOR\",\"origem\":\"evento.sh\",\"trecho\":$TRECHO}" ;;
  *)
    case "$VALOR" in
      0|1|0.*|1.0|.[0-9]*) ;;
      *) echo "valor invalido: $VALOR (use um numero de 0 a 1, ou um rotulo)"; exit 2 ;;
    esac
    CORPO="{\"ocorrido_em\":\"$AGORA\",\"tipo\":\"movimentacao\",\"valor\":$VALOR,\"origem\":\"evento.sh\",\"trecho\":$TRECHO}" ;;
esac

RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/eventos" \
       -H "content-type: application/json" -H "X-Chave-Api: ${CHAVE_API:-}" -d "$CORPO")
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
