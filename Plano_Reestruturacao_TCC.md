# Plano de Reestruturação do TCC
## Da "Microgrid Urbana" para "Análise e Previsão de Consumo Energético Residencial com IoT e IA"

**Universidade Paulista – UNIP | Ciência da Computação – 7º Semestre**
Documento de apoio interno (não é entregável — é o mapa de como refazer os entregáveis)

---

## 1. Diagnóstico: o que realmente estava errado

A troca de tema está certa, mas é importante entender que o tema **não era o único problema**. Ao cruzar os documentos produzidos (`Pré-projeto`, `Revisão Bibliográfica`, `Metodologia`) com o documento de orientação da instituição, aparecem quatro falhas que teriam derrubado o projeto **mesmo que a microgrid tivesse dado certo**:

| # | Falha | Onde aparece | Gravidade |
|---|-------|--------------|-----------|
| 1 | **Nuvem ausente** | A orientação exige, em "Requisitos Comuns a Ambos os Vieses", *"Utilizar computação em nuvem de forma funcional"*. A Metodologia fala genericamente em "servidor", sem nomear provedor, serviço ou justificativa. O entregável de TC2 é literalmente *"Protótipo funcional integrado à nuvem"*. | **Crítica** — requisito obrigatório não atendido |
| 2 | **IA subdimensionada** | A Metodologia (seção 4) define **regressão linear** como técnica de IA. Isso é fraco para um TCC de Ciência da Computação e contradiz a própria Revisão Bibliográfica do grupo, que já citava LSTM e Deep Learning (Goodfellow et al.) como estado da arte. | **Alta** — o avaliador vai cobrar |
| 3 | **Sensor incompatível com o objeto real** | INA219 mede **corrente contínua de baixa potência** (barramento até 26 V DC). Rede residencial brasileira é **127/220 V em corrente alternada**. O sensor escolhido não mede aquilo que o trabalho diz medir. | **Crítica** — inviabiliza o protótipo |
| 4 | **Banco de dados raso** | A orientação exige *"arquitetura de banco de dados robusta"*. O modelo entregue tem duas tabelas (`residencias`, `leituras`) sem índice temporal, sem catálogo de aparelhos, sem tabela de previsões, sem separação entre leitura bruta e agregada. | **Média-alta** |

**Conclusão do diagnóstico:** o novo tema resolve o problema regulatório e de segurança, mas as falhas 1, 2 e 4 são independentes do tema e precisam ser corrigidas de qualquer forma. A falha 3 se resolve na nova escolha de hardware.

---

## 2. O novo tema é viável? Sim — e por motivos estruturais, não por ser "mais fácil"

A diferença essencial entre os dois temas:

> **Microgrid = sistema de ATUAÇÃO.** Você interfere no fluxo de energia. Isso exige inversor, proteção, aterramento, conformidade com PRODIST/ANEEL (Res. Normativa 1.059/2023 para geração distribuída), e assume risco elétrico real. Um grupo de graduação não tem como validar isso em bancada com segurança nem com respaldo legal.
>
> **Previsão de consumo = sistema de OBSERVAÇÃO E INFERÊNCIA.** Você mede e prevê. Não injeta energia, não comuta carga, não altera a instalação. Zero exposição regulatória. O risco elétrico é eliminado pela escolha de sensor não-invasivo.

**Enquadramento institucional:** a orientação restringe o domínio a *Cidades Inteligentes ou Fazendas Inteligentes*. Consumo residencial **se enquadra em Cidades Inteligentes** sem forçar a barra — mas isso precisa estar explícito no Capítulo 1. O argumento a usar: eficiência energética no setor residencial é um dos pilares de cidade inteligente, e a residência é a menor unidade da rede urbana. O setor residencial responde por parcela relevante do consumo nacional de eletricidade (verificar o número atualizado no Anuário Estatístico de Energia Elétrica da EPE antes de citar). Medição inteligente residencial é pré-condição para qualquer política de eficiência em escala urbana.

**Título proposto:**

> *Sistema de Monitoramento e Previsão de Consumo Energético Residencial baseado em Internet das Coisas, Computação em Nuvem e Aprendizado de Máquina*

Mantém IoT + IA, adiciona explicitamente a nuvem (que é requisito), e o escopo é honesto sobre o que o sistema faz.

