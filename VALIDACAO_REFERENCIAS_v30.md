# Validação das referências — v30 (11/10/2026)

Cada referência foi aberta no navegador do autor (Chrome), com o autor acompanhando.
Duas conferências por fonte: **dados** (autores, título, veículo, volume, número,
páginas, ano, DOI) e **conteúdo** (o que o texto atribui à fonte está nela?).
Artigos com DOI conferidos também no registro oficial (Crossref). PDFs públicos
baixados para leitura (permissão do autor). Contrato de concessão escaneado: lido
pelas imagens das páginas.

Legenda: ✅ confere · ⚠️ confere com ressalva · ❌ não confere · ◐ conferido em parte

## Problemas encontrados

| # | Referência | Onde no texto | Problema | Proposta |
|---|---|---|---|---|
| 1 | ❌ PERRY (2020) | 3.10, caso de San Diego | O texto diz que a reação pública "levou à desativação do programa em 2020 e à edição de norma municipal de vigilância". O artigo (8 ago. 2020) diz que o uso **continuava** e que a norma ainda estava em comitê ("San Diegans may yet get their ordinance"). Diz também que vandalismo e descarte irregular estavam **na lista de "crimes graves"**, e não que vieram depois. | Reescrever com o que o artigo diz: ~3.300 postes; acesso policial desde ago. 2018; quase 400 usos até 2020; a lista de "crimes graves" incluía vandalismo e descarte; a reação pública levou a pedidos de moratória e a uma proposta de norma municipal de vigilância, em discussão em meados de 2020. |
| 2 | ⚠️ GRINSZTAJN et al. (2022) | 2.7 | O artigo fala de modelos **baseados em árvores** em geral (XGBoost e florestas aleatórias), em dados de **porte médio** (~10 mil amostras), em 45 conjuntos. O texto diz "árvores com reforço de gradiente" e omite o porte. | "modelos baseados em árvores de decisão — como o reforço de gradiente e as florestas aleatórias — continuam superando… em conjuntos de porte médio". |
| 3 | ⚠️ SÃO PAULO (2026c), GeoSampa | 3.5.2 | Pontos de iluminação: 662.945 hoje, confere. Segmentos de logradouro: o texto diz 218.768 (contagem de 27/09/2026, DIVERGENCIAS item 54); hoje o serviço WFS responde **10.200**. A camada mudou ou o servidor passou a limitar a contagem. | Manter o número com a data ("em 27 de setembro de 2026") ou retirá-lo. |
| 4 | ⚠️ ABNT NBR 5123 (2016) | Referências | A edição de 2016 segue em uso (licitação de ago. 2026 cita "ABNT NBR 5123:2016 Versão Corrigida:2016"). | Acrescentar "Versão corrigida" à referência. |
| 5 | ◐ LIN et al. (2017) | 1.2.2, 2.4, 3.3 | Os dados conferem. As três camadas (percepção, rede e aplicação) não puderam ser vistas: o texto é pago, e o sumário só mostra "Architecture" e "Enabling Technologies and Challenges in Different Layers". | Conferir no texto completo (biblioteca/CAPES). |
| 6 | ◐ LANA et al. (2018) | 2.7 | Dados conferem; o texto foi reduzido ao que o resumo sustenta (v23). | — |
| 7 | ◐ GALIČ; GELLERT (2021) | 2.8 | Dados conferem; o resumo confirma câmeras, sensores de som e iluminação e o foco em proteção de dados. As datas 2014–2018 do colega não foram achadas (texto completo atrás de captcha/assinatura). | — |
| 8 | ◐ ABNT NBR 5101 (2024) | 2.5, 3.8, Quadro 6 | Dados conferem (4ª ed., 25/03/2024; versão corrigida 2, 20/09/2024). Pesos da tabela de ponderação da classe P: pendente (C39). | — |

Observação: o Termo de Referência do Smart Sampa diz que as APIs "devem ser tratadas
caso a caso" (Anexo A, item 5). A frase retirada do Quadro 1 na v25 tinha fonte; pode
voltar, se os autores quiserem.

## Todas as referências

