# Checagem do documento contra o roteiro do orientador

**Versão checada:** v60, já salva pelo autor com F9, em 10/10/2026.
**Roteiro:** `ROTEIRO (1).docx`, idêntico ao usado na primeira checagem, feita na v58.

**Como foi lido:**
- A v58 foi lida por inteiro, do título ao Apêndice D.
- Na v60, o texto completo foi comparado parágrafo a parágrafo com a v58. Todo trecho diferente foi lido, e o restante é idêntico.

Legenda: ✅ atende · ⚠️ atende com observação · ❌ não atende.
Para conferir à mão, use a coluna "Onde olhar".

## Resumo

| # | Item do roteiro | Situação | Onde olhar |
|---|---|---|---|
| 1 | Índice com páginas + listas separadas | ✅ | Sumário; Listas de quadros, figuras e tabelas |
| 2 | Resumo (~250 palavras, todos os estágios) | ⚠️ 289 palavras | Resumo |
| 3 | Introdução | ✅ | 1.1 a 1.7 |
| 4 | Revisão bibliográfica + hipóteses no fim | ✅ | 2.1 a 2.10 |
| 5 | Metodologia, com referência de método | ✅ | 3.1 a 3.11 |
| 5 | Engenharia de software | ✅ | 3.12 |
| 5 | Arquitetura: nuvem, back end, front end, banco, mobile | ✅ | Quadro 12 |
| 5 | Banco de dados | ✅ | 3.13, Quadros 16 e 17, Figura 10 |
| 6 | Resultados sem discussão | ✅ | Cap. 4 |
| 7 | Análise dos resultados (6 tópicos) | ✅ | 5.1 a 5.4 |
| 8 | Conclusões (≤ 6 sentenças) + Recomendações | ✅ | Cap. 6 e 6.1 |
| 9 | Bibliografia | ⚠️ autor-data por decisão do autor | Referências; Bibliografia consultada |
| 10 | Apêndices, um por tipo | ✅ | Apêndices A a D |

## Detalhe por item

### 1. Índice
- ✅ O Sumário lista seções e subseções com a página de início, inclusive a 3.12.6.4, as Referências, a Bibliografia consultada e os Apêndices A a D.
- ✅ Listas separadas e atualizadas: 21 quadros (com o Quadro 21, na p. 146), 11 figuras e 4 tabelas.
- **Para conferir à mão:** abrir três entradas do Sumário ao acaso e ver se a página bate.

### 2. Resumo
- ✅ Há uma ou mais sentenças para cada estágio:
  - problema (câmeras e luminárias que não se comunicam);
  - lacuna da revisão ("arranjo não localizado na revisão bibliográfica");
  - método (REST, XGBoost, Mamdani, verificação, MQTT, ESP32);
  - avaliação (suíte, noites reais, bancada, duas linhas de base);
  - resultados (667.200 passos, latência, energia, papel de cada IA);
  - hipóteses (duas aceitas, uma rejeitada);
  - conclusão.
- ✅ O Resumo é seguido de palavras-chave, e o Abstract é equivalente.
- ⚠️ **Tamanho:** o Resumo tem **289 palavras** e o Abstract, 277. O roteiro diz "cerca de 250", então está aceitável. A NBR 6028 admite de 150 a 500 em trabalhos acadêmicos.
  - **Opcional:** para chegar perto de 250, encurtar a frase do método, por exemplo tirando "por interface REST" e "do tipo Mamdani".

### 3. Introdução
- ✅ **Propósito e objetivos:** 1.5.1 (objetivo geral) e 1.5.2 (objetivos específicos a a i).
- ✅ **Necessidade e porquê do tema:** 1.4 (problema e pergunta de pesquisa) e 1.6 (justificativa em cinco eixos).
- ✅ **A quem se destina e como é executado:** 1.7.
- ✅ **Termos-chave:** 1.2 (cidades inteligentes, IoT, IA aplicada à decisão).

### 4. Revisão bibliográfica
- ✅ **Evolução histórica e situação atual:**
  - lógica nebulosa, de 1965 e 1975 a 2019–2026 (2.6);
  - previsão, da autorregressão aos métodos orientados por dados (2.7);
  - casos nacionais e internacionais (2.2, 2.3 e 2.8);
  - lacuna (2.9).
- ✅ Citações e referências no padrão ABNT, autor-data.
- ✅ Hipóteses enumeradas ao final (2.10).

### 5. Metodologia
- ✅ **Coleta de dados passo a passo e justificada:**
  - nó e bancada (3.4);
  - dados e cenários (3.5);
  - previsão (3.6);
  - decisão (3.7);
  - etapas 3 a 7 da avaliação (3.9);
  - energia (3.11).
- ✅ **Referência de metodologia:** Wazlawick (2009) em 3.1, como pesquisa empírica, estilo "apresentação de algo presumivelmente melhor", com a hipótese como centro do trabalho.
  - ⚠️ **Observação:** as categorias "aplicada, quantitativa, exploratória/experimental" da 3.1 não vêm do Wazlawick, cujo livro classifica por estilos. Se a banca perguntar a fonte dessas categorias, é a classificação usual de livros como o de Gil.

