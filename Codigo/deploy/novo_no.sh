#!/usr/bin/env bash
# Da credencial no broker a um no novo, na VM (RNF06, RNF09).
#
#   ./deploy/novo_no.sh SIMULADO-02
#
# O codigo tem de ser o mesmo de ponto_de_luz.codigo: a ACL deixa cada no
# ler e escrever so os topicos do proprio codigo. Nada muda no servico de
# decisao nem na ACL - so esta linha no passwd e o registro no banco.
# Mostra a senha gerada UMA vez; guarde-a (segredos do no).
set -eu
cd "$(dirname "$0")/.."

CODIGO=${1:-}
case "$CODIGO" in
  ''|*[!A-Za-z0-9-]*) echo "uso: ./deploy/novo_no.sh CODIGO   (letras, numeros e hifen)"; exit 2 ;;
esac
PASSWD=deploy/broker/passwd
sudo test -f "$PASSWD" || { echo "rode antes o deploy/preparar.sh"; exit 1; }
if sudo grep -q "^$CODIGO:" "$PASSWD"; then
  echo "$CODIGO ja tem credencial no broker"; exit 1
fi

SENHA=$(openssl rand -hex 24)
# O passwd pertence ao usuario do Mosquitto (1883): o conteiner edita.
docker run --rm --user 1883:1883 -v "$PWD/deploy/broker:/m" eclipse-mosquitto:2 \
  mosquitto_passwd -b /m/passwd "$CODIGO" "$SENHA"
# Recarrega usuarios sem derrubar as conexoes.
docker compose -f docker-compose.prod.yml kill -s HUP broker >/dev/null

cat <<EOF
Credencial criada para $CODIGO.
  MQTT_USUARIO=$CODIGO
  MQTT_SENHA=$SENHA
O ponto precisa existir em ponto_de_luz com o mesmo codigo e ter trecho em
trecho_ponto (db/seed_cadastro.sql).
EOF
