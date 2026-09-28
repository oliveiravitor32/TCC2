#!/usr/bin/env bash
# Publica a LEITURA de um trecho na API, com o carimbo de tempo de agora:
# quantas pessoas ha na area e se ha ocorrencia (DIVERGENCIAS 55).
#
#   ./evento.sh 0                  via vazia (a luz desce em rampa)
#   ./evento.sh 2                  duas pessoas: pleno na hora
#   ./evento.sh 0 seguranca        via vazia com ocorrencia: pleno
#   ./evento.sh 0 - 19400          no trecho 19400 (R. Varzea da Palma, SIMULADO-02)
#
# Argumentos: pessoas, ocorrencia (seguranca | transito | - para nenhuma) e
# trecho (GET /trechos lista os validos; sem ele, TRECHO do ambiente ou 20159,
# R. Antonio Viana, BANCADA-01). A leitura vale 1 min: a plataforma real
# publica a cada poucos segundos.
#
# Na VM:  API=https://seu-dominio CHAVE_API=... ./evento.sh 0

set -u
cd "$(dirname "$0")"

API=${API:-http://localhost:8000}
AGORA=$(date -u +%Y-%m-%dT%H:%M:%SZ)
PESSOAS=${1:-}
OCORRENCIA=${2:--}
TRECHO=${3:-${TRECHO:-20159}}

case "$PESSOAS" in
  ''|*[!0-9]*) echo "uso: ./evento.sh <pessoas> [seguranca|transito|-] [trecho]"; exit 2 ;;
esac
case "$TRECHO" in
  ''|*[!0-9]*) echo "trecho invalido: $TRECHO (use o numero do trecho; veja GET /trechos)"; exit 2 ;;
esac
case "$OCORRENCIA" in
  -) OC=null ;;
  seguranca|transito) OC="\"$OCORRENCIA\"" ;;
  *) echo "ocorrencia invalida: $OCORRENCIA (seguranca, transito ou -)"; exit 2 ;;
esac

CORPO="{\"ocorrido_em\":\"$AGORA\",\"pessoas\":$PESSOAS,\"ocorrencia\":$OC,\"origem\":\"evento.sh\",\"trecho\":$TRECHO}"

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
