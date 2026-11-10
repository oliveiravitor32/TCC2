# Folha de defesa — blocos 3 e 4 do REVISAR (09/11/2026)

Para os três autores lerem juntos. Cada item traz: **o que é e onde está** (numeração da v65), **origem** (quem propôs e se veio antes ou depois do resultado, com o commit), **pergunta provável da banca** com uma resposta de duas frases, e **o que vocês decidem**.

No fim de cada item, escrevam **CONCORDO** ou **MUDA: ...**. Os "concordo" eu marco no REVISAR; os "muda" viram a v66 (só a versão com tudo aceito).

Regra geral para a banca: **o critério foi proposto pela IA, discutido e aprovado por vocês ANTES de rodar** (o commit do protocolo é anterior ao do resultado, e o histórico do git é público). É isso que dá valor ao critério, não o número em si.

---

## Bloco 3 — critérios e desenho dos experimentos

### A2. Limiar de Zurique: ganho mínimo de 2 pp na faixa e 0,02 no F1
- **Onde:** 3.6 (critério mantido para o modelo em operação), 4.1, Quadro 20.
- **Origem:** IA. Protocolo `25a1ef5` (30/09 23:20) **antes** do resultado `c2a31de` (23:22). Com 5 pp o modelo teria reprovado (ganho real: 4,2 pp e 0,055).
- **Banca:** "Por que 2 pontos e não 5?" → *"É uma margem mínima para não chamar de ganho um empate dentro do ruído; o valor em si é critério nosso. O que o torna válido é ter sido fixado e registrado antes de qualquer resultado, e o texto informa o ganho medido para o leitor julgar."*
- **Decidir:** aceitam defender 2 pp como critério de vocês? ☑ **CONCORDO** (10/11/2026)

### A3. Mamdani × tabela: exigia menos inversões **e** menor variação total
- **Onde:** 3.7, 4.6, 5.3.
- **Origem:** IA. Protocolo `b69d78e` (30/09 01:11) antes do resultado `2360a2e` (01:53). O Mamdani variou menos, mas inverteu mais: não passou.
- **Banca:** "Então o fuzzy não serve para nada?" → *"No critério que fixamos antes, a pertinência nebulosa é substituível por uma tabela em degraus sem perda de segurança ou consumo, e declaramos isso. Ela permanece como forma de escrever e executar as regras de modo legível (RNF05), e o orientador aceitou essa formulação (C4)."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### A4. XGBoost × média sazonal no sistema: acerto maior ou déficit menor, sem gastar mais de 2 pp de energia
- **Onde:** 3.6, 4.6 (Tabela 3), 5.3.
- **Origem:** IA, mesmo protocolo `b69d78e` → `2360a2e`. Não passou na série horária de Melbourne.
- **Banca:** "Se a média sazonal empata, por que usar XGBoost?" → *"Com a série horária, não havia razão, e dissemos isso; por isso a série principal passou a ser a de 15 min de Zurique, onde o modelo supera a melhor referência simples. Essa troca foi decidida depois do resultado e o texto declara a ordem (5.3)."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### A5. "Nível que a situação pede" (métrica de déficit)
- **Onde:** 3.9, Tabela 3.
- **Definição:** classe da via com ocorrência ou volume alto; uma classe abaixo com volume médio; margem de 0,02. Criada pela IA para medir o horário fixo (protocolo `f9f3573`, 29/09 02:05, antes do resultado `0dcdf09`, 03:03; correção de fuso em `1793bc7`).
- **Banca:** "O 'nível pedido' não é circular, já que vem das próprias regras de vocês?" → *"Em parte sim: ele usa as mesmas classes da norma que as regras usam, por isso medimos com ele só o que os outros regimes deixam de entregar, e não 'acerto' do adaptativo. A margem de 0,02 só evita contar diferença de arredondamento como déficit."*
- **Decidir:** a definição faz sentido para vocês? ☑ **CONCORDO** (10/11/2026)

### A7. ~170 mensagens/s para 50 mil câmeras
- **Onde:** 3.5.2, Quadro 18, 3.12.6.4, 5.3.
- **Origem:** conta da IA: 50.000 ÷ 300 s ≈ 167. **Cálculo, não teste.**
- **Banca:** "Vocês testaram essa carga?" → *"Não; é a ordem de grandeza derivada do período de 5 min, supondo envios espalhados, e o texto diz que é estimativa. O teste de carga fica como trabalho futuro."*
- **Decidir:** o texto já diz "cerca de" e "estimada"; manter? ☑ **CONCORDO** (10/11/2026)

