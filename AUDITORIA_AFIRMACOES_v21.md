# Auditoria de afirmações sem base — v21 (10/10/2026)

> **Situação:** grupos A e B corrigidos na v22 (10/10/2026). O grupo C continua com os autores. O objetivo específico b) (1.5.2) ainda diz "a partir de conjuntos de dados públicos municipais": decidir se muda.

Leitura integral da `..._SP_v21.docx`. Cada item diz **onde** está, **o que** está
afirmado e **por que** é problema. Três grupos:

- **A. Falso, contraditório ou desatualizado.** Tem que corrigir.
- **B. Sem fonte.** Pôr fonte, suavizar ("estima-se", "segundo o fabricante")
  ou retirar.
- **C. Para os autores confirmarem.** Afirmações sobre o que vocês fizeram ou
  sobre o texto de normas que só vocês podem conferir.

O Capítulo 5, o 4.10 e os números de 3.6 e 3.7 foram conferidos contra os
arquivos de resultado na v20 e na v21 e não entram aqui.

---

## A. Falso, contraditório ou desatualizado

| # | Onde | O que diz | Problema |
|---|---|---|---|
| A1 | 3.5.1, 1º e 2º parágrafos; 3.10, 2º item | Os cenários são "construídos a partir da análise" do SP156 e da base georreferenciada, "de modo que correspondam a situações efetivamente observadas na cidade" | **Não é o que foi feito.** A suíte usa um perfil sintético (`cenarios/executar.py`, `perfil_horario`), e a avaliação usa noites de Zurique. O SP156 não entrou em nenhum cenário. |
| A2 | 1.2.1 ("ambas as coisas já estão em curso"); 2.3, abertura ("contratadas e em operação"); 2.9, 3ª conclusão ("contratadas e em operação"); Quadro 3, última linha ("Em operação") | A telegestão estaria em operação em cada luminária | **Sem base, e contra a fonte que vocês já têm.** O TCM registrou que a telegestão não estava implantada em 2022. O 4º termo aditivo adiou o cronograma e reduziu a contraprestação da telegestão. O próprio 2.3 diz depois "em estágio ainda em curso". O que se sustenta é "**contratada**", não "em operação". |
| A3 | 1.4 ("Operada em fluxo pleno durante toda a noite, como ocorre hoje no município (2.3)"); Quadro 1 ("Opera em regime praticamente invariante, comandado por horário ou por luz natural"); 3.11 (o fluxo pleno "corresponde ao regime hoje praticado no município, caracterizado em 2.3") | Como o parque opera hoje | **O 2.3 não documenta isso;** nenhuma fonte é citada. É provável, mas é inferência. |
| A4 | 3.6, parágrafo "O erro médio não diz…" | Média sazonal no sistema = "o nível da mesma hora na semana anterior" | **Errado:** o código usa a média das **até 4 semanas anteriores** na mesma hora (`decisao/previsao.py`, `MediaSazonal`). Também conflita com a definição do 3º parágrafo de 3.6 e com o 5.1, onde "semana anterior" é outra referência. |
| A5 | 3.7, parágrafo "Piso e taxa são ambos limites inferiores…" | O nível emitido é o maior entre pretendido, piso e taxa; registra-se "taxa" como restrição | **Desatualizado pelo item 71:** a central verifica só o piso, e a taxa é aplicada no nó. |
| A6 | 4.6.1, item "Serviço de decisão" ("aplica em seguida as duas restrições rígidas") | — | Mesmo problema de A5. |
| A7 | 4.6.1, último parágrafo ("planos gratuitos de plataforma suspendem processos ociosos, o que levaria o nó ao failsafe") | — | A parte do failsafe está desatualizada (agora a validade é de até 15 min); a parte dos planos gratuitos está sem fonte (B). |
| A8 | 4.6.3, última frase ("Nos ciclos seguintes, o serviço prossegue a descida à taxa admitida") | — | Desatualizado: a descida agora é feita pelo nó. |
| A9 | Quadros 15 e 16 | Atributos de `decisao`, `telemetria` e `trecho_via` | **Faltam as colunas da migração 009:** validade do comando, nível aplicado e régua aprendida com a data do cálculo. O CLAUDE.md exige atualizar o Quadro 16 quando o esquema muda. |
| A10 | 3.7, parágrafo "A escolha foi confrontada…" | Variação total 2,50 contra 1,47 e 16 contra 9 inversões, "com os números reportados no Capítulo 5" | **Esses números são de uma base antiga e não estão no Capítulo 5.** Retirar os números ou dizer que vieram da primeira comparação, com outra base. |
| A11 | 3.4.1, 1º parágrafo | "segundo **quatro** critérios declarados previamente" | Só três estão listados. |
| A12 | 2.1 ("nenhuma afirmação deste trabalho depende de literatura anterior ao recorte"; exceções declaradas) | Recorte de 2016 em diante | **Shikakura et al. (2003)** é usado em 3.9 e não está entre as exceções. |
| A13 | 3.7, parágrafo das partições ("O critério não é arbitrado pelos autores: é valor derivado do dado") | — | Contradiz o 6.3 ("critério dos autores"). O **valor** vem do dado; a **escolha** dos tercis é dos autores. Reescrever assim. |
| A14 | 3.7, parágrafo da saída ("A saída contínua (…) decorre de exigência normativa: (…) transições abruptas entre patamares seriam inadmissíveis") | — | Contradiz o 2.6 e o próprio 3.7: quem garante a taxa é a verificação, e agora o nó. A saída em degraus também respeitaria a norma (a tabela em degraus teve zero violações). |
| A15 | 3.4.4, 2º parágrafo ("o nível decidido pelo sistema, **em lux**") | — | O nível é uma fração do pleno, não lux (3.2 e 3.3). |
| A16 | 2.9, 1ª conclusão ("prevista em norma desde 2010") | — | A fonte de 2010 é a CIE 115, que não é norma brasileira e, pelo próprio 2.8, só "abre a possibilidade". A NBR 5101 trata do tema desde 2024. |

