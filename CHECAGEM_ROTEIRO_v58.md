# Checagem da v58 contra o roteiro do orientador

Leitura completa do `ROTEIRO (1).docx` (10 itens) e da v58 inteira, do título ao Apêndice D, em 10/10/2026.
Legenda: ✅ atende · ⚠️ atende em parte / ajuste recomendado · ❌ não atende.

Para conferir à mão, use a coluna "Onde olhar".

## Resumo

| # | Item do roteiro | Situação | Onde olhar |
|---|---|---|---|
| 1 | Índice + listas separadas | ⚠️ falta atualizar com F9 | Sumário; Listas de quadros, figuras e tabelas |
| 2 | Resumo (~250 palavras, todos os estágios) | ⚠️ 270 palavras; faltam a revisão e as hipóteses | Resumo |
| 3 | Introdução | ✅ | 1.1 a 1.7 |
| 4 | Revisão bibliográfica + hipóteses no fim | ✅ | 2.1 a 2.10 |
| 5 | Metodologia | ⚠️ falta citar autor de metodologia em 3.1 | 3.1 |
| 5 | Engenharia de software | ✅ (dois ajustes pequenos) | 3.12 |
| 5 | Arquitetura (nuvem, back, front, banco, mobile) | ✅ | Quadro 12 |
| 5 | Banco de dados | ✅ | 3.13, Quadros 16 e 17, Figura 10 |
| 6 | Resultados sem discussão | ⚠️ há análise no 4.6 (e um pouco no 4.4) | 4.4 e 4.6 |
| 7 | Análise dos resultados (6 tópicos) | ⚠️ falta "sugerir novos trabalhos" no Cap. 5 | 5.1 a 5.4 |
| 8 | Conclusões (≤ 6 sentenças) + Recomendações | ⚠️ 6 sentenças; objetivos a) e b) não citados | Cap. 6 e 6.1 |
| 9 | Bibliografia | ⚠️ roteiro pede ordem de aparecimento e todas as fontes usadas | Referências |
| 10 | Apêndices, um por tipo | ✅ | Apêndices A a D |

## Detalhe por item

### 1. Índice
- ✅ Sumário com seções e páginas. ✅ Listas de quadros, figuras e tabelas, separadas.
- ⚠️ **Os campos estão desatualizados:**
  - o Sumário não mostra a **3.12.6.4** nem o **Apêndice D**;
  - a Lista de quadros não tem o **Quadro 21**.
  - **Correção:** Ctrl+A e F9 no Word, escolhendo "atualizar o índice inteiro".

### 2. Resumo
- ⚠️ **Tamanho:** tem **270 palavras** (o Abstract tem 253). O roteiro diz "cerca de 250", então está aceitável.
- ✅ Problema, método, resultados e conclusão estão presentes.
- ⚠️ **Estágios ausentes:** o roteiro pede "todos os estágios", e não aparecem a revisão bibliográfica (a lacuna) nem as hipóteses (H1 e H2 aceitas, H3 rejeitada).
  - **Correção:** trocar uma frase por "A revisão não localizou o arranjo…; das três hipóteses, duas foram aceitas e uma rejeitada."

### 3. Introdução
- ✅ Propósito e objetivos (1.5.1 e 1.5.2), necessidade (1.4) e porquê do tema (1.6).
- ✅ A quem se destina e como é executado (1.7). Termos-chave (1.2).

### 4. Revisão bibliográfica
- ✅ Evolução histórica e situação atual:
  - lógica nebulosa, de 1965 e 1975 até 2019–2026;
  - previsão, com Lana (2018) e a mudança de abordagem do campo;
  - estado nacional e internacional (2.2 e 2.8).
- ✅ Citações e referências no padrão ABNT. ✅ Hipóteses enumeradas no fim (2.10).