**Problema de pesquisa proposto:**

> *Como a integração entre sensoriamento IoT não-invasivo, computação em nuvem e modelos de aprendizado de máquina em séries temporais pode fornecer previsão confiável de consumo energético residencial de curto prazo, com hardware de baixo custo?*

---

## 3. Mapa de reaproveitamento — o que salvar, adaptar e descartar

### 3.1 Revisão Bibliográfica (`Revisao_Bibliografica.docx`)

Este é o documento **mais aproveitável dos três**. Estimativa: ~55% reaproveitado.

| Seção atual | Destino |
|---|---|
| 1. Evolução histórica das redes elétricas | **Manter, encurtar para ~1 parágrafo.** Vira contextualização. |
| 2. Smart Grids e cidades inteligentes | **Manter, reposicionar.** É a ponte que justifica o enquadramento em Cidades Inteligentes. Ganha importância. |
| 3. Microgrids urbanas: estado da arte | **Reduzir drasticamente** a 1 parágrafo de contexto, ou remover. Lasseter e Olivares saem do núcleo. |
| 4. IoT em sistemas energéticos | **Manter quase integral.** Atzori et al. e o modelo de 3 camadas (percepção/rede/aplicação) continuam sendo a espinha dorsal. |
| 5. IA aplicada à gestão energética | **Manter e EXPANDIR.** O parágrafo sobre LSTM em séries temporais deixa de ser nota de rodapé e vira o centro do trabalho. |
| 6. Sistemas multi-agente | **Remover.** Não há mais múltiplos agentes negociando. Wooldridge sai. |
| 7. Comparativo de hardware (ESP32) | **Manter.** A justificativa do ESP32 permanece válida e bem construída. |
| 7.1 Comparativo de sensores | **REFAZER.** O INA219 é substituído (ver seção 5). O formato do quadro comparativo se aproveita; o conteúdo, não. |
| 8. Trabalhos relacionados e lacunas | **Reescrever.** A lacuna deixa de ser "falta protótipo físico de microgrid" e passa a ser sobre previsão residencial. |
| 9. Hipóteses | **Reescrever** (ver 3.4). |
| 10. Referências | Manter Atzori, Farhangi, Russell & Norvig, Goodfellow. Remover Lasseter, Olivares, Wooldridge, Mohassen, datasheet INA219. |

### 3.2 Seções NOVAS obrigatórias na Revisão Bibliográfica

O trabalho não se sustenta academicamente sem literatura específica de *load forecasting* residencial. Referências a buscar e ler (via Google Scholar / IEEE Xplore / Portal de Periódicos CAPES — o acesso institucional da UNIP cobre parte disso):

- **HART, G. W.** *Nonintrusive appliance load monitoring.* Proceedings of the IEEE, v. 80, n. 12, 1992. — Artigo fundador de NILM. Citação obrigatória se vocês forem desagregar por aparelho.
- **KELLY, J.; KNOTTENBELT, W.** *Neural NILM: Deep neural networks applied to energy disaggregation.* ACM BuildSys, 2015.
- **KONG, W. et al.** *Short-term residential load forecasting based on LSTM recurrent neural network.* IEEE Transactions on Smart Grid, v. 10, n. 1, 2019. — **Esta é a referência central do novo trabalho.**
- **HOCHREITER, S.; SCHMIDHUBER, J.** *Long Short-Term Memory.* Neural Computation, v. 9, n. 8, 1997.
- **HYNDMAN, R.; ATHANASOPOULOS, G.** *Forecasting: Principles and Practice.* 3. ed. OTexts, 2021. — Base metodológica para baselines, validação temporal e métricas. Disponível gratuitamente online.
- **KELLY, J.; KNOTTENBELT, W.** *The UK-DALE dataset.* Scientific Data, v. 2, 2015. — Dataset público.
- Um levantamento nacional: buscar artigos brasileiros sobre previsão de carga residencial (SBSE, CBA, revistas da SBA) para ancorar no contexto do país.

> **Atenção:** confiram cada referência na fonte original antes de citar. Não citem nada que o grupo não tenha aberto — inclusive as acima. A referência "MOHASSEN et al." que consta no documento atual, por exemplo, tem indícios de estar com autoria incorreta; vale reverificar todas as antigas também.

### 3.3 Metodologia (`Metodologia.pdf`)

