# Preparação para a banca por integrante (v81)

Cada um responde pela sua área (divisão da 3.12.2). Para cada área há três blocos:

- **o que dominar**;
- **números de cabeça**;
- **perguntas específicas com resposta curta**.

As perguntas gerais estão em `ROTEIRO_RESPOSTAS_BANCA.md`, e os ataques, em `LEVANTAMENTO_ATAQUES_BANCA.md`.

---

## Vitor: borda e infraestrutura
Nó, firmware, comunicação segura, nuvem e banco.

### O que dominar (seções)
- **3.4 a 3.4.5:** nó, bancada, calibração e diagnóstico.
- **3.12.6.1 e 3.12.6.2:** implantação em nuvem e contratos.
- **3.12.6.4 e Apêndices D e F:** arquitetura de escala, custo e particionamento.
- **3.13:** banco.
- **3.12.9 e 4.3:** CT15–CT20 e latência.
- **Código:**
  - `firmware/no/no.ino`: rampa, failsafe e tabela de calibração;
  - `decisao/verificacao.py`;
  - `db/schema.sql`;
  - `docker-compose.prod.yml`;
  - `broker/`: TLS e ACL.

### Números de cabeça
- **PWM:** 5 kHz e 12 bits (4.096 degraus).
- **Calibração (sessão 113, texto):**
  - 10 lux = 65,6 % do duty e 5 lux = 34,0 %;
  - teto de 1,57 vez a classe;
  - tolerância do diagnóstico de 3,4 %.
- **Calibração vigente no nó:** sessão 115.
- **Fita e caixa:**
  - fita: 3 emissores, 6 cm, 0,86 W;
  - caixa de 43,7 × 31 × 24 cm;
  - sensor a 0,437 m da fita.
- **Rampa:** 0,008 a cada 5 s (≈ 0,1 por minuto); de P3 a P5 leva 5 min 15 s.
- **Latência:** 30 repetições de 1,03 a 1,47 s, mediana 1,25 s; o limite é 180 s.
- **Failsafe:** pleno no vencimento da validade (no máximo 15 min); o sensor registrou o pleno 2,3 s depois.
- **Alertas:** falha total após 3 leituras; perda de controle após 12.
- **Custo da arquitetura de escala:** ~US$ 2.976 por mês na AWS São Paulo.

### Perguntas específicas
- **Por que ESP32 e não Raspberry Pi?**
  - O nó não pode decidir: a decisão fica na nuvem.
  - O ESP32 tem PWM em hardware e Wi-Fi nativo.
  - Também pesam o custo e a falta de sistema de arquivos para corromper.
- **PWM não é 0–10 V, que o contrato pede.**
  - É só a interface elétrica. Um filtro passa-baixas com seguidor de tensão converte uma na outra.
  - O serviço manda um nível adimensional; quem converte é o nó.
- **Como garante que não desce rápido demais?**
  - O nó faz a rampa com arredondamento para baixo.
  - Ele recebe o piso e a taxa no comando: é uma segunda barreira, além do serviço.
- **E se a internet cair?** Vencida a validade, o nó vai ao pleno (RNF07). Falha do sistema vira luz a mais, nunca escuridão.
- **Por que validade e não um "heartbeat" a cada 5 s?**
  - Comando a cada 5 s, no parque, seriam ~120 mil comandos por segundo.
  - Com comando só na mudança e validade, cai para ~1.000.
- **Como é a segurança do MQTT?**
  - TLS 1.3 com CA própria gravada no firmware.
  - Senha por dispositivo e ACL: cada nó só lê o próprio comando e só publica a própria telemetria.
  - Sem credencial, a conexão é recusada (CT19).
- **Por que QoS 1 sem retain?**
  - QoS 1 entrega ao menos uma vez.
  - Sem retain, o nó que reconecta não aplica decisão velha.
  - Mensagem duplicada é absorvida pelo `decisao_id`.
- **Por que banco relacional?**
  - A auditoria é feita por junção: decisão → classe → piso vigente.
  - A integridade referencial impede decisão sem ponto, sem classe ou sem versão.
- **Por que VM e não PaaS?** O serviço de decisão é um processo sempre ligado, com conexão contínua ao broker. A camada gratuita dá conta de 1 nó.
- **Qual o ponto único de falha?** A VM. Está declarado em 5.3; em escala, a solução está na 3.12.6.4 (Kafka, réplicas, Kubernetes e várias zonas).
- **O sensor não é calibrado.**
  - Não afirmamos lux absoluto.
  - O que vale é a razão: erro de escala constante se cancela.
  - Há repetibilidade (0,86 %) e estabilidade (0,2 %).
- **O que o particionamento resolve?** Tabelas que crescem com o tempo. Apagar um mês vira operação de catálogo, e a consulta de um dia lê só a partição daquele dia.

### Demonstração ao vivo (ensaiar)
1. Mostrar no terminal que a verificação corrige um pedido abaixo do piso:

   ```bash
   .venv/Scripts/python.exe -m pytest tests/test_verificacao.py -v
   ```

