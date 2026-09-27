#!/usr/bin/env bash
# Sobe todo o sistema de uma vez, para desenvolvimento e demonstracao.
#
#   ./subir.sh              banco, broker, API, decisao, no simulado e painel
#   ./subir.sh --sem-no     idem, mas sem o no simulado (use o ESP32 de verdade)
#   ./subir.sh --sem-painel idem, sem o painel
#
# Cada servico roda em segundo plano, com log em Codigo/.logs/.
# Para encerrar tudo:  ./parar.sh

set -u
cd "$(dirname "$0")"

PY=.venv/Scripts/python
LOGS=.logs
COM_NO=1
COM_PAINEL=1
for arg in "$@"; do
  case "$arg" in
    --sem-no) COM_NO=0 ;;
    --sem-painel) COM_PAINEL=0 ;;
    *) echo "opcao desconhecida: $arg"; exit 2 ;;
  esac
done

mkdir -p "$LOGS"

erro() { echo "ERRO: $*" >&2; exit 1; }
[ -x "$PY" ] || erro "ambiente Python nao encontrado em $PY"

# --------------------------------------------------------------------------
# 1. Banco e broker (Docker)
# --------------------------------------------------------------------------
echo "subindo banco e broker..."
docker compose up -d >/dev/null 2>&1 || erro "docker nao respondeu. O Docker Desktop esta aberto?"

printf "  aguardando o Postgres"
for _ in $(seq 1 40); do
  if docker compose exec -T db pg_isready -U iluminacao -d iluminacao >/dev/null 2>&1; then
    ok=1; break
  fi
  printf "."; sleep 1
done
echo
[ "${ok:-0}" = 1 ] || erro "o Postgres nao ficou pronto a tempo (veja: docker compose logs db)"

# --------------------------------------------------------------------------
# 2. Servicos Python
# --------------------------------------------------------------------------
subir() { # nome, log, comando...
  local nome="$1" log="$2"; shift 2
  echo "subindo $nome..."
  ("$@" > "$LOGS/$log" 2>&1 &)
}

subir "API de eventos"      api.log      "$PY" -m uvicorn api_eventos.app:app --port 8000
subir "servico de decisao"  servico.log  "$PY" -m decisao.servico
[ "$COM_NO" = 1 ] && subir "no simulado" no.log "$PY" -m simulador.no_simulado

# --------------------------------------------------------------------------
# 3. Painel
# --------------------------------------------------------------------------
if [ "$COM_PAINEL" = 1 ]; then
  if [ -d painel/node_modules ]; then
    echo "subindo painel..."
    (cd painel && npm run dev > "../$LOGS/painel.log" 2>&1 &)
  else
    echo "painel: node_modules ausente; rode  cd painel && npm install"
    COM_PAINEL=0
  fi
fi

# --------------------------------------------------------------------------
# 4. Conferencia
# --------------------------------------------------------------------------
printf "  aguardando a API"
for _ in $(seq 1 30); do
  if curl -s -o /dev/null localhost:8000/pontos; then api_ok=1; break; fi
  printf "."; sleep 1
done
echo

echo
if [ "${api_ok:-0}" = 1 ]; then
  echo "  API .......... http://localhost:8000/docs"
else
  echo "  API .......... NAO RESPONDEU (veja $LOGS/api.log)"
fi
[ "$COM_PAINEL" = 1 ] && echo "  painel ....... http://localhost:5173"
echo "  logs ......... $LOGS/"
echo
echo "publicar um evento de teste (movimentacao baixa: a luz desce em rampa):"
echo "  ./evento.sh 0.05"
echo "encerrar tudo:"
echo "  ./parar.sh"
