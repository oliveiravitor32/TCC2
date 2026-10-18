# Plano: mapa do recorte com nós fictícios (só para a demonstração na banca)

> **Para quem for executar:** leia este arquivo inteiro e o `CLAUDE.md` da raiz antes de começar. Avalie o plano, aponte riscos e só depois implemente, em commits pequenos e com mensagem em português. **Não faça push**: o autor faz.

## 1. O que é, em poucas palavras

Uma **tela nova no painel**, que passa a ser a tela inicial. Ela mostra o mapa do bairro **Jardim Helena**, em São Paulo, com **todos os 36 postes reais** do recorte do GeoSampa, cada um colorido conforme o seu estado.

Hoje só 2 desses postes existem no sistema:
- **BANCADA-01**: o ESP32 real;
- **SIMULADO-02**: um nó simulado.

Os outros **34 viram nós fictícios**, simulados por programa, para o mapa mostrar como seria o bairro inteiro sendo controlado.

O operador pode **selecionar vários trechos de rua no mapa** e, com um botão, **abrir uma ocorrência**. Os postes daqueles trechos vão ao pleno na hora. Outro botão **encerra** a ocorrência, e eles voltam a atenuar.

## 2. Objetivo

- Dar à banca uma **visão de conjunto**: como o sistema se comportaria num bairro, e não só num poste de bancada.
- Mostrar **controle em grupo** sem criar nenhum caminho que fuja da camada de verificação normativa.
- **Não alterar o documento do TCC.** É só para a apresentação. Se surgir algo importante que valha entrar no texto, avisar o autor antes.

## 3. Decisões já tomadas pelo autor

| Assunto | Decisão |
|---|---|
| Onde aparece | Só na demonstração; o texto do TCC **não** muda |
| Botão de grupo | **Opção A:** "abrir ocorrência" e "encerrar", pelo `POST /eventos` em pacote, que já existe. **Sem** "escolher nível" manual |
| Movimento que anima o mapa | **Opção C:** números inventados (uma noite que esvazia aos poucos), simples e controlável na apresentação |
| Ponto padrão | A aba Monitoramento e o `GET /energia` abrem sempre na **BANCADA-01**, mesmo com os 34 fictícios cadastrados |

## 4. Regras que não podem ser quebradas

1. **Nenhum comando chega a um poste sem passar pelo serviço de decisão e pela verificação de piso** (seção 3.7 do TCC). O botão de grupo só publica **eventos**, como a plataforma faria.
2. A BANCADA-01 e o SIMULADO-02 **continuam funcionando exatamente como hoje**, com as mesmas credenciais e a mesma ACL.
3. Os resultados do TCC **não podem mudar**: suíte de cenários, testes e números. Rodar `pytest` (262 testes hoje) e a suíte antes e depois.
4. Os nós fictícios têm **lux sintético** e devem ser marcados como fictícios no banco. Nunca aparecem como resultado.
5. Nada de segredo no git: `segredos.h`, `.env`, `senha_*.txt` e a chave da VM.
6. **VM:**
   - perguntar ao autor antes de acessar;
   - fazer backup do banco antes de qualquer migração;
   - **nunca** rodar `docker compose down -v`.

## 5. O que já existe e será reaproveitado

| Peça | Onde está | Para que serve aqui |
|---|---|---|
| 36 postes e 16 trechos reais | `Codigo/cadastro/dados/recorte_jardim_helena.json` | Lista dos pontos do mapa |
| Associação poste ↔ trecho (até 25 m) | `Codigo/cadastro/associar.py` | Gerar `trecho_ponto` dos 34 novos |
| Seed atual (2 postes) | `Codigo/db/seed_cadastro.sql` | Base do seed novo |
| Colunas `latitude`/`longitude` | `ponto_de_luz` em `Codigo/db/schema.sql` (hoje vazias; só UTM preenchido) | Posição no mapa |
| `GET /pontos`, `GET /trechos` | `Codigo/api_eventos/app.py` | Dados do mapa |
| `POST /eventos` em pacote (até 500) | idem | Botão de grupo |
| Rampa, validade e failsafe do nó | `Codigo/decisao/rampa.py` (`Controlador`) | Comportamento dos nós fictícios |
| Simulador de um nó | `Codigo/simulador/no_simulado.py` | Modelo para a frota |
| Credencial de nó novo | `Codigo/deploy/novo_no.sh` | Modelo para a credencial da frota |
| Painel (Vite + React + Tailwind 4 + lucide) | `Codigo/painel/` | Recebe a aba nova |

## 6. Arquitetura