### B1. Avaliação das IAs com 8 noites reais de Melbourne
- **Onde:** 3.9, Tabela 3. Arquivo `Codigo/cenarios/avaliacao_ia/PROTOCOLO.md`.
- **Origem:** desenho da IA, protocolo `f9f3573` antes de `0dcdf09`. 4 sensores sorteados com semente 57; câmera falhando = contagem zero por 2 h.
- **Banca:** "Por que 8 noites e esses sensores?" → *"O sorteio com semente fixa e registrada impede que escolhêssemos noites favoráveis, e qualquer um reproduz a seleção. Oito noites são amostra pequena, e por isso reportamos números e não afirmamos significância estatística."*
- **Decidir:** leram o protocolo? ☑ **CONCORDO** (10/11/2026)

### B2. Linha de base "horário fixo" = atenuação das 0 h às 5 h locais
- **Onde:** 3.11 ("janela escolhida pelos autores"), Tabela 2. Erro de fuso (UTC) corrigido em `1793bc7` (30/09).
- **Banca:** "Por que 0 h–5 h? Isso é o que São Paulo usa?" → *"Não achamos fonte oficial de programação horária no parque, e o texto diz que a janela é escolha nossa. Ela representa o que uma telegestão sem dados do ambiente pode fazer: atenuar quando o movimento costuma ser menor."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### B3. Desenho do experimento de Zurique
- **Onde:** 3.6, 4.1, Quadro 20. Arquivo `Codigo/modelo/PROTOCOLO_ZURIQUE.md`.
- **Origem:** IA, `25a1ef5` antes de `c2a31de`. Janela 2016–2019, pontos com ≥ 730 dias e ≥ 95 % de cobertura, treino até 2018, teste 2019, alvo = média dos próximos 60 min.
- **Banca:** "Por que 2016–2019?" → *"É o período com mais pontos completos e antes da pandemia, que mudou o padrão de movimento. O experimento mede a previsão, não a luz; o efeito na luz é medido à parte, na suíte e nas noites reais."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### B4. Conferências posteriores de Zurique
- **Onde:** 4.6 ("Três conferências posteriores ao protocolo, e por isso reportadas à parte").
- **Origem:** IA, `e84046f` (30/09 23:36), **depois** do resultado; o texto já declara assim.
- **Banca:** "Isso não é procurar até achar?" → *"Elas vieram depois e estão separadas do resultado principal, que não mudou; servem só para ver se o ganho se sustenta por ponto e contra referências mais fortes. Se tivessem dado contra, também estariam lá."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### C31. Troca da série principal para Zurique (15 min)
- **Onde:** 3.6, 5.3 ("decidida depois desse resultado... e é declarada como tal"), Quadro 19 ("troca para Zurique").
- **Origem:** desenho todo da IA, protocolo `840800d` (06/10 23:40) antes do resultado `45d1e3c` (07/10 00:46). Escolhas: sensor travado = zero por ≥ 8 h entre 8 h e 20 h; horário de verão com média dos carimbos repetidos; realocação só reportada; feriados do cantão sem os meios-feriados; noites sorteadas pela mesma regra e semente; referência do trecho com 672 blocos de 15 min (7 dias).
- **Banca:** "Trocar de dado depois de perder não é ajustar o resultado?" → *"A troca foi motivada pelo resultado e declaramos isso no texto, com os resultados de Melbourne mantidos. Mas o critério de aprovação e as regras de limpeza de Zurique foram fixados antes de rodar, num commit anterior ao resultado."*
- **Decidir:** concordam com as regras de limpeza listadas? ☑ **CONCORDO** (10/11/2026)

### C32. Rampa das funções de pertinência (base v6)
- **Onde:** 3.7 ("a regra foi restabelecida depois de observado esse efeito, e a ordem é declarada").
- **Origem:** IA, `e6df6e8` (07/10 23:57), **depois** de ver o efeito da v5 (rampa fixa de 0,05 engolia o volume de via vazia). A regra (¼ da faixa mais estreita = 0,017) era a da v0; resultados da v5 guardados no repositório.
- **Banca:** "Vocês mexeram na função depois de ver o resultado?" → *"Sim, e dizemos isso: voltamos à regra que já estava na primeira versão, que tinha sido trocada sem querer por um valor herdado. Os resultados da versão anterior continuam no repositório para comparação."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