## B. Sem fonte

| # | Onde | Afirmação | Sugestão |
|---|---|---|---|
| B1 | 1.2.1 | Definição de cidade inteligente e suas "características principais" | Citar uma fonte ou cortar a lista de características. |
| B2 | 2.4, 3º parágrafo | "Um dispositivo constitui elemento de IoT quando reúne quatro atributos" | Definição sem fonte, retomada em 3.3. Citar (Lin et al. servem só se trouxerem isso) ou apresentar como "critério adotado neste trabalho". |
| B3 | 2.4, 1º parágrafo | MQTT é "o padrão consolidado" para telemetria | A fonte citada é a especificação (OASIS), que não sustenta "consolidado". Suavizar. |
| B4 | 3.3, último parágrafo | "circunstância que a literatura sobre parcerias público-privadas de iluminação registra como característica do setor" | **Nenhuma fonte.** Retirar a frase ou citar. |
| B5 | Quadro 5 | PWM do ESP8266 com "instabilidade temporal incompatível"; IRF520 "exige 5 V por declaração do fabricante"; refletor de 12–24 V "denuncia regulação interna de corrente constante"; refletor de 10 W/800 lm daria "cerca de 1.300 lux a 0,44 m"; luxímetros "declaram erro de zero da ordem de dez lux" | Sem fonte e sem conta mostrada. Citar folhas de dados, mostrar a conta ou suavizar. A distância agora é 0,437 m (sem efeito prático). |
| B6 | 3.4.2 | Anúncios declaram de "600 a 1.300 lm por metro" | Sem fonte (anúncios). Dizer "em anúncios consultados pelos autores" ou retirar os números. |
| B7 | 3.4.3, 1º parágrafo | Iluminação de serviço do recinto "entre 300 e 500 lux" | Sem fonte e sem medição. Medir o recinto ou citar norma de iluminação de interiores. |
| B8 | 3.4.4, 1º parágrafo | BH1750 declara "exatidão da ordem de vinte por cento" | A folha de dados do sensor não está nas Referências. Incluir. |
| B9 | 3.7, parágrafo "A base de regras é construída…" | Regras com origem no "conhecimento de domínio documentado na literatura revisada" | **Não há fonte por regra.** Algumas vêm da norma (R1 e o piso), outras são critério de projeto (R6, R7). Indicar a origem de cada uma ou assumir "critério dos autores". |
| B10 | 3.11 e Tabela 2 | Horário fixo "das 0 h às 5 h" | A janela não tem fonte; é escolha de projeto. Declarar assim. |
| B11 | 3.11, último parágrafo | Regulador de corrente "cuja eficiência varia com o nível de saída" | Sem fonte. Citar ou suavizar ("tende a"). |
| B12 | 4.6.1 | Planos gratuitos de PaaS "suspendem processos ociosos" | Sem fonte. Citar a documentação do provedor ou retirar. |
| B13 | 6.3 (enlace); Quadro 5 ("as efetivamente empregadas em implantações") | Telegestão usa "predominantemente" tecnologias de longo alcance | A fonte citada (ABCIP 2024b) lista o Wi-Fi como admitido, mas não diz que as outras predominam. Suavizar. |
| B14 | 6.3 (classe única) | "um mesmo ponto de luz costuma iluminar a pista e a calçada" | Sem fonte. Suavizar ("pode iluminar"). |
| B15 | 3.6 | Janela de 2016 a 2019 é o "período de maior número de pontos de contagem" | Conferir contra o arquivo de Zurique; se não houver contagem registrada, retirar. |
| B16 | 3.6 | 15 min "é a mais próxima, entre as séries públicas localizadas" | Melbourne publica por minuto (só 24 h). Ajustar para "com histórico suficiente". |
| B17 | 3.4.3, último parágrafo | Estabilização: "subiu 0,34 % (…) cerca de três minutos" | Ensaio da **caixa antiga**. Dizer isso ou refazer na caixa nova. |

## C. Para os autores confirmarem

| # | Onde | O quê |
|---|---|---|
| C1 | 2.1 | O procedimento de busca (bases, termos, critérios) **foi feito assim por vocês?** Se não, reescrever com o que foi feito. |
| C2 | 1.6, 2º parágrafo; 3.7 | A NBR 5101 diz que a iluminância vertical se destina "ao reconhecimento facial e à reação antecipada do pedestre diante de eventual ato de agressão"? Conferir a redação na norma. |
| C3 | 2.5 e 3.8 | Valores da 6.10 e soma dos fatores que leva à P3: conferir na tabela da norma (já em D3 do REVISAR). |
| C4 | 6.3 (acionamento) | "indisponibilidade de módulo pronto no mercado nacional em prazo compatível": foi isso que aconteceu? |
| C5 | Quadro 9 | 40–440 W e 90 lm/W "exigidos de toda luminária": conferir as páginas do Caderno. |
| C6 | 2.2 a 2.8 | Os resumos dos artigos (Alves et al., Dizon e Pranggono, Lana et al., Belloni et al., Nogueira etc.) batem com o que os artigos dizem? |

## Conferido e sem problema

- Os autores citados no texto aparecem na lista de Referências (conferência por nome; a conferência inversa, de entradas nunca citadas, não foi feita).
- Números do Capítulo 5, de 4.10 e de 3.6/3.7 batem com os arquivos de
  resultado; os cálculos (170 msg/s, ~1.000 comandos/s) estão declarados como cálculo.