Estimativa: ~40% da **estrutura** aproveitável, com conteúdo substituído.

| Seção | Ação |
|---|---|
| 1. Classificação da pesquisa | **Manter estrutura.** Continua aplicada, quantitativa, experimental. Trocar "gerenciamento" por "monitoramento e previsão". |
| 2. Método de coleta de dados | **Reescrever.** Muda o sensor, muda o cenário (residência real em vez de microgrid simulada), muda a janela (precisa de semanas de coleta, não minutos). |
| 3. Justificativa da metodologia | **Reescrever.** A justificativa nova é: dados reais de uma residência + dataset público para robustez estatística. |
| 4. Aplicação da IA | **REESCREVER POR COMPLETO.** Regressão linear vira *baseline*, não solução. Ver seção 6. |
| 5.1–5.5 (requisitos) | **Adaptar.** Boa parte dos requisitos funcionais/não-funcionais sobrevive com ajuste. Remover "gerenciar distribuição de energia" e "identificar excedentes". Adicionar requisitos de nuvem e de previsão. |
| 5.6 Processo incremental | **Manter.** Escolha adequada, justificativa válida. |
| 5.7–5.10 Arquitetura e diagramas | **Refazer** com a arquitetura da seção 7 deste plano. Os diagramas precisam existir como imagem, não só como descrição textual — o documento atual descreve diagramas em prosa, o que não cumpre a exigência. |
| 5.12 Casos de teste | **Expandir muito.** A tabela atual tem 3 linhas e todas com resultado "Sucesso" já preenchido antes dos testes existirem. Isso é frágil. Ver seção 9. |
| 5.13 Cronograma | **Refazer** com datas reais restantes. |
| 6. Banco de dados | **Refazer** — ver seção 8. |

### 3.4 Novas hipóteses

Substituem H1–H4:

- **H1:** Um nó IoT de baixo custo (ESP32 + sensor não-invasivo) coleta dados de consumo residencial com erro aceitável frente a um medidor de referência (erro relativo < 5%).
- **H2:** Um modelo LSTM treinado sobre a série histórica coletada prevê o consumo agregado das próximas 24 horas com erro (MAPE) inferior ao de baselines estatísticos clássicos (persistência sazonal e regressão linear).
- **H3:** A arquitetura em nuvem proposta sustenta ingestão contínua de telemetria e inferência sob demanda dentro dos limites de custo de uma camada gratuita/mínima de provedor público.
- **H4:** A disponibilização das previsões ao usuário final em interface web permite identificar padrões de consumo acionáveis (picos, cargas dominantes, projeção de custo tarifário).

H1, H2 e H4 são **evolução direta** das hipóteses antigas — não é trabalho jogado fora. H3 é nova e existe para cobrir o requisito de nuvem.

---

## 4. Enquadramento: viés científico ou de mercado?

A orientação obriga a escolher um. **Recomendação: viés científico.**

Motivo: o grupo já tem uma revisão bibliográfica construída, e o viés científico avalia por *"benchmarks, métricas de desempenho ou análise comparativa"* — que é exatamente o que uma comparação LSTM vs. baselines produz naturalmente. O viés de mercado exigiria pesquisa de público-alvo, entrevistas e análise de concorrência, que é trabalho novo e do zero.

Isso deve ser declarado explicitamente na Introdução.

---

## 5. Protótipo físico — projeto e lista de materiais

### 5.1 A troca de sensor (ponto mais importante da parte física)

| Opção | Mede | Isolamento | Custo aprox. | Veredito |
|---|---|---|---|---|
| INA219 (atual) | Corrente DC ≤ 3,2 A, ≤ 26 V | Não isolado | Baixo | **Inadequado** — não mede rede AC 127/220 V |
| **SCT-013-030 / SCT-013-000** | Corrente AC, não-invasivo (garra) | Isolamento magnético total — não toca o condutor | Baixo | **Recomendado** — seguro, padrão em TCC |
| **PZEM-004T v3.0** | Tensão, corrente, potência, energia, FP, frequência | Comunicação serial isolada; requer conexão à rede | Baixo-médio | **Recomendado como complemento** — entrega grandezas já calculadas |
| Medidor comercial com API | Tudo | Total | Médio-alto | Alternativa se o grupo não quiser montar hardware |