2. Publicar uma ocorrência no painel e mostrar a luz subindo na hora.
3. Depois, publicar volume 0 e mostrar a descida em rampa.

---

## Lucas: módulo de inteligência
Previsão, inferência nebulosa e métricas.

### O que dominar (seções)
- **2.6 e 2.7:** por que fuzzy e por que XGBoost.
- **3.6:** previsão, série de Zurique, régua p99 e protocolo.
- **3.7:** variáveis, tercis, trapézios, as 7 regras e os degraus.
- **3.9:** avaliação, H3, substitutos e percepção.
- **4.1 e 4.6:** Tabelas 3 e 4.
- **5.1 e 5.2:** hipóteses.
- **Apêndice G:** Quadro 22 e Figura 14.
- **Código:**
  - `decisao/inferencia.py`;
  - `decisao/previsao.py`;
  - `decisao/regras/v6-zurique.toml`;
  - `modelo/treinar_zurique.py`;
  - `cenarios/`.

### Números de cabeça
- **Tercis:** 0,0693 e 0,2946; meia largura da rampa do trapézio de 0,017. À noite, 56 % dos blocos ficam na faixa baixa.
- **Erro (MAE) do XGBoost:**
  - 0,042 no XGBoost;
  - 0,069 na média sazonal;
  - 0,076 na persistência;
  - 0,063 na regressão linear;
  - 0,043 na Random Forest (o XGBoost é 3,0 % melhor e ganha em 11 de 12 pontos).
- **Acerto da faixa à noite:** 91,4 % contra 87,2 % da semana anterior (+4,2 pp); F1 de 0,638 contra 0,583.
- **Tabela 4:** em 15 min, o modelo não é substituível (+4,0 pp); por hora, é substituível (+1,8 pp).
- **H3:** 27,9 % de transição com previsão contra 23,3 % no modo reativo. Rejeitada.
- **Contenção:** a previsão acerta 70,7 % das vezes, contra 62,4 % da média sazonal e 7,8 % de reter sempre.
- **Fuzzy contra tabela:**
  - inversões de sentido: 140 × 86;
  - mudanças perceptíveis a 6 %: 20 (fuzzy), 13 (tabela) e 9 (tabela com histerese).

### Perguntas específicas
- **Por que Mamdani e não Sugeno?** Mamdani tem saída linguística (degraus de classe), legível regra a regra, que é a justificativa de 2.6. Sugeno daria uma fórmula, menos legível.
- **De onde vêm os tercis?** Da distribuição do nível normalizado no treino de Zurique, com todos os pontos reunidos. A norma não dá números, e a escolha do tercil é nossa, declarada.
- **Por que três faixas?** São as três classes que a norma admite para um ponto: a da via e até duas abaixo.
- **Por que p99 e não o máximo?** Um evento raro definiria a escala inteira. O teste de sensibilidade com 95, 99,5 e 99,9 mantém a faixa em 95,7–99,2 % dos blocos.
- **Por que não aprendizado supervisionado para decidir?** Os rótulos seriam escritos por nós: o sistema aprenderia a imitar quem o avalia (circularidade, 2.6).
- **Zurique conta passagens; vocês publicam ocupação.** Transferimos a forma do ciclo, normalizada por ponto, e não a grandeza. Está declarado em 5.3.
- **Por que a H3 falhou?**
  - A previsão retém a luz quando acha que o movimento vai voltar, e isso conta como "transição" na métrica.
  - Ela compensa com outra utilidade: é segunda evidência contra erro de contagem (luz perdida de 0,318 contra 0,343).
- **Fuzzy igualado pela tabela: por que manter?** Foi um resultado honesto: a pertinência parcial é forma de execução, e não ganho de segurança ou energia. O valor está na base de regras legível; o motor é trocável.
- **Como explica uma decisão de 0,521?**
  - R5 com grau 1,0 e R7 com grau 0,06; o centroide dá o degrau 1,92;
  - convertendo, ≈ 0,521, logo acima do piso de 0,5.
- **Alguma regra pode baixar a luz com ocorrência?** Não. Toda regra que desce exige ocorrência = não (CT03 e CT04).
- **E sem dado nenhum?** Nenhuma regra dispara, o nível vai ao pleno. Falta de informação nunca baixa a luz.
- **Por que não LSTM?** Grinsztajn mostra que árvores ganham em dado tabular de porte médio, com custo menor.

---

## Bruno: requisitos e operação
Norma, contrato, dados urbanos, interface e painel.

### O que dominar (seções)
- **1.3 e 1.4:** problema e pergunta.
- **2.3 a 2.5:** Smart Sampa, telegestão e NBR 5101.
- **3.3:** Quadros 2 e 3 (protótipo × implantação).
- **3.5.2:** trechos, GeoSampa e raio de 25 m.
- **3.8:** cálculo da classe P3.
- **3.10:** LGPD.
- **3.11:** energia e linhas de base.
- **3.12.1, 3.12.3 e 3.12.4:** partes interessadas, RF e RNF.
- **4.4:** Quadro 18 e Tabela 1.
- **5.3 e 5.4:** limitações e termo aditivo.

