# Varredura da v24 — sujeira deixada pelas mudanças (10/10/2026)

Leitura integral da `..._SP_v24.docx` (aceita). Quatro grupos:

- **D. Contradições** (o texto diz duas coisas diferentes, ou contradiz o código/resultados).
- **E. Perdido no tempo** (fala de algo que mudou ou não existe mais).
- **F. Sem base** (afirmação sem fonte ou sem dado).
- **G. Texto solto, erro de redação.**

Nenhum item foi corrigido ainda.

## D. Contradições

| # | Onde | O que diz | Problema |
|---|---|---|---|
| D1 | 1.2.3 ("não consulta a tabela") e 1.6, 3º eixo ("não se resolve por tabela"; a composição é "condição para que o sistema se comporte de modo previsível") | A decisão exigiria inferência nebulosa | 2.6, 3.7, 5.6 e 6.3 mostram que **uma tabela com as mesmas regras é substituta** (mesma segurança e energia, menos mudanças perceptíveis). A introdução promete o que o resultado nega. |
| D2 | 3.2, item "Camada de verificação"; 3.7, parágrafo "A inferência é seguida, obrigatoriamente…"; 4.6 (texto da Figura 1); Quadro 13 | A camada de verificação aplica as **duas** restrições antes de emitir | Desde o item 71, o serviço verifica só o **piso**; a **taxa** é aplicada pelo nó. O próprio 3.7 (parágrafo seguinte) e o 4.6.1 já dizem isso. A Figura 1 pode estar desatualizada também. |
| D3 | 3.4.2 ("plena em torno de metade do ciclo e piso em torno de um quarto") e Quadro 6 (mesmas palavras) | Posição da faixa no ciclo de trabalho | A calibração real (3.4.4) deu **65,6 %** e **34,0 %**. |
| D4 | 3.7 e Quadro 6 ("queda máxima de 0,0083 por passo") × 5.3 ("passos de 0,008") | Tamanho do passo da rampa | O código arredonda para baixo: o passo aplicado é **0,008** (por isso a descida leva 5,25 min e não 5,0). Harmonizar. |
| D5 | 3.4, parágrafo do firmware | "fixado por **quatro** regras" | O parágrafo lista **cinco** (pleno ao ligar; tabela; rampa; validade; configuração fora do repositório). |
| D6 | 3.10 | "**Três** características do arranjo asseguram" | Seguem **quatro** itens. |
| D7 | 3.3, parágrafo após o Quadro 3 | "De dez elos, **sete já existem**: estão contratados ou normalizados" | O próprio quadro diz que a publicação da plataforma "não está publicada", e a v22 tirou "telegestão em operação": **contratado não é existir**. Sugestão: "sete estão contratados ou normalizados". |
| D8 | 4.7.2 ("a relação entre decisão e telemetria é de um para um, porque cada comando emitido produz uma leitura") | Cardinalidade | Hoje o serviço **grava decisão mesmo quando não publica** (`servico.py`, `deve_publicar`). Decisão sem comando não tem telemetria: a relação é de um para **no máximo** um. |
| D9 | 4.4, RNF02, "Forma de verificação: derivada da série de telemetria entre comandos consecutivos" | Como a taxa é verificada | Telemetria agora só chega a cada comando (~1 % dos passos); a taxa é verificada no nó virtual da suíte (3.9, 5.2). |
| D10 | 2.6 ("cada regra terá origem declarada — prescrição normativa ou **conhecimento de domínio**"; partições "derivadas… e **não arbitradas**") | Origem das regras | O 3.7 (v22) diz "norma e **critérios de projeto dos autores**", e o 6.3 diz que os tercis são critério dos autores. |
| D11 | 3.7, parágrafo "A escolha foi confrontada…" | "fundamenta-a na legibilidade da base e na **resposta gradual** junto às fronteiras" | No mesmo parágrafo e em 5.6: mais inversões que a tabela e mais mudanças perceptíveis que a tabela com histerese. A justificativa da escolha não se sustenta pelo próprio resultado; ficaria só a legibilidade. |
| D12 | Quadro 19, linha "Inferência nebulosa × tabela, oito noites reais" (inversões 58 e 20; energia 62,4 %) × última linha "oito noites reais de Zurique, em 15 min" (inversões 32 e 21; energia 63,4 %) | Dois resultados para "oito noites reais de Zurique" | O leitor não sabe por que os números diferem. São sorteios diferentes (avaliação de 3.9 × protocolo de suavidade)? Dizer isso no texto. |
| D13 | 5.4, parágrafo após a Tabela 1 | Discordâncias "por 10 min **em cada um**" | Pela Tabela 1: madrugada ociosa 4,2 % de 1.440 passos ≈ 5 min; ocorrência 16,7 % de 1.080 ≈ 15 min. Conferir no arquivo de resultado. |
| D14 | 2.2, último parágrafo | SP "constitui o caso em que a pergunta pode ser formulada **sem depender de investimento ainda não realizado**" | O 2.3 diz que a telegestão está "contratada e **em implantação**", com cronograma adiado. |
| D15 | 3.5.2 ("cerca de 1 % dos passos") × 5.2 ("cerca de 1,3 %") | Comandos sobre passos | Usar o mesmo número. |
| D16 | Apêndice A, Quadro 21, linha "Capítulo 2 — Prospecção bibliográfica: formulação dos **termos de busca e operadores booleanos** e localização das fontes **nas bases consultadas**" | — | Contradiz o 2.1 da v23 (revisão **narrativa**, sem lista de bases e termos). Os autores precisam decidir o que declarar. |
| D17 | Apêndice A, item 4.3 ("Todas as citações… foram **checadas individualmente contra as fontes primárias**") | Declaração que os autores assinam | Hoje **não é verdade**: Lana et al. só pelo resumo; pesos da classe P (C3) não conferidos; Catlett não conferido (retirado). Só assinar depois de conferir. |