**Engenharia de software (3.12)**
- ✅ **Roteiro e processo:** 3.12.2, iterativo e incremental guiado pela especificação, **com justificativa** (prazo curto, equipe pequena, especificação como critério).
- ✅ **Elicitação:**
  - partes interessadas (3.12.1);
  - escopo (3.12.1 e 1.3);
  - RF (Quadro 10);
  - RNF e critérios de qualidade pela ISO/IEC 25010 (Quadro 11).
- ✅ **Planejamento e validação dos requisitos:** cada requisito tem caso de teste (3.12.1 e Quadro 15).
- ✅ **Artefatos:**
  - especificação dos requisitos;
  - diagrama de casos de uso (Figura 3);
  - arquitetura (Figura 4, Quadros 12 e 13, 3.12.6.1 a 3.12.6.4);
  - protótipo (3.3 e 3.4, Figuras 1 e 2, 6 a 9);
  - casos de teste (Quadro 15).
- ✅ **Cronograma:** 3.12.8.
- ✅ **Resultado dos testes depois do protótipo:** 3.12.9, com 262 testes automatizados aprovados em 10/10/2026 e CT15 a CT20 satisfeitos.
- ✅ **Itens i a v do desenho da arquitetura:** respondidos no Quadro 12 (nuvem sim, back end sim, front end sim, banco sim, mobile não, com justificativa).

**Banco de dados (3.13)**
- ✅ Especificação dos dados armazenados (Quadro 16).
- ✅ Modelo conceitual (3.13.1), lógico com DER (Figura 10, 3.13.2) e físico (Quadro 17).
- ✅ O Quadro 17 traz atributos, domínios, restrições e uso pelo sistema.

### 6. Resultados
- ✅ O Cap. 4 apresenta números, tabelas e a leitura pelos critérios fixados antes, sem interpretação. A interpretação está em 5.1 e 5.2.
- ⚠️ **Resquícios leves, aceitáveis:**
  - 4.5 termina com "não se afirma economia anual…", que é delimitação e não análise;
  - 4.3 registra "o ensaio expôs também um efeito da arquitetura…", que é constatação do ensaio.
  - Se quiserem rigor máximo, essas duas frases podem ir para 5.3.

### 7. Análise dos resultados
- ✅ **Hipóteses** avaliadas e declaradas aceitas ou rejeitadas (5.1).
- ✅ **Padrões e anomalias** com explicação (5.2: quatro padrões e quatro anomalias).
- ✅ **Explicação** apoiada em teoria e hipóteses (5.1 e 5.2).
- ✅ **Acordo com a literatura** (5.2: Pasolini, Buyukkinaci, Dizon, Pickering/Rudin, Nogueira).
- ✅ **Exatidão e confiabilidade** (5.3).
- ✅ **Implicações e impacto** (5.4).
- ✅ **Novos trabalhos em sequência** (último parágrafo de 5.4, remetendo a 6.1).

### 8. Conclusões e Recomendações
- ✅ **6 sentenças** e **sem informação nova**. O "21,4 % a menos" é a conta do 78,6 % de 4.5.
- ✅ **Objetivos revisitados com o grau atingido:** a) b) c) d) e) f) g) h) i).
  - O d) e o e) aparecem na 1ª sentença ("sem nenhuma violação… latência de 1,03 s a 1,47 s").
- ✅ Hipóteses e classe de pedestres (P3 a P5) explícitas.
- ✅ **Recomendações (6.1):** 16 itens com melhorias de método e de abordagem, cada um com a seção de origem.

### 9. Bibliografia
- ✅ Todas as citações têm referência e vice-versa, inclusive GALIČ e WAZLAWICK.
- ✅ **"Toda e qualquer fonte utilizada":** atendido pela seção **Bibliografia consultada**, com 10 documentações de ferramentas, títulos conferidos nos sites em 10/10/2026.
- ⚠️ **"Enumerados na sequência de aparecimento":** **não seguido, por decisão do autor.** O trabalho usa o sistema autor-data da ABNT (NBR 10520), em que a lista é alfabética.
  - **Para conferir:** se o orientador cobrar, a resposta é que se seguiu o autor-data da ABNT.

### 10. Apêndices
- ✅ Um apêndice por tipo de informação:
  - A, declaração de IA;
  - B, reprodutibilidade;
  - C, registro fotográfico;
  - D, estimativa de custo.

## Pendências fora do roteiro (antes de entregar)
- [ ] Apêndice A: CPFs, local, data e assinaturas (fora do repositório).
- [ ] Exportar as conversas do aplicativo Claude (claude.ai → Settings → Privacy → Export data).
- [ ] Repositório público no GitHub (o Apêndice B afirma que é).
- [ ] Ler os itens C58 e C59 do REVISAR (texto novo das v59 e v60).
- [ ] Opcional: encurtar o Resumo para perto de 250 palavras.
