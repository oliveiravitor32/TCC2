# Roteiro de implantação na VM da Oracle (passo 10)

VM: Ubuntu 24.04, ARM (VM.Standard.A2.Flex). Tudo roda em Docker; o painel
vai para a Vercel. Faça as etapas na ordem. Onde está `seu-subdominio`,
use o nome que você criar no DuckDNS.

---

## 1. Domínio no DuckDNS (no navegador, uma vez)

1. Entre em <https://www.duckdns.org> e faça login.
2. Crie um subdomínio (ex.: `tcc-iluminacao`), o que dá `tcc-iluminacao.duckdns.org`.
3. No campo **current ip**, coloque o **IP público** da VM (Oracle: Compute →
   Instances → sua instância → "Public IP address") e clique em **update ip**.

Confira no seu PC (o resultado deve mostrar o IP da VM):

```bash
nslookup seu-subdominio.duckdns.org
```

## 2. Portas na Oracle (no console da Oracle, uma vez)

Networking → Virtual Cloud Networks → sua VCN → Security Lists → Default
Security List → **Add Ingress Rules**. Crie três regras, todas com
Source CIDR `0.0.0.0/0`, protocolo TCP:

| Porta | Para quê |
|---|---|
| 80 | validação do certificado HTTPS (Let's Encrypt) |
| 443 | API em HTTPS (o painel e o `evento.sh` usam) |
| 8883 | MQTT com TLS (o ESP32 usa) |

Não abra 5432 (banco) nem 1883: eles ficam só dentro da VM.

## 3. Firewall do Ubuntu (na VM, uma vez)

As imagens Ubuntu da Oracle vêm com o `iptables` bloqueando tudo além do SSH.
Conecte por SSH na VM e rode:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8883 -j ACCEPT
sudo netfilter-persistent save
```

## 4. Docker e o código (na VM, uma vez)

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git openssl
sudo usermod -aG docker $USER
```

Saia do SSH e entre de novo (para o grupo `docker` valer). Depois:

```bash
git clone https://github.com/oliveiravitor32/TCC2.git
cd TCC2/Codigo
```

Se o repositório for privado, o `git clone` pede usuário e senha: a senha é
um *personal access token* do GitHub (Settings → Developer settings →
Personal access tokens), não a sua senha.

## 5. Segredos (na VM, uma vez)

```bash
./deploy/preparar.sh seu-subdominio.duckdns.org
```

O script cria as senhas, a chave da API, os certificados do broker e os
usuários do broker. **Ao final ele mostra** o que vai para o `segredos.h` do
ESP32 e a chave da API: copie para um lugar seguro (gerenciador de senhas).
Nada disso vai para o git.

## 6. Subir (na VM)

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

Os cinco serviços (db, broker, api, decisao, caddy) devem aparecer como `Up`.
A primeira construção leva alguns minutos.

Carregue a calibração da bancada (sessão 72), **uma vez só**:

```bash
docker compose -f docker-compose.prod.yml exec -T db psql -U iluminacao -d iluminacao < deploy/calibracao_bancada.sql
```

Confira (no seu PC ou na VM):

```bash
curl https://seu-subdominio.duckdns.org/pontos
```

Deve voltar um JSON com o ponto `BANCADA-01`. Se der erro de certificado,
espere um minuto (o Caddy está tirando o certificado) e veja
`docker compose -f docker-compose.prod.yml logs caddy`.

## 7. Painel na Vercel

1. Em <https://vercel.com>, **Add New → Project** e importe o repositório `TCC2`.
2. **Root Directory**: `Codigo/painel`. Framework: Vite (detectado sozinho).
3. Em **Environment Variables**: `VITE_API_URL` = `https://seu-subdominio.duckdns.org`.
4. **Deploy**. Anote o endereço gerado (ex.: `https://tcc2-xyz.vercel.app`).

De volta à VM, restrinja a API a esse endereço: edite o `.env`
(`nano .env`), troque `ORIGENS_PAINEL=*` pelo endereço do painel e rode:

```bash
docker compose -f docker-compose.prod.yml up -d
```

## 8. ESP32

No `firmware/no/segredos.h` (no seu PC), use o que o `preparar.sh` mostrou:

```cpp
#define MQTT_URI     "mqtts://seu-subdominio.duckdns.org:8883"
#define MQTT_USUARIO "BANCADA-01"
#define MQTT_SENHA   "a-senha-que-o-script-mostrou"
static const char *MQTT_CA_PEM = R"(-----BEGIN CERTIFICATE-----
...cole aqui o certificado inteiro que o script mostrou...
-----END CERTIFICATE-----
)";
```

Grave no ESP32 e abra o Monitor Serial: deve aparecer a conexão ao broker, e
o painel deve mostrar o ponto online.

## 9. Teste rápido

No seu PC (Git Bash, pasta `Codigo`):

```bash
API=https://seu-subdominio.duckdns.org CHAVE_API=a-chave-do-script ./evento.sh 0.05
```

A luz deve começar a descer em rampa, e o painel deve mostrar isso.

---

## Comandos úteis (na VM, pasta `TCC2/Codigo`)

| Para | Comando |
|---|---|
| ver o estado | `docker compose -f docker-compose.prod.yml ps` |
| ver logs da decisão | `docker compose -f docker-compose.prod.yml logs -f decisao` |
| atualizar o código | `git pull && docker compose -f docker-compose.prod.yml up -d --build` |
| parar tudo | `docker compose -f docker-compose.prod.yml down` (o banco é mantido) |

Nunca use `down -v`: o `-v` apaga o banco (decisões, telemetria e calibração).
