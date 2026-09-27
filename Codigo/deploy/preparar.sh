#!/usr/bin/env bash
# Prepara os segredos da implantacao, UMA vez, na maquina virtual.
#
#   ./deploy/preparar.sh seu-subdominio.duckdns.org
#
# Gera, todos fora do git:
#   .env                        senhas do banco e do broker, chave da API
#   deploy/broker/certs/        CA propria e certificado do broker (TLS 8883)
#   deploy/broker/passwd        usuarios do broker: servico e BANCADA-01
#
# Ao final, mostra o que precisa ir para o segredos.h do ESP32 e para o
# evento.sh. Rodar de novo NAO sobrescreve nada que ja exista.
set -eu
cd "$(dirname "$0")/.."

DOMINIO=${1:-}
[ -n "$DOMINIO" ] || { echo "uso: ./deploy/preparar.sh seu-subdominio.duckdns.org"; exit 2; }
command -v openssl >/dev/null || { echo "falta o openssl (sudo apt install openssl)"; exit 1; }
command -v docker  >/dev/null || { echo "falta o docker (veja deploy/ROTEIRO.md)"; exit 1; }

PONTO=BANCADA-01
CERTS=deploy/broker/certs
PASSWD=deploy/broker/passwd
aleatorio() { openssl rand -hex 24; }   # so [0-9a-f]: seguro em URL e em .env

# ---------------------------------------------------------------- .env
if [ -f .env ]; then
  echo ".env ja existe: mantido"
else
  cat > .env <<EOF
DOMINIO=$DOMINIO
SENHA_BANCO=$(aleatorio)
CHAVE_API=$(aleatorio)
SENHA_MQTT_SERVICO=$(aleatorio)
SENHA_MQTT_NO=$(aleatorio)
# Depois de publicar o painel, troque * pelo endereco dele na Vercel
# (ex.: https://tcc-iluminacao.vercel.app) e rode o "up" de novo.
ORIGENS_PAINEL=*
EOF
  chmod 600 .env
  echo ".env criado"
fi
# shellcheck disable=SC1091
. ./.env

# ---------------------------------------------------------- certificados
# CA propria: o no confia nela (certificado colado no segredos.h). O
# certificado do broker vale para o dominio, que e o nome que o no usa.
if [ -f "$CERTS/servidor.crt" ]; then
  echo "certificados ja existem: mantidos"
else
  mkdir -p "$CERTS"
  openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
    -keyout "$CERTS/ca.key" -out "$CERTS/ca.crt" \
    -subj "/CN=CA Iluminacao Adaptativa (TCC)" 2>/dev/null
  openssl req -newkey rsa:2048 -nodes \
    -keyout "$CERTS/servidor.key" -out "$CERTS/servidor.csr" \
    -subj "/CN=$DOMINIO" 2>/dev/null
  printf "subjectAltName=DNS:%s\nextendedKeyUsage=serverAuth\n" "$DOMINIO" > "$CERTS/ext.cnf"
  openssl x509 -req -in "$CERTS/servidor.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" \
    -CAcreateserial -days 825 -extfile "$CERTS/ext.cnf" -out "$CERTS/servidor.crt" 2>/dev/null
  rm -f "$CERTS/servidor.csr" "$CERTS/ext.cnf"
  echo "certificados criados para $DOMINIO"
fi

# ----------------------------------------------------- usuarios do broker
if [ -f "$PASSWD" ]; then
  echo "passwd do broker ja existe: mantido"
else
  : > "$PASSWD"
  docker run --rm -v "$PWD/deploy/broker:/m" eclipse-mosquitto:2 sh -c \
    "mosquitto_passwd -b /m/passwd servico '$SENHA_MQTT_SERVICO' && mosquitto_passwd -b /m/passwd '$PONTO' '$SENHA_MQTT_NO'"
  echo "usuarios do broker criados: servico e $PONTO"
fi

# O Mosquitto roda como usuario 1883 dentro do conteiner: ele precisa ler a
# chave e o passwd, e ninguem mais.
sudo chown -R 1883:1883 "$CERTS" "$PASSWD"
sudo chmod 600 "$CERTS/servidor.key" "$CERTS/ca.key" "$PASSWD"
sudo chmod 644 "$CERTS/ca.crt" "$CERTS/servidor.crt"

cat <<EOF

==================================================================
Pronto. Proximo passo: docker compose -f docker-compose.prod.yml up -d --build

Para o segredos.h do ESP32:
  #define MQTT_URI     "mqtts://$DOMINIO:8883"
  #define MQTT_USUARIO "$PONTO"
  #define MQTT_SENHA   "$SENHA_MQTT_NO"
  e o certificado da CA (ca.crt) em MQTT_CA_PEM:
EOF
sudo cat "$CERTS/ca.crt"
cat <<EOF

Para publicar eventos (evento.sh ou qualquer cliente):
  API=https://$DOMINIO CHAVE_API=$CHAVE_API ./evento.sh 0.05
==================================================================
EOF