```
gerador_volumes (números inventados) ──POST /eventos (pacote, 16 trechos, a cada 5 min)──► API ─► banco
                                                                                              │
Painel ── aba "Mapa" (tela inicial) ──GET /pontos e /trechos a cada 2–5 s                      ▼
        └─ botões "abrir ocorrência" / "encerrar" ──POST /eventos (pacote)           serviço de decisão
                                                                                     (inferência + piso)
                                                                                              │ MQTT comando
                         frota simulada: 1 processo, 34 nós, 1 conexão MQTT ◄─────────────────┤
                         BANCADA-01 (ESP32) e SIMULADO-02: sem mudança  ◄──────────────────────┘
```

O **serviço de decisão não muda**: ele já decide só para os postes do trecho que recebeu evento (RNF09).

## 7. Plano passo a passo

### Passo 1: Banco (cadastro dos 34 postes)
- **Migração** `Codigo/db/migracoes/011_pontos_simulados.sql`:
  - coluna `simulado BOOLEAN NOT NULL DEFAULT false` em `ponto_de_luz`;
  - atualizar também `db/schema.sql`.
- **Script que gera o seed novo** `db/seed_mapa.sql`, a partir do recorte:
  - insere os 34 postes restantes;
  - códigos com prefixo fixo, por exemplo `JH-` + placa (`JH-IP0412405`), para a ACL e para reconhecer de longe;
  - `simulado = true`, classe P3 e `estado_operacional = 'operante'`;
  - associações em `trecho_ponto` pelo mesmo critério de 25 m (`cadastro/associar.py`).
- **Preencher `latitude` e `longitude` de todos os 36**, convertendo de UTM SIRGAS 2000 / 23S (**EPSG:31983**) para WGS84 (**EPSG:4326**). Pode usar `pyproj` no script do seed, sem dependência nova no serviço.
- **Geometria dos trechos para o mapa:** `trecho_via.geometria` está em UTM. Gerar a versão em lat/long no próprio seed, em coluna nova ou JSON convertido.
- **Pronto quando:** `GET /pontos` lista 36 pontos, os 34 com `simulado=true`, todos com lat/long.

### Passo 2: API (só acrescentar campos)
- `GET /pontos`: acrescentar `latitude`, `longitude` e `simulado`.
- `GET /trechos`: acrescentar a geometria em lat/long.
- **BANCADA-01 como padrão:** onde o código escolhe um ponto sem que ele seja indicado (`GET /energia`, consultas do painel), usar a **BANCADA-01**, e nunca "o primeiro ponto da tabela".
- **Não mudar** o formato dos campos que já existem, para o painel atual não quebrar.
- Testes novos em `Codigo/tests/` para os campos e para o padrão BANCADA-01.

### Passo 3: Frota simulada (34 nós num processo)
- Arquivo novo `Codigo/simulador/frota.py`:
  - **um processo e uma conexão MQTT**, com credencial própria `FROTA-SIM`;
  - lê do banco, ou de arquivo, a lista de pontos com `simulado = true`;
  - para cada ponto, um `decisao.rampa.Controlador`. Assina `iluminacao/{ponto}/comando` e responde em `iluminacao/{ponto}/telemetria`, no mesmo formato do `no_simulado.py`: `decisao_id`, `duty`, `lux`, `nivel`, `nivel_antes`, `lux_antes`;
  - rampa a cada 5 s, failsafe ao vencer a validade (RNF07) e estado `online` no tópico de estado.
  - **Sobre a last will:** o MQTT só permite **uma last will por conexão**. Avaliar como marcar os 34 como "sem comunicação" se a frota cair, por exemplo com a frota publicando `offline` retido para cada ponto ao sair, e a last will num tópico próprio da frota.
- **ACL do Mosquitto** (`Codigo/deploy/broker/`):
  - linhas explícitas para a `FROTA-SIM` ler `iluminacao/JH-.../comando` e escrever `.../telemetria` e `.../estado` **só dos 34 códigos**;
  - gerar essas linhas por script;
  - a frota **não pode** escrever nos tópicos da BANCADA-01 nem do SIMULADO-02.
- Script de credencial no estilo do `deploy/novo_no.sh`.
- Testes: rampa e failsafe por ponto, e nenhum tópico fora da lista.

### Passo 4: Gerador de volumes (números inventados)
- Arquivo novo `Codigo/simulador/gerador_volumes.py`:
  - a cada 5 min, publica **um pacote** pelo `POST /eventos` com o volume dos 16 trechos, usando a chave de acesso;
  - **perfil inventado:**
    - começo da noite movimentado;
    - esvaziamento aos poucos até a madrugada;
    - pequena variação aleatória por trecho, com semente fixa;
    - alguns trechos sempre mais cheios, para o mapa não ficar uniforme;
  - `origem = "gerador-demo"`, para ficar claro na auditoria;
  - parâmetros simples pela linha de comando: intensidade e, se viável, um modo "noite acelerada".
  - **Atenção:** o serviço usa o relógio real, e a faixa horária (início da noite, madrugada) vem dele. Na apresentação durante o dia, o serviço trata o horário como "início da noite", como já acontece na bancada. O perfil inventado deve funcionar bem assim.
