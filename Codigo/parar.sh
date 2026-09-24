#!/usr/bin/env bash
# Encerra o que o subir.sh iniciou.
#
#   ./parar.sh            para API, decisao, no simulado e painel
#   ./parar.sh --tudo     para tambem o banco e o broker (docker compose down)

set -u
cd "$(dirname "$0")"

echo "encerrando processos..."
powershell -NoProfile -Command "
  Get-CimInstance Win32_Process -Filter \"Name='python.exe' or Name='node.exe'\" |
    Where-Object { \$_.CommandLine -match 'uvicorn api_eventos|decisao.servico|simulador.no_simulado|vite' } |
    ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }
" >/dev/null 2>&1

if [ "${1:-}" = "--tudo" ]; then
  echo "parando banco e broker..."
  docker compose down >/dev/null 2>&1
  echo "tudo parado (os dados do banco ficam no volume; 'docker compose down -v' apagaria)."
else
  echo "banco e broker continuam no ar (use ./parar.sh --tudo para parar tambem)."
fi
