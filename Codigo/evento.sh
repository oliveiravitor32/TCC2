#!/usr/bin/env bash
# Publica na API, com o carimbo de tempo de agora, o que a plataforma de
# monitoramento publicaria para um trecho (DIVERGENCIAS 56):
#
#   ./evento.sh volume 0.2            media de 0,2 pessoa nos ultimos 5 min
#   ./evento.sh volume 4              movimento alto: classe da via
#   ./evento.sh ocorrencia seguranca  ocorrencia: classe da via na hora
#   ./evento.sh ocorrencia encerrada  fecha a ocorrencia do trecho
#   ./evento.sh volume 0 19400        no trecho 19400 (R. Varzea da Palma, SIMULADO-02)
#
# Terceiro argumento: o trecho (GET /trechos lista os validos; sem ele, TRECHO
# do ambiente ou 20159, R. Antonio Viana, BANCADA-01). O volume vale 15 min
# (3 periodos de 5 min); a ocorrencia, ate 'encerrada' ou 15 min.
#
# Na VM:  API=https://seu-dominio CHAVE_API=... ./evento.sh volume 0

set -u
cd "$(dirname "$0")"

API=${API:-http://localhost:8000}
AGORA=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TIPO=${1:-}
VALOR=${2:-}
TRECHO=${3:-${TRECHO:-20159}}
USO="uso: ./evento.sh volume <media de pessoas> [trecho]  |  ./evento.sh ocorrencia <seguranca|transito|encerrada> [trecho]"

case "$TRECHO" in
  ''|*[!0-9]*) echo "trecho invalido: $TRECHO (use o numero do trecho; veja GET /trechos)"; exit 2 ;;
esac
case "$TIPO" in
  volume)
    case "$VALOR" in
      ''|*[!0-9.]*|*.*.*) echo "$USO"; exit 2 ;;
    esac
    CAMPOS="\"tipo\":\"volume\",\"pessoas_media\":$VALOR,\"periodo_s\":300" ;;
  ocorrencia)
    case "$VALOR" in
      seguranca|transito|encerrada) CAMPOS="\"tipo\":\"ocorrencia\",\"ocorrencia\":\"$VALOR\"" ;;
      *) echo "$USO"; exit 2 ;;
    esac ;;
  *) echo "$USO"; exit 2 ;;
esac

CORPO="{\"ocorrido_em\":\"$AGORA\",$CAMPOS,\"origem\":\"evento.sh\",\"trecho\":$TRECHO}"

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