**Arquitetura de hardware recomendada (segura e defensável):**

- **Nó principal (medição total da residência):** ESP32 + SCT-013-030 no condutor fase do quadro de distribuição, com o circuito de condicionamento (burden resistor + divisor de tensão com offset DC, capacitor de desacoplamento). A garra **abraça o fio pelo lado de fora do isolamento** — não há corte, emenda ou contato elétrico.
- **Nós secundários (2 a 3 cargas individuais):** ESP32 + SCT-013 em extensões/réguas dedicadas para geladeira, ar-condicionado e chuveiro ou micro-ondas. Alternativamente, use PZEM-004T nesses pontos para ter potência real e fator de potência.
- **Tensão:** para calcular potência real (não apenas aparente) é preciso amostrar tensão. O PZEM resolve isso; se usar só SCT-013, assuma tensão nominal e **declare essa simplificação como limitação do trabalho** — isso é honestidade metodológica e conta a favor.

### 5.2 Lista de materiais estimada

| Item | Qtd | Faixa de preço |
|---|---|---|
| ESP32 DevKit V1 | 3 | R$ 35–60 cada |
| SCT-013-030 (garra 30 A) | 3 | R$ 45–80 cada |
| PZEM-004T v3.0 + bobina | 1 | R$ 60–110 |
| Componentes de condicionamento (resistores, capacitores, protoboard, jumpers) | — | R$ 40–70 |
| Fontes 5 V / cabos USB | 3 | R$ 20–35 cada |
| Caixa/estrutura de apresentação | 1 | R$ 50–120 |

**Total estimado: R$ 450 a R$ 800.** Verifiquem os preços atuais antes de colocar no documento — a tabela de custo é um bom elemento para a seção de viabilidade.

### 5.3 Segurança — inegociável

- Toda instalação em quadro de distribuição deve ser feita ou supervisionada por um eletricista, ou substituída por medição em **extensão/régua** montada em bancada.
- Nunca energizar protoboard com 127/220 V.
- Se algum membro do grupo tiver receio da parte elétrica: **use só o SCT-013 em réguas de tomada com cargas conhecidas** (chaleira, secador, notebook, lâmpada). Isso é suficiente para validar H1 e não exige mexer na instalação da casa.

### 5.4 O que apresentar na banca

Uma maquete de bancada: uma régua de tomadas com 2–3 cargas visíveis (lâmpada, ventilador, carregador), os nós ESP32 com as garras instaladas, e um notebook/tablet mostrando o dashboard em nuvem atualizando ao vivo enquanto se liga e desliga uma carga. **Esse momento — ligar o ventilador e a linha do gráfico subir na tela em tempo real — é o que convence a banca.** É simples, é dramático, e é infinitamente mais viável que uma microgrid.

---

## 6. A camada de Inteligência Artificial

### 6.1 Estratégia de modelagem

Regressão linear **não sai do trabalho** — ela é rebaixada de solução para **baseline de comparação**, que é o papel correto dela. A comparação entre modelos é o que gera os resultados analisáveis exigidos pelo viés científico.

**Modelos a implementar, em ordem:**

1. **Baseline ingênuo (persistência sazonal):** a previsão para a hora *h* de amanhã é o consumo da hora *h* de hoje. Custa 5 linhas de código e é surpreendentemente difícil de superar. Obrigatório.
2. **Regressão linear / Ridge** com features de calendário (hora do dia, dia da semana, fim de semana) e defasagens (lags de 1h, 24h, 168h). Baseline estatístico.
3. **LSTM** (Keras/TensorFlow ou PyTorch) sobre janela deslizante — o modelo principal, alinhado à literatura (Kong et al., 2019).
4. **Opcional, se sobrar tempo:** XGBoost sobre as mesmas features. Frequentemente vence LSTM em séries curtas, e esse achado seria um resultado interessante para a Análise de Resultados.

### 6.2 Métricas

MAE, RMSE e MAPE. Reportar as três. Usar **validação temporal** (`TimeSeriesSplit`) — nunca embaralhar os dados, é o erro mais comum e mais fatal em séries temporais.

### 6.3 O problema do volume de dados (leiam com atenção)

Uma LSTM não aprende sazonalidade semanal com três dias de coleta. Vocês precisam de **no mínimo 4 a 8 semanas** de série contínua para ter algo defensável. Duas providências:

