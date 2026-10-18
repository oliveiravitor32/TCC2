# Arquitetura atual, arquitetura proposta e validação para o mundo real

Levantamento de 18/10/2026, feito sobre:
- o código e o `docker-compose.prod.yml`;
- a v60 do texto (3.2, 3.5.2, 3.12.6.1 a 3.12.6.4 e Apêndice D);
- medições novas, feitas agora, do custo de cada decisão.

Os números de escala são **cálculo, não teste de carga**.

---

## 1. Arquitetura atual (protótipo implantado)

**Onde roda:** uma VM ARM da Oracle Cloud (camada gratuita) com Docker Compose. O painel fica fora dela.

| Componente | Tecnologia | Instâncias | Papel |
|---|---|---|---|
| Proxy HTTPS | Caddy 2 (DuckDNS, certificado automático) | 1 | Recebe a internet nas portas 80 e 443 e repassa à API |
| API de eventos | FastAPI + uvicorn, **1 processo** | 1 | `POST /eventos` com chave; consultas do painel |
| Serviço de decisão | Python, **1 processo**, laço único | 1 | Acorda por `pg_notify` a cada evento gravado; previsão XGBoost, Mamdani e verificação do piso; publica no MQTT; varredura a cada minuto |
| Broker | Mosquitto 2, TLS na porta 8883, CA própria, ACL por nó | 1 | Comando e telemetria |
| Banco | PostgreSQL 16 em contêiner, volume local | 1 | Cadastro, eventos, decisões, telemetria e auditoria |
| Painel | React estático na Vercel | (CDN) | Só leitura, com uma chave de demonstração pública |
| Nós | ESP32 físico (Wi-Fi, MQTT 3.1.1) + nó simulado | 2 | Rampa, validade (failsafe) e telemetria |

**Fluxo:** evento (REST) → gravado no banco → `pg_notify` → decisão para os pontos do trecho → comando MQTT, só quando o alvo muda ou o comando precisa ser renovado → nó faz a rampa → telemetria → banco → painel.

**Medido e adequado para a bancada:**
- latência de 1,03 s a 1,47 s;
- zero violações em 667.200 passos;
- failsafe ensaiado.

**Ponto único de falha em tudo:** uma VM, um processo de cada, sem réplica e com backup manual. Isso já está declarado em 5.3.

## 2. Arquitetura proposta (3.12.6.4 e Apêndice D)

| Camada | Proposta |
|---|---|
| Entrada | Kong (mTLS, limite de taxa, validação do Quadro 18) → **Kafka particionado por trecho** |
| Decisão | Réplicas sem estado, cada uma com algumas partições; estado (último comando, ocorrências, régua) no Redis; verificação do piso no processo **e repetida no adaptador** |
| Previsão | Treino periódico fora do caminho, com versões no MLflow |
| Atuação | Adaptador TALQ para o sistema central da concessionária; reenvio idempotente pelo `decisao_id`; telemetria elétrica no lugar do lux |
| Dados | RDS PostgreSQL Multi-AZ (cadastro, classes, versões **e decisões**); TimescaleDB em EC2 (eventos e telemetria); réplica de leitura para o painel |
| Operação | Kubernetes em 3 zonas, Vault/Secrets Manager, OpenTelemetry + Prometheus + Grafana |
| Custo | ~US$ 2.976/mês (AWS São Paulo, sob demanda) |

---

## 3. Validação contra o mundo real

### 3.1 Volume de dados: números de partida

| Grandeza | Valor | Fonte |
|---|---|---|
| Pontos de luz | 662.945 | GeoSampa (3.5.2) |
| Trechos de logradouro | 218.768 | GeoSampa (3.5.2) |
| Câmeras do Smart Sampa | ~50 mil | Quadro 1 |
| Pontos por trecho (raio de 25 m) | **5,1** | recorte real do Jardim Helena: 81 associações para 16 trechos e 35 postes |
| Trechos por ponto | **2,3** | mesmo recorte |
| Custo de CPU de uma decisão | **2,8 ms** (Mamdani 0,8 ms + XGBoost 2,0 ms) | medido hoje no código, 1 núcleo do notebook |

**Carga derivada:**

| Fluxo | Cobertura atual (50 mil câmeras ≈ 50 mil trechos) | Cobertura total (218.768 trechos) |
|---|---|---|
| Publicações de volume | ~170/s | ~730/s |
| **Decisões** (cada publicação decide os ~5 pontos do trecho) | **~850/s** | **~3.700/s** |
| Comandos (só na mudança ou na renovação) | ~1.000/s (3.5.2) | ~1.000/s |
| Telemetria (1 por comando) | ~1.000/s | ~1.000/s |
| Linhas de decisão por dia | ~73 milhões | **~320 milhões** |