- **Não** publicar nos trechos da BANCADA-01 se isso atrapalhar a demonstração do nó real. Deixar opção para excluir trechos.

### Passo 5: Painel (aba "Mapa")
- **Dependências:** `leaflet` e `react-leaflet`, com fundo do **OpenStreetMap** e o crédito "© OpenStreetMap" visível. Fixar as versões no `package.json`.
- **Aba "Mapa"** como **tela inicial**. As abas atuais continuam iguais.
- **Visual:** seguir o estilo atual do painel, com Inter, branco/preto/azul, cantos retos e cursor de clique.
- **Cores dos postes, em duas dimensões:**
  - **preenchimento = nível atual:** pleno (P3), uma abaixo (P4) e mínima (P5), em tons de azul do mais forte ao mais fraco;
  - **borda ou ícone = saúde:** ok, alerta de diagnóstico, sem comunicação e manutenção.
- **Trechos** como linhas: cor do volume (baixo, médio, alto) ou destaque vermelho com ocorrência aberta.
- **Postes reais × fictícios:** diferença visual discreta, por exemplo a BANCADA-01 com marcador especial.
- **Clique no poste:** cartão com a última decisão (pretendido, emitido, restrição, lux) e link para a "decisão explicada", que já existe.
- **Seleção de trechos**, por clique ou por área, e dois botões:
  - **"Abrir ocorrência"**: pacote com `tipo: "ocorrencia", ocorrencia: "seguranca"` para os trechos escolhidos;
  - **"Encerrar"**: pacote com `ocorrencia: "encerrada"`.
- **Legenda** fixa e **resumo do recorte:** quantos postes em cada classe e quantos com alerta.
- **Atualização** a cada 2 a 5 s.
- **Celular:** não pode quebrar; o mapa pode ocupar a largura toda.

### Passo 6: Testes e conferência local
- `pytest` inteiro passando: hoje são 262 testes, mais os novos.
- Rodar a suíte de cenários e conferir que os números do TCC **não mudaram**: 667.200 passos, aderência de 98,2 %, energia de 75,7 % do pleno etc.
- Subir tudo localmente com docker compose, abrir o painel e conferir:
  - mapa com 36 pontos;
  - cores mudando com o gerador;
  - botão de grupo levando os postes ao pleno e o "encerrar" liberando;
  - aba Monitoramento ainda na BANCADA-01.

### Passo 7: Deploy (só com autorização do autor)
1. Pedir autorização para acessar a VM.
2. **Backup do banco** antes da migração.
3. Aplicar a migração 011 e o seed novo.
4. Criar a credencial `FROTA-SIM` e a ACL.
5. Subir `frota` e `gerador_volumes` como serviços novos no `docker-compose.prod.yml`, com **limite de tamanho de log**.
6. Publicar o painel novo na Vercel.
7. Conferir que a BANCADA-01 (ESP32 real) continua respondendo.

## 8. Pontos de atenção

- **Chave pública da demonstração:** o botão de grupo usa a `CHAVE_DEMO`, que já é pública no painel. Qualquer visitante pode abrir ocorrência em todos os trechos. O pior caso é luz a mais, aceitável para a demonstração. Revogar a chave depois da banca, como já está combinado.
- **Carga na VM gratuita:** 16 trechos a cada 5 min geram cerca de 36 decisões por rodada, o que é desprezível. A frota num processo só ocupa algumas dezenas de MB.
- **Documentação interna:**
  - registrar a mudança em `Codigo/DIVERGENCIAS_TCC.txt` como item novo, deixando claro que é só para a demonstração;
  - atualizar o `CLAUDE.md`, na seção de estrutura e de implantação.
- **Texto do TCC:** não mexer. Se o autor decidir incluir depois, as seções afetadas seriam:
  - 3.5.2 e Quadro 16 ("dois registros");
  - RF08, Quadro 13 e 3.12.6.1;
  - uma figura nova;
  - uma limitação sobre nós fictícios;
  - uma linha no Quadro 19.

## 9. Pronto quando

- [ ] 36 postes no mapa, os 34 fictícios marcados como tal
- [ ] Cores de nível e de saúde funcionando, com legenda
- [ ] Gerador de volumes deixando o mapa "vivo"
- [ ] Botões "abrir ocorrência" e "encerrar" em grupo funcionando pelo `POST /eventos`
- [ ] Aba Monitoramento e `GET /energia` abrindo na BANCADA-01
- [ ] BANCADA-01 e SIMULADO-02 sem nenhuma mudança de comportamento
- [ ] `pytest` passando e números da suíte iguais aos do TCC
- [ ] Commits pequenos, sem push, sem segredos