- **Comecem a coletar o quanto antes**, mesmo com o código do dashboard incompleto. Um ESP32 gravando em banco é a primeira coisa a subir. Cada dia de atraso é um dia de dado perdido que não se recupera.
- **Usem um dataset público em paralelo** (UK-DALE, REDD, AMPds2, ou o "Individual Household Electric Power Consumption" do UCI, que tem ~4 anos de dados de uma residência). Treinem e validem o modelo neles enquanto a coleta própria acumula. Isso é prática aceita e citável, e a própria orientação prevê *"coleta de dados via sensores IoT e bases públicas"* — está literalmente autorizado no documento da instituição.

---

## 7. Arquitetura do sistema (com a nuvem que faltava)

```
CAMADA DE PERCEPÇÃO (física, na residência)
  ESP32 #1 ── SCT-013 ──> quadro geral / entrada
  ESP32 #2 ── SCT-013 ──> carga A (ex.: geladeira)
  ESP32 #3 ── PZEM-004T ─> carga B (ex.: ar-condicionado)
        │
        │  firmware C++/Arduino: amostragem, cálculo RMS,
        │  buffer local, timestamp via NTP
        ▼
CAMADA DE REDE
  Wi-Fi 802.11 → MQTT sobre TLS (tópico por dispositivo)
        ▼
CAMADA DE NUVEM  ◄── requisito institucional obrigatório
  ├─ Broker MQTT gerenciado (HiveMQ Cloud free tier, AWS IoT Core,
  │  ou Mosquitto em VM — mas prefira serviço gerenciado, é mais
  │  defensável como "nuvem funcional")
  ├─ Serviço de ingestão (API REST em FastAPI/Node, containerizada)
  ├─ Banco de dados (PostgreSQL gerenciado — Supabase/Neon/RDS —
  │  ou InfluxDB Cloud para séries temporais)
  ├─ Serviço de previsão (job agendado: retreino periódico +
  │  endpoint de inferência sob demanda)
  └─ Armazenamento de modelos treinados (bucket de objetos)
        ▼
CAMADA DE APRESENTAÇÃO
  Aplicação web (React ou Next.js) hospedada em nuvem:
  ├─ consumo em tempo real
  ├─ histórico (dia / semana / mês)
  ├─ previsão das próximas 24 h com banda de incerteza
  ├─ ranking de cargas monitoradas
  └─ estimativa de custo na tarifa vigente (incluir bandeira tarifária)
```

**Sobre custo de nuvem:** tudo isso cabe em camadas gratuitas ou de poucos reais por mês (HiveMQ free, Supabase free, Vercel/Render free, Hugging Face Spaces ou Render para o serviço de inferência). Documentem essa escolha — "arquitetura de custo zero em camada gratuita" é uma justificativa arquitetural legítima e vocês serão perguntados sobre isso.

**Diagramas a produzir** (a orientação cobra artefatos, e o documento atual só os descreve em texto):

1. Diagrama de arquitetura em camadas (o esquema acima, desenhado)
2. Diagrama de implantação (deployment) — o que roda onde
3. Diagrama de casos de uso — atores: Morador, Administrador, Serviço de Previsão
4. Diagrama de atividades — fluxo da leitura até a exibição da previsão
5. Diagrama de sequência — ciclo completo de uma medição
6. DER do banco

Ferramentas: draw.io, Mermaid, PlantUML ou Astah. Exportem em boa resolução.

---

## 8. Arquitetura do banco de dados (reforçada)

O modelo de duas tabelas não atende "robusta". Proposta:

```sql
CREATE TABLE residencia (
  id              SERIAL PRIMARY KEY,
  nome            VARCHAR(80) NOT NULL,
  num_moradores   SMALLINT,
  area_m2         NUMERIC(6,2),
  tipo_tarifa     VARCHAR(30),
  criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dispositivo (
  id              SERIAL PRIMARY KEY,
  residencia_id   INT NOT NULL REFERENCES residencia(id),
  identificador   VARCHAR(60) UNIQUE NOT NULL,   -- MAC / device id
  tipo_sensor     VARCHAR(30) NOT NULL,          -- SCT013 | PZEM004T
  ponto_medicao   VARCHAR(60) NOT NULL,          -- 'quadro_geral' | 'geladeira'
  ativo           BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE leitura (
  id              BIGSERIAL PRIMARY KEY,
  dispositivo_id  INT NOT NULL REFERENCES dispositivo(id),
  medido_em       TIMESTAMPTZ NOT NULL,
  tensao_v        NUMERIC(6,2),
  corrente_a      NUMERIC(8,3),
  potencia_w      NUMERIC(10,2) NOT NULL,
  fator_potencia  NUMERIC(4,3),
  energia_wh      NUMERIC(12,3),
  qualidade       SMALLINT NOT NULL DEFAULT 0    -- flag de dado suspeito
);
CREATE INDEX idx_leitura_disp_tempo ON leitura (dispositivo_id, medido_em DESC);

-- Agregação horária: a série que alimenta o modelo
CREATE TABLE consumo_horario (
  residencia_id   INT NOT NULL REFERENCES residencia(id),
  hora            TIMESTAMPTZ NOT NULL,
  energia_wh      NUMERIC(12,3) NOT NULL,
  potencia_media_w NUMERIC(10,2),
  potencia_pico_w  NUMERIC(10,2),
  n_amostras      INT NOT NULL,
  PRIMARY KEY (residencia_id, hora)
);

CREATE TABLE modelo_treinado (
  id              SERIAL PRIMARY KEY,
  algoritmo       VARCHAR(40) NOT NULL,          -- baseline | ridge | lstm | xgboost
  versao          VARCHAR(20) NOT NULL,
  treinado_em     TIMESTAMPTZ NOT NULL,
  janela_treino_inicio TIMESTAMPTZ,
  janela_treino_fim    TIMESTAMPTZ,
  mae NUMERIC(10,4), rmse NUMERIC(10,4), mape NUMERIC(6,3),
  caminho_artefato TEXT
);

CREATE TABLE previsao (
  id              BIGSERIAL PRIMARY KEY,
  residencia_id   INT NOT NULL REFERENCES residencia(id),
  modelo_id       INT NOT NULL REFERENCES modelo_treinado(id),
  gerada_em       TIMESTAMPTZ NOT NULL,
  hora_alvo       TIMESTAMPTZ NOT NULL,
  energia_prevista_wh NUMERIC(12,3) NOT NULL,
  limite_inferior_wh  NUMERIC(12,3),
  limite_superior_wh  NUMERIC(12,3)
);
CREATE INDEX idx_previsao_alvo ON previsao (residencia_id, hora_alvo);
```

**Por que isso é "robusto" e a versão anterior não era:**

- Separa **dispositivo** de **residência** — permite múltiplos pontos de medição, que é o coração do trabalho.
- Separa **leitura bruta** de **agregado horário** — padrão de arquitetura de dados de série temporal, e é o agregado que alimenta o modelo.
- Persiste **previsões e métricas de modelo**, permitindo comparar previsão × realizado *a posteriori*. Isso gera dados diretamente para o capítulo de Resultados.
- Tem **índices explícitos** e justificados pelo padrão de consulta.
- Tem **flag de qualidade** para tratar leituras espúrias — mostra maturidade de engenharia de dados.

Guardem essas justificativas: a orientação pede explicitamente *"explicando a aplicação e utilização dela pelo sistema"*.

---

## 9. Plano de testes

A tabela de 3 linhas com "Sucesso" pré-preenchido precisa virar uma matriz real, e o resultado só se preenche **depois** de executar.

| ID | Tipo | Cenário | Critério de aceite |
|---|---|---|---|
| T01 | Unidade | Cálculo de corrente RMS a partir da amostragem | Erro < 2% vs. valor calculado manualmente |
| T02 | Integração | Publicação MQTT do ESP32 até persistência no banco | Registro presente com timestamp correto |
| T03 | Acurácia HW | Carga conhecida (lâmpada 100 W) medida pelo nó | Erro relativo < 5% vs. potência nominal / medidor de referência |
| T04 | Resiliência | Queda de Wi-Fi por 10 min | Buffer local retém dados e reenvia ao reconectar; zero lacuna |
| T05 | Carga | 3 nós publicando a cada 5 s por 24 h | Sem perda de mensagens; latência p95 < 3 s |
| T06 | ML | LSTM vs. baseline de persistência no conjunto de teste | MAPE do LSTM inferior ao do baseline |
| T07 | ML | Validação temporal sem vazamento de dados | Nenhum dado futuro no treino (auditoria do split) |
| T08 | Sistema | Previsão de 24 h exibida no dashboard | Renderiza em < 2 s com dados atualizados |
| T09 | Integridade | Inserção de leitura com dispositivo inexistente | Rejeitada por chave estrangeira |
| T10 | Usabilidade | Usuário leigo identifica o horário de pico | Tarefa concluída sem instrução prévia |