---

## Bloco 4 — interpretações e conclusões

### C1. "Retirar as regras custa luz"
- **Onde:** 4.6. Depende de A5.
- **Fato:** horário fixo ≥ 2 lux abaixo do pedido em 278 min (suíte) e 529 min (noites reais); o adaptativo, nunca.
- **Banca:** "O adaptativo nunca fica abaixo porque ele é quem define o pedido." → *"O pedido é derivado do movimento e da norma, não da saída do sistema; o adaptativo pode ficar abaixo quando a rampa atrasa ou quando a contagem falha, e isso foi medido. O que o resultado mostra é que um horário cego atenua em momentos em que há movimento."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### C2. "Com a série horária, o XGBoost é substituível pela média sazonal no sistema"
- **Onde:** 4.6, 5.3.
- **Banca:** "Isso não enfraquece o trabalho?" → *"É o resultado medido, e escondê-lo enfraqueceria mais. Ele é a razão da troca para a série de 15 min, onde o modelo passa a ganhar."*
- **Decidir:** concordam em afirmar? ☑ **CONCORDO** (10/11/2026)

### C3. "Com 15 min, o XGBoost supera as referências simples; ganho moderado"
- **Onde:** 4.1, 4.6. Números atuais: +4,2 pp na faixa, F1 0,638 × 0,583.
- **Banca:** "Então ML é indispensável?" → *"Não dizemos isso: o ganho é real, mas moderado, e o texto evita a palavra. O que dizemos é que, com o critério fixado antes, o modelo não é substituível pelas referências simples nessa série."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### C5. Por que o ML não ganha com a série horária
- **Onde:** 5.3.
- **Fato:** quatro razões; três medidas (regras leem a previsão em 3 faixas; subida da luz é imediata; movimento noturno é regular) e **uma hipótese não investigada** (modelo treinado para erro médio, não para a faixa).
- **Banca:** "Vocês testaram treinar para a faixa?" → *"Não; o texto a apresenta como hipótese, separada das três que foram medidas. Fica como recomendação."*
- **Decidir:** confiram que no 5.3 a quarta razão está como hipótese. ☑ **CONCORDO** (10/11/2026)

### C6. "A previsão é segunda evidência contra erro de contagem"
- **Onde:** 3.7, 4.6, 5.3, Tabela 3.
- **Fato:** medido só no início da noite (0,153 × 0,280); na madrugada não protege (119,5 min na classe mínima, com ou sem previsão).
- **Banca:** "E de madrugada?" → *"De madrugada a previsão também é baixa e não segura o nível, e o texto diz isso. O pior caso continua dentro da faixa da norma, porque o piso é P5."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### C9. "Uma pessoa sozinha não força o pleno"
- **Onde:** 3.7. Decisão do autor; argumento redigido com a IA.
- **Banca:** "E a segurança de quem passa sozinho?" → *"A classe mínima, P5, já é uma classe de pedestres prevista pela NBR 5101; quem passa sozinho continua com iluminação normativa. Ocorrência de segurança reportada leva ao pleno na hora (R1)."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### C21. Diagnóstico no campo pela telemetria elétrica
- **Onde:** 3.4.5, 3.12.6.2, 5.3. Ideia do autor, redação da IA (v12).
- **Fato:** no parque, conferir potência medida × esperada; confirma o consumo, não a luz na via. **Não ensaiado.** O texto **não** diz que a concessionária estima lux pelo consumo (falta fonte, D12).
- **Banca:** "Como vocês sabem que a luz chegou na rua?" → *"Na bancada medimos lux; no parque, só a potência, e declaramos que sujeira, obstrução e depreciação passariam despercebidas. É proposta, não ensaio."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### C22. 5.3: controle coordenado e proteção de dados em dois itens
- **Onde:** 5.3. Frase nova da IA: "O que o trabalho assegura é que a camada de decisão não consome imagem nem identificador (3.10)".
- **Atenção (conferido na v65):** o 5.3 ainda diz "Cada ponto de luz é decidido isoladamente". **Desde a v62 a decisão é por grupo de controle**, então a frase ficou imprecisa. Sugestão para a v66: "Cada grupo de controle é decidido a partir dos seus próprios trechos: não se contempla o controle coordenado entre grupos, em que o nível de um ponto considera o dos vizinhos." A limitação continua valendo, porque o grupo não olha para os vizinhos.
- **Banca:** "E a LGPD?" → *"O sistema só recebe contagens agregadas por trecho; nenhuma imagem ou identificador entra ou é gravado. A conformidade da plataforma de câmeras é de quem a opera."*
- **Decidir:** ☑ **CONCORDO** (10/11/2026)