## E. Perdido no tempo

| # | Onde | O que diz | Problema |
|---|---|---|---|
| E1 | Quadro 1, linha "Dados abertos municipais" (SP156, CGE, "adequados à caracterização de distribuições") | Para que servem os dados abertos | O SP156 e o CGE **não são usados** em nada (a v22 tirou dos cenários). A linha sobrou da versão antiga. |
| E2 | 6.3, 2º item ("Os dados públicos empregados são agregados e não são publicados em tempo real, conforme declarado em 3.5") | — | Falava do SP156. O 3.5 não declara mais isso. Os dados usados hoje são Zurique e GeoSampa. |
| E3 | 6.1 (marcador PENDENTE) | "H3 … comparação que as etapas de 3.9 **ainda não preveem**" | O 3.9 já prevê (execução com a previsão desligada) e o 5.6 tem o resultado. |
| E4 | Apêndice A, Quadro 21, linha "**Figuras 1 e 2** — diagramas de arquitetura e de entidade-relacionamento" | — | Desde a v11 a Figura 2 é o diagrama de sequência, e o entidade-relacionamento é a **Figura 3**. |
| E5 | 4.6.3, exemplo de 29/09 | Graus 0,938/0,062, degrau 1,914 e "junto ao tercil inferior" | O texto avisa que a **arquitetura** mudou, mas não que a **base e os tercis** também mudaram (eram os de Melbourne, 0,1038). Com a base atual, os números seriam outros. Avisar ou trocar por exemplo novo. |
| E6 | Quadro 10, RF02 ("a cada ciclo") | Estimativa de demanda | Não há mais ciclo fixo: a decisão é por evento e por varredura. |
| E7 | Quadros 15 e 16 (restrição em {nenhuma, piso, **taxa**}) e 3.7 ("registra-se o piso… ou nenhuma") | Domínio da restrição | A taxa não é mais registrada pelo serviço; ficou só nos registros antigos. Dizer isso. |
| E8 | Quadro 16, evento_urbano: "abrangência em {via, quadra, bairro, município}" | — | Existe no banco, mas o texto (3.5.2, Quadro 14, Quadro 18) não fala de abrangência: toda publicação é por trecho. Campo sem uso explicado. |
| E9 | 3.11 ("adota a potência mínima da **faixa contratual**"; "extremo superior da faixa contratual, 440 W") | — | Depois da v23, o Quadro 9 diz que a faixa é da tabela de distribuição e admite outras potências. Trocar "contratual" por "do Caderno". |
| E10 | 3.11 (trajetória "imposta pela camada de verificação") | — | Hoje a rampa é do nó. |
| E11 | 2.2 (SP com "modernização integral prevista para **2024**") | Notícia de 2021 | Já passou de 2024 e o texto não diz se aconteceu. |