---

## 10. Sequência de trabalho recomendada

A ordem importa, porque há uma dependência crítica de tempo (a coleta de dados).

**Fase 0 — imediata, esta semana**
1. Confirmar a troca de tema com o **Prof. Marco Gomes** antes de reescrever qualquer linha. Levem este raciocínio: o tema anterior tinha impedimento regulatório e de segurança inviável para graduação; o novo preserva IoT + IA + nuvem e cabe em Cidades Inteligentes.
2. Comprar o hardware. É o item de maior lead time.

**Fase 1 — coleta começa cedo (prioridade absoluta)**
3. Montar UM nó (ESP32 + SCT-013) e validar contra uma carga conhecida.
4. Subir banco em nuvem + ingestão mínima. Não precisa estar bonito, precisa estar gravando.
5. **Ligar e deixar coletando.** A partir daqui o relógio dos dados está correndo a favor de vocês.

**Fase 2 — em paralelo à coleta**
6. Reescrever Pré-projeto e Revisão Bibliográfica (aproveitando o mapa da seção 3).
7. Refazer a Metodologia com a nova arquitetura, diagramas e DER.
8. Desenvolver os modelos usando dataset público enquanto os dados próprios acumulam.

**Fase 3 — consolidação**
9. Adicionar os nós 2 e 3.
10. Retreinar os modelos com os dados reais coletados; rodar a comparação.
11. Construir o dashboard.
12. Executar a matriz de testes e registrar resultados reais.
13. Escrever Resultados, Análise e Conclusões.

---

## 11. Limitações a declarar (isso protege vocês na banca)

Declarar limitação não é fraqueza — é rigor metodológico, e a orientação tem seção específica para isso. Declarem:

- Amostra de **uma única residência**, sem generalização estatística para outros perfis domiciliares.
- Janela de coleta limitada ao período do TCC; sazonalidade anual não capturada.
- Se usarem só SCT-013: tensão assumida como nominal, portanto potência aparente e não real.
- Sensores de baixo custo sem calibração laboratorial rastreável.
- Desagregação por aparelho limitada aos pontos instrumentados (não é NILM completo, é submedição direta).
- Dependência de conectividade Wi-Fi residencial.

---

## 12. Resposta direta às suas três perguntas

**"Esse novo tema é viável e simples de implementar fisicamente?"**
Sim. É a diferença entre medir e controlar. Medir com garra não-invasiva não exige alteração da instalação elétrica, não tem risco regulatório e monta em bancada. O item de maior risco não é o hardware — é o **tempo de coleta de dados**, e por isso ele é a primeira coisa a começar.

**"E a arquitetura para a documentação?"**
Também sim, e na verdade fica *mais fácil* de documentar que a microgrid, porque o fluxo é linear (sensor → nuvem → modelo → tela) em vez de bidirecional com negociação entre agentes. As seções 7 e 8 deste plano já são o esqueleto pronto dos capítulos "Arquitetura do Sistema", "Arquitetura da Infraestrutura" e "Arquitetura do Banco de Dados".

**"Vou reaproveitar alguma coisa do antigo projeto?"**
Bastante. Grosso modo: ~55% da Revisão Bibliográfica, ~40% da estrutura da Metodologia, a escolha do ESP32 com sua justificativa, o modelo de camadas IoT, o processo incremental, e três das quatro hipóteses em versão evoluída. O que morre de fato: microgrid como objeto, sistemas multi-agente, o sensor INA219 e a regressão linear como solução principal (ela vira baseline).

---

## 13. Ponto de atenção final

Reparei que o `Pré-projeto.pdf` lista **três** integrantes e os demais documentos listam **quatro** (Lucas de Araujo Vergara aparece na Metodologia e na Revisão, mas não no Pré-projeto). Verifiquem e padronizem a autoria em todos os entregáveis antes da submissão final.