### C24. 2.5: origem contratual da NBR 5101
- **Onde:** 2.5, Referências (SÃO PAULO, 2015, Anexos III e V).
- **Origem:** IA (v14), a partir da pergunta do orientador.
- **Conferir na fonte:** cláusula 11.2 do contrato (p. 28); itens 6.2 e 6.5 do Caderno; Anexo V, indicador NI (p. 20–21). E decidir a forma da referência: uma só (2015) ou separada em 2015a e 2015b.
- **Banca:** "A NBR é lei?" → *"Não; ela obriga pelo contrato da PPP, que a exige na cláusula 11.2 e no Caderno de Encargos. O indicador NI do Anexo V afere a iluminância em campo e afeta a remuneração da concessionária."*
- **Decidir:** abriram as páginas? Referência única ou 2015a/2015b? ☑ **CONCORDO** (10/11/2026)

### C25. 5.3: o indicador NI contaria um ponto atenuado como não atendido
- **Onde:** 5.3. **Interpretação da IA:** o Anexo V zera o fator do ponto abaixo de 80 % do mínimo, e P5 = 50 % de P3.
- **Limite:** a busca no Caderno foi por palavra ("dimeriz", "adaptativ"), não leitura integral; os aditivos também não tratam do assunto. A v64 acrescentou a proposta de redação de termo aditivo.
- **Banca:** "Então o sistema seria multado?" → *"Pelo texto do indicador, um ponto em P5 aferido contra P3 ficaria abaixo de 80 %, e o contrato não diz contra qual classe aferir um ponto dimerizado. Por isso propomos um termo aditivo que defina isso (5.4)."*
- **Decidir:** concordam com a interpretação? ☑ **CONCORDO** (10/11/2026)

### C33. Arquitetura de implantação
- **Onde:** 3.4, 3.5.2, 3.7, 3.12.4 (RNF03, RNF07), 3.12.6. Seguir o Caderno: decisão do autor. **Desenho da IA** (protocolo `a96f3a8`, 08/10 23:34 → resultado `afb87b3`, 23:39):
  - validade = até vencer o volume que sustenta a decisão, máx. 900 s;
  - renovar faltando 300 s, só se o comando novo vencer depois;
  - varredura a cada 60 s; régua a cada 24 h;
  - piso na central e no nó; taxa no nó; RNF03 = 180 s (Caderno 7.2.1).
- **Banca:** "A verificação ainda é invariante se a taxa está no nó?" → *"Sim: nenhum comando sai da central sem o piso conferido, e o nó aplica de novo piso e taxa com os valores que viajam no comando, pela mesma regra. Se o nó fica sem comando válido, volta ao pleno."*
- **Decidir:** (a) validade e renovação fazem sentido? (b) o texto diz "o Caderno exige", nunca "São Paulo usa"? (c) abrir o PDF do Caderno em 7.1.1, 7.1.2, 7.2.1 e p. 4. ☑ **CONCORDO** (10/11/2026)

---

## Já conferido pela IA no texto da v65 (09/11/2026)

- C31: o 5.3 já declara que a troca para Zurique foi decidida depois do resultado.
- C32: o 3.7 já declara que a regra da rampa foi restabelecida depois de observado o efeito.
- B2: o 3.11 já diz "janela escolhida pelos autores".
- B4: o 4.6 já separa as conferências posteriores.
- A7: o texto já diz "cerca de" e "estimada".
- **C22: o 5.3 ainda diz "decidido isoladamente"**, frase que ficou desatualizada com os grupos (v62). É a única correção de texto que a IA encontrou nos dois blocos.