## F. Sem base

| # | Onde | Afirmação | Problema |
|---|---|---|---|
| F1 | 6.3, item da cobertura das câmeras | O ponto sem câmera "permanece no fluxo pleno, **como hoje**" | "Como hoje" = o parque opera em fluxo pleno, afirmação que a v22 tirou por não ter fonte. |
| F2 | Quadro 7, linha "Classe da via — Origem: **Base georreferenciada municipal**" | — | O GeoSampa não traz a classe da NBR. A classe do ponto é atribuída pelos autores (P3, 3.8) no cadastro do banco. |
| F3 | 2.1 (critérios de inclusão: revisão por pares; exceções só para documentos públicos e CIE) | — | O texto usa fontes que não cabem nos critérios nem nas exceções: **ABCIP** (censo e guia), **OASIS** (MQTT), **Espressif** (datasheet), **TALQ**, **ISO/IEC 25010**, **ANSI**, **Perry** (IEEE Spectrum, revista). Acrescentar a exceção (normas, especificações técnicas, documentos setoriais) ou ajustar. |
| F4 | Quadro 7, linha "Volume" ("a variável que a norma indica como **determinante** do tempo de funcionamento… 6.10.3") e 2.5 ("o meio que a própria norma indica como **preferencial**") | — | A 6.10.3 **recomenda** monitorar tráfego de veículos e meio ambiente; não diz "determinante" nem "preferencial", nem fala de pedestres. Suavizar. |
| F5 | Quadro 1, Smart Sampa: "o acesso à interface é tratado **caso a caso, sem endpoint público**" | — | Sem fonte indicada no quadro. Conferir de onde veio (edital de chamamento de 2024?) ou tirar. |
| F6 | 2.2, Reia e Cruz | Depois da correção da v23, a frase ficou **solta**: não sustenta mais nenhum argumento do parágrafo (ver G1). | Tirar a frase e a referência, ou ligar ao argumento. |
| F7 | Quadro 6 ("Classe P3, **Tabela 7**") | Número da tabela da norma | Não conferido (junto com C3/C39). |

## G. Texto solto e erros de redação

| # | Onde | Problema |
|---|---|---|
| G1 | 2.2, Anthony Jnr | Frase quebrada pela v23: "aponta os sistemas isolados… como obstáculo à integração, **e que** a especificação da interface é o instrumento pelo qual **essa fragmentação** se resolve" — falta o verbo ("e conclui que") e "fragmentação" não tem mais antecedente. |
| G2 | 3.7, parágrafo das versões da base | "A base vigente sucede duas versões. **Mais recentemente**, a troca da série… **A primeira**, de oito regras… **A segunda**…" — a ordem confunde; a frase do meio interrompe a lista. |
| G3 | 3.7, parágrafo das partições | "(6.3)" aparece duas vezes com sentidos diferentes: seção 6.3 **do TCC** e subseção 6.3 **da norma**. Escrever "subseção 6.3 da norma". |
| G4 | 3.4.1, Quadro 5, linha "Medição" | "resistência, não iluminância**; Qualquer**" — maiúscula depois de ponto e vírgula. |
| G5 | 7.1, 1º item | "política de retenção **e,** armazenamento" — vírgula fora do lugar. |
| G6 | Apêndice B, 3º parágrafo | "item 71 para… **e** item 72 para… **e** item 73" — dois "e" seguidos na enumeração. |
| G7 | 3.2 / RF06 ("plano de **trabalho**") × resto do texto ("plano de **medição**") | Termo trocado. |
| G8 | Lista de figuras | Figura 2 sem número de página (as outras têm). Lista de quadros: 16 a 20 e 22 sem página. Atualizar o sumário/listas no Word. |
| G9 | 3.9 | A Etapa 7 está como parágrafo normal; as etapas 3 a 6 estão como lista. |

## Observação útil para o C3

O Apêndice A diz que os autores **carregaram a norma ABNT NBR 5101** nas sessões com a IA. Se esse arquivo ainda existir, a conferência dos pesos da classe P (C39) pode ser feita nele.