### 5. Metodologia
- ✅ Coleta de dados detalhada passo a passo e justificada: 3.4 a 3.11, com as etapas 3 a 7 em 3.9.
- ⚠️ **Falta referência de metodologia:** o roteiro diz "é comum utilizar referências a metodologias que suportem sua escolha". A **3.1** classifica a pesquisa (aplicada, quantitativa, exploratória/experimental) **sem citar autor**.
  - **Correção:** citar um livro de metodologia que vocês tenham consultado, por exemplo Gil, *Como elaborar projetos de pesquisa*, ou Marconi e Lakatos. Só citem o que leram.

**Engenharia de software (3.12)**
- ✅ **Roteiro e processo de desenvolvimento:** 3.12.2.
  - ⚠️ A **justificativa** da escolha do processo é fraca. O texto diz *o que* foi feito (iterativo e incremental, guiado pela especificação), mas não *por que* esse processo e não outro.
  - **Correção:** acrescentar uma frase, por exemplo: escolhido porque o prazo curto e a equipe pequena pediam entregas testáveis a cada passo, com o texto servindo de especificação.
- ✅ **Elicitação:**
  - partes interessadas (3.12.1);
  - delimitação de escopo (3.12.1 e 1.3);
  - RF (Quadro 10) e RNF com critérios de qualidade ISO/IEC 25010 (Quadro 11).
- ✅ **Planejamento e validação dos requisitos:** 3.12.1 (cada requisito tem caso de teste) e 3.12.2.
- ✅ **Artefatos:**
  - especificação dos requisitos;
  - diagrama de casos de uso (Figura 3);
  - arquitetura (Figura 4, Quadros 12 e 13);
  - definição do protótipo (3.3 e 3.4);
  - casos de teste (Quadro 15).
- ✅ **Cronograma** (3.12.8), em lista. Um quadro ou gráfico de Gantt é opcional.
- ✅ **Resultado dos testes** (3.12.9), depois da apresentação do protótipo.
  - ⚠️ Para CT01 a CT14, o texto diz só "todos os testes aprovados", sem número nem data.
  - **Correção:** acrescentar "262 testes automatizados aprovados em DD/MM/2026", conferindo antes o número com `pytest` no dia.
- ✅ **Desenho da arquitetura, itens i a v:** o Quadro 12 responde nuvem (sim), back end (sim), front end (sim), banco (sim) e mobile (não, justificado).
- ⚠️ **Detalhe de redação:** a abertura de 3.12 diz "o banco de dados, que **o roteiro** trata à parte". Citar o roteiro do orientador dentro do texto acadêmico fica estranho.
  - **Correção:** trocar por "que se apresenta à parte, em 3.13".

**Banco de dados (3.13)**
- ✅ Especificação dos dados (Quadro 16).
- ✅ Modelagem conceitual (3.13.1), lógica com DER (Figura 10, 3.13.2) e física (Quadro 17), com atributos, domínios, restrições e uso pelo sistema.

### 6. Resultados ("nada de discussão ou análise")
- ✅ 4.1, 4.2, 4.3 e 4.5 são basicamente apresentação.
- ⚠️ **Análise dentro do capítulo de resultados:**
  - **4.6, parágrafo depois da Tabela 3** ("Pelas regras de leitura…, três constatações decorrem…", "Já a pertinência parcial é substituível…"): é interpretação.
  - **4.6, último parágrafo:** "O ganho é moderado…" também é interpretação.
  - **4.4, depois da Tabela 1:** "O resultado é lido com a ressalva de 3.9…" é ressalva interpretativa.
  - **Correção:** deixar no Cap. 4 só os números e a leitura pelo critério fixado antes ("pelo critério, substituível / não substituível"). O "por que" e o "o que significa" vão para 5.2, onde boa parte já está.
- ❌ **Erros de concordância:**
  - "**O** Tabela 3" (4.6, 1º parágrafo);
  - "decorrem **do** Tabela 3" (4.6);
  - "**O** Tabela 4 apresenta" (4.6);
  - "está **no** Tabela 4" (4.1, 3º parágrafo).
  - **Correção:** "A Tabela", "da Tabela", "na Tabela".