| Referência | Dados | Conteúdo citado |
|---|---|---|
| AGÊNCIA NACIONAL DE ENERGIA ELÉTRICA (2022) | ✅ Despacho 3.423, 29/11/2022 | ✅ manual do art. 474 da REN 1.000 |
| ALVES; DIAS; SEIXAS (2019) | ✅ | ✅ (v23) |
| AMERICAN NATIONAL STANDARDS INSTITUTE (2013) | ✅ ANSI C136.41-2013 | ✅ tomada de 7 contatos (Caderno, p. 74) |
| ANTHONY JNR (2024) | ✅ (Crossref: "Anthony, Bokolo") | ✅ (v23) |
| ASKOLA et al. (2022) | ✅ v.54, n.1, p.75-89 | ✅ 0–2 % de vida útil |
| ABCIP (2024a), Censo | ✅ set. 2024 | ✅ 19.362.437; 22.037.666; 20.185.063–24.761.415; 3.793.293; 19,6 % |
| ABCIP (2024b), Guia de telegestão | ✅ 3ª ed., 2024 | ✅ Wi-Fi entre as tecnologias, com 6LoWPAN, Zigbee, LoRaWAN, NB-IoT, RF Mesh |
| ABNT NBR 5101 (2024) | ✅ | ◐ ver item 8 |
| ABNT NBR 5123 (2016) | ⚠️ ver item 4 | ✅ |
| BELLONI et al. (2024) | ✅ v.56, n.5, p.481-501 | ✅ |
| BRASIL, LGPD (2018) | ✅ Lei 13.709, 14/08/2018 | ✅ |
| BUYUKKINACI et al. (2019) | ✅ v.51, n.6, p.910-921 | ✅ M3–M5, ~40 %, Istambul |
| CHEN; GUESTRIN (2016) | ✅ p.785-794 | ✅ |
| CITY OF MELBOURNE (2026) | ✅ | ✅ |
| CIE 115:2010 | ✅ 2ª ed. | ✅ frase da adaptativa, quase literal |
| DIZON; PRANGGONO (2022) | ✅ Eisley (corrigido na v29) | ✅ 66.802 / 99,5 % / calendário solar |
| ESPRESSIF SYSTEMS (2023) | ✅ v4.3, © 2023 | ✅ |
| FRANÇA FILHO; TAVARES (2025) | ✅ v.107, n.1, art. 19 | ✅ |
| GALIČ; GELLERT (2021) | ✅ v.40, art. 105486 | ◐ item 7 |
| GRINSZTAJN et al. (2022) | ✅ | ⚠️ item 2 |
| HIROKI (2021) | ✅ | ✅ 6,2 min de redução |
| INMETRO, Portaria 20/2017 | ✅ 15/02/2017 | ✅ |
| INMETRO, Portaria 62/2022 | ✅ 17/02/2022 (corrigido na v29) | ✅ |
| INMETRO, Portaria 221/2022 | ✅ 23/05/2022 | ✅ |
| ISO/IEC 25010 (2023) | ✅ 2ª ed. | ✅ características (v29) |
| LANA et al. (2018) | ✅ | ◐ item 6 |
| LIN et al. (2017) | ✅ v.4, n.5, p.1125-1142 | ◐ item 5 |
| MAMDANI; ASSILIAN (1975) | ✅ v.7, n.1, p.1-13 | ✅ |
| NOGUEIRA (2024) | ✅ UFF | ✅ |
| OASIS (2019) | ✅ OASIS Standard, 07/03/2019 | ✅ |
| OLIVEIRA; FAGUNDES; SPOLLE (2025) | ✅ v.17, n.27 | ✅ "majoritariamente pessoas negras como suspeitas" |
| PERRY (2020) | ✅ | ❌ item 1 |
| PICKERING; COHEN; DE BAETS (2026) | ✅ v.28, n.4, p.1313-1332 | ✅ "interpretability cannot be assumed just because an FRBM is built" |
| RIBEIRO (2026) | ✅ autoria no portal | ✅ 2.615 sensores, TIM, Procel Reluz |
| RUDIN (2019) | ✅ v.1, n.5, p.206-215 | ✅ "myth" da troca precisão × interpretabilidade |
| SÃO PAULO (2015), Caderno e Anexo V | ✅ | ✅ itens 6.2, 7.1.1, 7.2.1 (180 s), 13, 17; 0–10 V; ≥ 90 lm/W; NI com amostra ≥ 100 |
| SÃO PAULO (2018a), Contrato | ✅ | ✅ cl. 6.1 (20 anos); cl. 11.2 a) normas ABNT, f) Anexo III |
| SÃO PAULO (2018b) | ✅ SECOM | ✅ 20 anos, R$ 6,9 bi, 535 mil / 618 mil |
| SÃO PAULO (2019-2022), aditivos | ✅ termos de retomada e de aditamento publicados | ✅ |
| SÃO PAULO (2021) | ✅ SECOM | ✅ ~90 % convertido |
| SÃO PAULO (2022), Termo de Referência | ✅ | ✅ analíticos; interoperabilidade/API; Anexo XI: iluminação pública (mão dupla), estações climáticas, INMET |
| SÃO PAULO (2023), Contrato 032/SMSU | ✅ 07/08/2023, Consórcio Smart City SP | ✅ |
| SÃO PAULO (2024), Edital | ✅ | ✅ latitude, longitude, endereço, distrito, subprefeitura |
| SÃO PAULO (2025) | ✅ | ✅ 40 mil (20 mil municipais + 20 mil privadas) |
| SÃO PAULO (2026a), dados abertos | ✅ | ✅ "pedestre" → só Cadastro de Lombadas; "Fluxo de Pessoas" = equipamentos |
| SÃO PAULO (2026b) | ✅ | ✅ 50 mil câmeras |
| SÃO PAULO (2026c), GeoSampa | ✅ | ⚠️ item 3 |
| SHIKAKURA; MORIKAWA; NAKAMURA (2003) | ✅ v.27, n.2, p.75-82 | ✅ 6 % atento; 30 % em tarefa |
| STADT ZÜRICH (2026) | ✅ Viertelstundenwerte | ✅ |
| TALQ CONSORTIUM (2026) | ✅ 2.7.1, 16/04/2026 | ✅ REST/JSON, grupos, localização |
| UNIVERSIDADE ESTADUAL DE CAMPINAS (2026) | ✅ | ✅ |
| ZADEH (1965) | ✅ v.8, n.3, p.338-353 | ✅ |