### Números de cabeça
- **Classe P3:** ponderação 1 + 0 + 1 + 0,5 + 0 = 2,5; 6 − 2,5 = 3,5 → P3.
- **Classes:** P3 = 10 lux, P4 = 7,5 lux, P5 = 5 lux (piso). Taxa de 1/10 do pleno por minuto, então P3 → P5 leva no mínimo 5 min.
- **Parque e cadastro:**
  - 662.945 pontos de luz no GeoSampa;
  - 218.768 segmentos de logradouro;
  - 50 mil câmeras do Smart Sampa → ~170 msg/s.
- **Recorte:**
  - 16 trechos e 36 registros, que são 35 postes (uma placa duplicada);
  - 34 postes associados, formando 17 grupos;
  - raio de 25 m.
- **Energia na suíte:**
  - adaptativo = 75,7 % do pleno e 106,7 % do horário fixo;
  - aderência ao envelope: 98,2 % contra 72,2 % do fixo.
- **Energia nas noites reais:** 62,4 % do pleno e 78,6 % do fixo.
- **Contrato:** Caderno de Encargos de 2015 (Anexo III); indicador NI no Anexo V (p. 20–22); troca de dados em até 180 s (item 7.2.1).

### Perguntas específicas
- **Como escolheram a classe P3?** Pela Tabela 6 da NBR 5101, com os parâmetros de uma calçada de via local. A conta está em 3.8; é um cenário de referência e não uma medição da rua.
- **A norma permite dimerizar?** Sim, desde 2024 (6.10): até duas classes abaixo, com taxa de no máximo 1/10 por minuto. A recomendação de não dimerizar com chuva ou neblina não foi implementada; está em 5.3 e no Apêndice E.
- **O Smart Sampa conta pessoas hoje?** O Termo de Referência exige a contagem por área. Se está em operação em cada câmera, não é público, e isso está declarado.
- **Como uma câmera vira um poste?**
  - Tudo é ligado pelo trecho do GeoSampa.
  - Poste → trechos: até 25 m, uma associação que nós construímos.
  - Câmera → trecho: cabe à plataforma, como requisito do Quadro 18.
- **Por que ocupação e não passagens?** Passagens contam duas vezes quem entra e sai da imagem; a média de pessoas presentes, não.
- **Por que 5 min e válido por 15?**
  - 5 min é o tempo mínimo de P3 a P5 pela norma; publicar mais rápido não desce a luz mais rápido.
  - 15 min = três períodos: tolera duas publicações perdidas.
- **LGPD: vocês usam câmeras de reconhecimento facial.**
  - Só consumimos números agregados (média de pessoas e ocorrência).
  - O sistema não tem campo para imagem ou identidade (RNF08).
  - A decisão fica fora da plataforma justamente para isso; o caso de San Diego mostra o risco.
  - A integração real exige tratamento jurídico, declarado.
- **A concessionária seria penalizada por dimerizar?** Pode ser: o indicador NI não diz contra qual classe se mede um ponto dimerizado. Por isso propusemos o termo aditivo (5.4), que manda medir contra a classe registrada no instante.
- **Economia em reais para São Paulo?** Não afirmamos. A suíte não é um perfil anual da cidade, e o driver tem um consumo fixo que não foi contado.
- **Por que a economia sobre o horário fixo é negativa na suíte?** O horário fixo baixa a luz às cegas, inclusive com gente na rua. O adaptativo só desce com movimento baixo: gasta 6,7 % mais, mas não deixa a via sub-iluminada.
- **Quem são as partes interessadas?**
  - o município;
  - a concessionária;
  - o operador da plataforma;
  - o pedestre;
  - a norma (ABNT).
  - A elicitação foi só documental (limitação).
- **Como validaram os requisitos?** Cada RF e RNF tem ao menos um caso de teste (Quadro 15), e todos foram satisfeitos.

### Demonstração ao vivo (ensaiar)
- No painel, abrir a decisão explicada e ler as regras e o grau de cada uma.
- Abrir o mapa do bairro: um poste de esquina fica no pleno por causa do trecho vizinho movimentado (maior volume entre os trechos).

---

## Perguntas que qualquer um dos três deve saber responder
1. **A contribuição em uma frase.** Uma camada que usa dados que a cidade já produz para decidir a luz, e que verifica cada decisão contra a norma antes de chegar ao poste.
2. **Por que H2 é o resultado mais forte.** Porque o critério vem inteiro da norma: zero violações em 667.200 passos.
3. **O que não foi feito.**
   - Integração real com o Smart Sampa e com a telegestão.
   - Medição elétrica.
   - Teste de carga.
4. **Uso de IA.** Programação em par: a IA executou, nós definimos, conferimos e decidimos (Apêndice A).