### 7. Análise dos resultados
- ✅ Hipóteses avaliadas e declaradas aceitas ou rejeitadas (5.1).
- ✅ Padrões e anomalias com explicação (5.2: quatro padrões e quatro anomalias).
- ✅ Explicação apoiada em teoria e hipóteses (5.1 e 5.2). ✅ Comparação com a literatura (5.2, último parágrafo).
- ✅ Exatidão e confiabilidade (5.3, abertura e limitações). ✅ Implicações e impacto na área (5.4).
- ⚠️ **"Discutir e sugerir novos trabalhos em sequência":** não há trecho no Cap. 5; as sugestões estão só em 6.1.
  - **Correção:** um parágrafo curto no fim de 5.4, por exemplo: "Os desdobramentos mais diretos são… (dados reais do município, integração efetiva, série de 5 min), relacionados em 6.1."

### 8. Conclusões e Recomendações
- ✅ **6 sentenças.**
- ✅ **Sem informação nova.** O "21,4 % a menos" é a conta de 78,6 % de 4.5, então não é dado novo.
- ⚠️ **Objetivos com grau de atingimento:** a conclusão cobre c, d, e, f, g, h e i, mas **não cita a) (caracterizar a infraestrutura) nem b) (especificar as variáveis)**.
  - **Correção:** na 2ª sentença, acrescentar "a infraestrutura municipal foi caracterizada, as variáveis e faixas foram especificadas". Continua sendo uma sentença só.
- ✅ **Recomendações** (6.1): 16 itens, com melhorias de método e de abordagem, cada um com a seção de origem.

### 9. Bibliografia
- ✅ Todas as citações do texto têm referência e vice-versa (conferido por programa).
- ⚠️ **Diacrítico:** no texto aparece "GALIC; GELLERT, 2021" e na referência "GALIČ". Unificar.
- ⚠️ **Duas exigências do roteiro que o documento não segue:**
  1. **Ordem:** o roteiro diz "enumerados na sequência de aparecimento no texto" (sistema numérico). O documento usa o sistema **autor-data** da ABNT (NBR 10520), em que a ordem é **alfabética**. Os dois sistemas são válidos, mas não se misturam. Trocar exigiria renumerar todas as citações do texto.
  2. **Abrangência:** o roteiro diz que a Bibliografia deve ter "toda e qualquer fonte utilizada, e não apenas as citadas". O documento tem só **Referências**, ou seja, só o que foi citado. Fontes usadas e não citadas incluiriam, por exemplo, as documentações de FastAPI, scikit-fuzzy, XGBoost, PostgreSQL, Mosquitto, React/Tailwind e Docker.
- **Decisão de vocês, de preferência confirmada com o orientador:**
  - manter autor-data alfabético (padrão ABNT), ou mudar para o numérico;
  - acrescentar ou não uma seção "Bibliografia consultada" depois das Referências.

### 10. Apêndices
- ✅ Um apêndice por tipo de informação: A (declaração de IA), B (reprodutibilidade), C (fotos) e D (custo).

## Lista de correções (para marcar à mão)

[x] = aplicado pela IA na v59, a conferir no Word.

- [ ] F9 no Word (Sumário com 3.12.6.4 e Apêndice D; Quadro 21 na lista)
- [x] Resumo e Abstract: uma frase sobre a revisão/lacuna e as hipóteses
- [x] 3.1: citar autor de metodologia lido pela equipe (Wazlawick, 2009 — v60)
- [x] 3.12: trocar "que o roteiro trata à parte" por "que se apresenta em 3.13"
- [x] 3.12.2: uma frase justificando o processo iterativo e incremental
- [x] 3.12.9: número e data dos testes automatizados (CT01–CT14)
- [x] 4.4 e 4.6: mover a interpretação para 5.2 (deixar só números e leitura pelo critério)
- [x] 4.1 e 4.6: "O/no/do Tabela" → "A/na/da Tabela"
- [x] 5.4: parágrafo curto sugerindo os trabalhos em sequência (remete a 6.1)
- [x] Cap. 6: citar os objetivos a) e b) na 2ª sentença
- [x] GALIC → GALIČ nas citações
- [x] Autor-data mantido (decisão do autor); "Bibliografia consultada" incluída na v60