**Entrada (170 a 730 publicações/s): ✅ condiz.** É carga pequena para um API gateway e para o Kafka, que suportam dezenas de milhares de mensagens por segundo num cluster de 3 brokers. O pacote de até 500 itens reduz ainda mais o número de requisições.

### 3.2 Pontos em que a proposta condiz com o mundo real ✅
- **Arquitetura orientada a eventos com fila durável:** padrão consolidado para ingestão em escala. Reter os eventos enquanto a decisão está fora do ar é o comportamento correto.
- **Réplicas sem estado + estado no Redis:** é o padrão para escalar horizontalmente.
- **Segurança fora do caminho da IA:** a verificação do piso no caminho do comando e repetida no adaptador é defesa em profundidade, coerente com sistemas críticos.
- **Degradação segura:** sem decisão, a validade vence e a luz vai ao pleno. Falha resulta em luz a mais, nunca a menos. Esse é o ponto mais forte da proposta para a confiabilidade.
- **Idempotência pelo `decisao_id`:** permite reentrega sem efeito duplicado. É requisito real de quem integra com sistemas de terceiros.
- **Redundância:** Multi-AZ no banco, Kafka com 3 réplicas e Redis com réplica eliminam o ponto único de falha da VM atual.
- **Observabilidade com correlação pelo `decisao_id`:** adequada, mas a API atual nem tem logs (ver o levantamento de logs).

### 3.3 Pontos em que a proposta, como está escrita, NÃO condiz ⚠️

**A. Decisões gravadas no banco relacional: não cabe.**
- Na cobertura total são ~320 milhões de decisões por dia, cada uma com o JSON das entradas e das ativações (~0,5 a 1 KB). Isso dá **~150 a 300 GB por dia**.
- O Apêndice D dimensiona o RDS com **100 GB**, que acabariam em horas.
- **Correção:**
  - tratar a decisão como série temporal, no TimescaleDB, com compressão e retenção, ao lado da telemetria;
  - gravar completa só a decisão que **muda o alvo ou gera comando** (~1.000/s);
  - guardar das demais apenas um resumo.
  - A auditabilidade continua, porque a decisão que manteve o alvo é reconstituível pelos eventos e pela versão da base (RNF04).

**B. Previsão feita a cada decisão: desperdício que muda o dimensionamento.**
- A previsão depende só do **histórico do trecho**, não do ponto. Hoje ela roda a cada decisão (2 ms × ~3.700/s ≈ 7,4 núcleos só para o XGBoost).
- Prevendo **uma vez por trecho a cada bloco de 15 min**, são 218.768 ÷ 900 s ≈ **243 previsões/s**, em lote vetorizado e muito mais barato.
- **Dimensionamento:** sem essa mudança, a cobertura total pede ~3.700 × 2,8 ms ≈ 10 núcleos só de cálculo. Com o custo de banco e de serialização, que costuma multiplicar por 2 ou 3, chega a **20 a 30 vCPU**.
  - Os 3 × m7g.xlarge do Apêndice D somam 12 vCPU e ainda dividem espaço com Kong, Keycloak, MLflow e Grafana. **Para a cobertura atual de 50 mil câmeras está adequado; para a cobertura total, não.**
- **Correção:**
  - previsão por trecho, em lote, gravada no Redis;
  - **agregar as decisões de um ponto numa janela curta** (o ponto recebe ~2,3 publicações a cada 5 min, então basta decidir uma vez por janela);
  - escalar as réplicas pela fila (autoscaling pelo atraso do Kafka).

**C. Partição do Kafka por trecho, mas a decisão é por ponto: condição de corrida.**
- Um ponto ligado a 2 ou 3 trechos pode cair em partições, e portanto em réplicas, diferentes. Duas réplicas podem decidir o mesmo ponto ao mesmo tempo e publicar comandos fora de ordem.
- **Correção:** dois estágios.
  1. O evento, particionado por trecho, atualiza o estado do trecho e gera um aviso "reavaliar ponto X" para cada ponto associado.
  2. Esse aviso vai para um segundo tópico **particionado por ponto**. Assim, cada ponto tem um único dono.

**D. Modelo de comando e renovação contra a rede real de telegestão: o ponto mais sério.**
- Telegestão em campo usa redes de baixa taxa (LoRaWAN, NB-IoT, malha RF, 6LoWPAN). Nessas redes, **mensagem de descida para a luminária é recurso escasso**: o gateway transmite um por vez e as janelas de recepção do controlador são curtas.
- **Renovação:** a proposta exige renovar o comando de cada uma das 662.945 luminárias a cada ~10 min só para manter a validade de 15 min. Isso dá ~1.000 mensagens/s de descida **permanentemente**, mesmo sem mudança de nível. Numa rede LPWAN, isso não é realista.
- **O próprio Caderno de Encargos** (citado em 3.5.2) prevê lógica e **agenda residentes no controlador**, que funciona sem comunicação, e comando **em grupo**.
- **Correção:**
  - **o failsafe de campo** deve ser "sem comando, volta à agenda residente ou ao pleno", com validade longa;
  - **a renovação** vira um sinal de vida por **grupo ou circuito**, e não por luminária;
  - **o comando individual** fica só para mudança de alvo;
  - **onde houver comando de grupo**, decidir por trecho ou circuito.
- O texto já declara em 5.3 que "a arquitetura de comando por mudança segue o Caderno e não o implantado", mas a 3.12.6.4 não trata a capacidade da rede de campo.

**E. Retomada após falha: pico de comandos.**
- Depois de uma queda maior que a validade, todo o parque vai ao pleno. Na volta, centenas de milhares de pontos mudam de alvo ao mesmo tempo. A ~1.000 comandos/s, levaria ~11 min para redistribuir, e a rede de campo talvez não aguente nem isso.
- **Correção:** retomada escalonada com limite de taxa no adaptador (contrapressão) e prioridade para os pontos com ocorrência. Ficar no pleno durante a retomada é seguro.

**F. Tempo e ordem dos eventos.**
- Plataformas diferentes têm relógios diferentes; o protótipo já precisou corrigir 1,3 s.
- Em escala, é preciso tratar evento atrasado ou fora de ordem: descartar o que já venceu e usar o horário do evento, não o da chegada.
- A proposta não menciona isso.

**G. Recuperação de desastre.**
- Tudo fica numa única região (São Paulo).
- Para o mundo real, faltam cópia dos backups em outra região e um tempo de recuperação declarado (RTO/RPO). Ainda assim, a falha total da região resulta no pleno, que é seguro.

**H. Custo.**
- Com as correções A a C, o custo muda:
  - mais armazenamento de série temporal;
  - mais CPU na cobertura total;
  - menos CPU com a previsão por trecho.
- Os ~US$ 3 mil/mês valem para a **cobertura atual de 50 mil câmeras**. Para a cobertura total, a ordem de grandeza provavelmente dobra ou triplica. Não foi recalculado.

### 3.4 Veredito

| Critério | A proposta condiz? |
|---|---|
| Tráfego de entrada | ✅ sim, com folga |
| Escalabilidade do processamento | ⚠️ sim na cobertura atual; na total, só com previsão por trecho, agregação por ponto e mais CPU (B) |
| Armazenamento | ❌ não, como escrito: as decisões no RDS de 100 GB não cabem (A) |
| Consistência | ⚠️ falta o estágio por ponto para evitar corrida (C) |
| Controle de falhas | ✅ forte na segurança (pleno); ⚠️ falta a retomada escalonada (E) e o DR (G) |
| Confiabilidade da atuação em campo | ❌ a renovação por luminária não cabe nas redes de telegestão; deve virar agenda residente + comando de grupo (D) |

**Resumo:** a **direção** da arquitetura é a do mundo real: eventos, réplicas, segurança fora da IA, idempotência e degradação para o pleno. Porém **três pontos do texto, como estão escritos, não se sustentam** em escala de cidade: o armazenamento das decisões, a corrida entre trechos e pontos, e o modelo de renovação por luminária na rede de campo. Há também ajustes de dimensionamento e de custo. Nada disso afeta os resultados do trabalho, que são de bancada e de simulação. Afeta só a seção de proposta (3.12.6.4) e o Apêndice D.

## 4. O que mudar no texto (se os autores aprovarem)
1. **3.12.6.4 "Dados em dois níveis":** decisões que mudam o alvo vão completas para a série temporal; as demais, resumidas.
2. **3.12.6.4 "Serviço de decisão replicado":** previsão por trecho a cada 15 min em lote; segundo estágio particionado por ponto; agregação por ponto numa janela curta.
3. **3.12.6.4 "Adaptador de telegestão":** comando individual só na mudança; renovação por grupo; failsafe de campo como agenda residente; retomada escalonada com limite de taxa.
4. **3.12.6.4:** uma frase sobre eventos atrasados e sobre DR em outra região.
5. **Apêndice D:** declarar que o custo vale para a cobertura atual (~50 mil câmeras) e que a cobertura total exige redimensionar.
6. **5.3:** limitação sobre a capacidade de descida das redes de telegestão, não avaliada.
