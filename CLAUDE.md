# Projeto: Iluminação Adaptativa (TCC) — contexto para o Claude Code

Responda sempre em **português do Brasil**. O autor é iniciante em eletrônica e intermediário em programação: explique de forma direta, passo a passo, sem enrolar.

## Fonte da verdade

> **Limpeza de 10/10/2026:** na pasta ficaram só as 3 últimas versões (hoje **v59, v60 e v61**, com os `_revisado`); as demais versões citadas abaixo, o `_SP_7` obsoleto e as figuras soltas `Figura2_*.png` saíram da pasta e continuam no histórico do git (`git log -- <arquivo>` e `git show <commit>:<arquivo>`). Manter no máximo as 3 últimas versões.

> **Estado em 10/10/2026:** a versão mais recente do texto é a **v61** (`..._SP_v61.docx`), que acumula todas as rodadas; as versões v4 a v51 ainda aguardam a aprovação do autor no Word. A v2 abaixo é a última aprovada formalmente.

A especificação vigente é a **v2**: `C:\Users\vitor\Documents\GitHub\TCC2\Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v2.docx` (26/09/2026, com as duas rodadas de revisão aceitas pelo autor). **Siga o TCC.**

- `..._SP.docx` (e o `.pdf`) = versão anterior, mantida como histórico; não editar.
- `..._SP_revisado.docx` = a mesma v2 com as alterações marcadas (registro do que mudou).
- `..._SP_v3_revisado.docx` = v2 + rodadas de 27 e 28/09/2026 marcadas (meteorologia, itens 49, 53, 54 e 55 do DIVERGENCIAS). `..._SP_v3.docx` = a mesma com tudo aceito e a Figura 2 nova.
- `..._SP_v4_revisado.docx` = v3 aceito + rodada de 29/09/2026 marcada (item 56: volume de 5 min, degraus de classe, pacote, Quadro 18 da especificação da interface; 1.4; previsão como segunda evidência). `..._SP_v4.docx` = a mesma com tudo aceito; **passa a ser a vigente quando o autor aprovar a revisão no Word**.
- `..._SP_v5_revisado.docx` = v4 aceito + rodada de 30/09/2026 marcada (itens 57 a 60: avaliação das IAs por retirada e por substituto simples, déficit do horário fixo, experimento de Zurique em 15 min; 3.6, 3.7, 3.9, 5.1, nova 5.6 com Quadros 19 e 20, 6.3, 7.1). `..._SP_v5.docx` = a mesma com tudo aceito; **passa a ser a vigente quando o autor aprovar a revisão no Word**.
- `..._SP_v6_revisado.docx` = v5 aceito + rodada de 01/10/2026 marcada (Apêndice B de reprodutibilidade com o Quadro 22, frase em 3.9 e duas linhas **propostas** no Quadro 21 da declaração de uso de IA, que os autores precisam revisar). `..._SP_v6.docx` = a mesma com tudo aceito.
- `..._SP_v7_revisado.docx` = v6 aceito + segunda rodada de 01/10/2026 marcada (1.4: problema e pergunta de pesquisa; 1.5.1; 2.6: propriedades da inferência nebulosa sem exclusividade; 3.7: tercis únicos sobre o nível normalizado; item 61 em 3.7, 3.9, 5.6 e 6.3; limitação de cobertura das câmeras; Apêndice B; referência de Shikakura et al.; a de Akashi e Neches saiu na v8). `..._SP_v7.docx` = a mesma com tudo aceito.
- `..._SP_v8_revisado.docx` = v7 aceito + correção de 01/10/2026 marcada (limiares de percepção em 3.9: 6 % pela fonte conferida, Shikakura et al., e 15 % como valor dos autores; citação de Akashi e Neches **retirada** por decisão do autor; conferência a 20 % e 30 % em 5.6). `..._SP_v8.docx` = a mesma com tudo aceito.
- `..._SP_v9_revisado.docx` = v8 aceito + frase em 3.5.2 e limitação em 6.3 sobre a associação câmera → trecho, que cabe à plataforma e não foi construída nem verificada (01/10/2026). `..._SP_v9.docx` = a mesma com tudo aceito.
- `..._SP_v10_revisado.docx` = v9 aceito + resultados com dado disponível (02/10/2026): abertura do Capítulo 5, 5.2, 5.4 (Tabela 1), 5.5 (Tabela 2, luminária de referência), abertura de 6.3 e item 42 em 6.3 e 7.1. `..._SP_v10.docx` = a mesma com tudo aceito.
- `..._SP_v11_revisado.docx` = v10 aceito + nova subseção 4.6.3 "Percurso de uma decisão" (dez passos, diagrama de sequência e exemplo real com o nó simulado) e ajuste em 3.2 (02/10/2026). **A Figura 2 passou a ser o diagrama de sequência; o diagrama entidade-relacionamento é a Figura 3.** `..._SP_v11.docx` = a mesma com tudo aceito.
- `..._SP_v12_revisado.docx` = v11 aceito + transposição do diagnóstico para o campo (02/10/2026): em 3.4.5, 4.6.2 e 6.3, a telemetria elétrica do controlador no lugar da iluminância, com o limite declarado (confirma o consumo, não a luz na via). **Não afirmar que a concessionária estima lux pelo consumo: falta fonte** (busca pendente, item D12 do arquivo de revisão). `..._SP_v12.docx` = a mesma com tudo aceito.
- `..._SP_v13_revisado.docx` = v12 aceito + separação, em 6.3, da limitação que juntava controle coordenado, tensão de rede e proteção de dados (02/10/2026): viraram dois itens, e a tensão de rede saiu, por já constar do item do nó em baixa tensão. `..._SP_v13.docx` = a mesma com tudo aceito.
- `..._SP_v14_revisado.docx` = v13 aceito + origem contratual da NBR 5101 (03/10/2026, pergunta do orientador): parágrafo novo em 2.5 (a norma obriga pelo contrato, cláusula 11.2, e pelo Caderno, itens 6.2 e 6.5; indicador NI do Anexo V afere em campo e afeta a remuneração), limitação nova em 6.3 (o NI não diz contra qual classe se afere um ponto dimerizado) e a referência de 2015 passa a cobrir os Anexos III e V. `..._SP_v14.docx` = a mesma com tudo aceito.
- `..._SP_v15_revisado.docx` = v14 aceito + correção em 3.5.2 (03/10/2026): a validade do volume (15 min) segue a mesma lógica do failsafe do nó, mas o failsafe é de **15 s** (comando a cada 5 s); vírgula dupla no RNF07. `..._SP_v15.docx` = a mesma com tudo aceito.
- `..._SP_v16_revisado.docx` = v15 aceito + limitação em 6.3 (03/10/2026): comando a cada 5 s é cadência de bancada; no parque (~120 mil comandos/s) exigiria comando só na mudança + sinal de vida espaçado, não implementado. `..._SP_v16.docx` = a mesma com tudo aceito.
- `..._SP_v17_revisado.docx` = v16 aceito + resultados da sessão de bancada (05/10/2026, itens 65 e 66): 4.10 com CT15–CT20 (**CT18 não satisfeito** pelo texto estrito, decisão do autor: failsafe em 15,0 s, sensor em 17,3 s), 5.3 (latência 0,98–1,93 s, três execuções declaradas, falha induzida, failsafe), energia de bancada em 5.5, conferência da calibração em 3.4.4 (tabela na memória do nó) e POST /bancada no Quadro 14. `..._SP_v17.docx` = a mesma com tudo aceito.
- `..._SP_v18_revisado.docx` = v17 aceito + Apêndice B (05/10/2026): três linhas no Quadro 22 (conferência, CT15–CT20, energia de bancada com `bancada/energia_bancada.py`) e frase sobre o que da bancada se reproduz sem o hardware. `..._SP_v18.docx` = a mesma com tudo aceito.
- `..._SP_v19_revisado.docx` = v18 aceito + comparação de modelos (06/10/2026, item 68): 2.7 (a referência não ordena as árvores entre si), 3.6 (regressão linear e floresta aleatória, regra de 2 % fixada antes), 5.1 (XGBoost superior ao linear, **equivalente à Random Forest**; mantido pela referência e pelo custo de previsão) e linha no Quadro 22. Sem a M5 (D14 pendente). `..._SP_v19.docx` = a mesma com tudo aceito.
- `..._SP_v20_revisado.docx` = v19 aceito + rodada de 09/10/2026 (itens 69 a 72): **Zurique 15 min passa a ser a série principal** (3.6, 5.1; Melbourne vira achado), tercis 0,0693/0,2946 e rampa 0,017 (3.7), **arquitetura de implantação** (3.4, 3.5.2 parágrafo novo, 3.7, 4.4 RNF03 = 180 s e RNF07 por validade, 4.6, Quadro 14, Quadro 17, 4.10), régua p99 com teste de sensibilidade (3.6, 6.3), Capítulo 5 inteiro com os números da v6 + item 71 (Tabelas 1 e 2, Quadro 19), 6.3, 7.1 e Quadro 22. `..._SP_v20.docx` = a mesma com tudo aceito.
- `..._SP_v21_revisado.docx` = v20 aceito + caixa nova e sessão de bancada de 10/10/2026 (item 73): Quadro 4 (caixa de polipropileno 43,7 × 31 × 24 cm, 0,437 m), 3.4.2, 3.4.4 (sessão 113), 4.10 (CT15–CT20 **todos satisfeitos**), 5.3 (latência 1,03–1,47 s; CT18 pleno no vencimento), 5.5 (energia 75,9 %), 6.3 e Apêndice B. `..._SP_v21.docx` = a mesma com tudo aceito.
- `..._SP_v22_revisado.docx` = v21 aceito + retirada de afirmações sem base (10/10/2026, `AUDITORIA_AFIRMACOES_v21.md`, grupos A e B; regra do autor: sem fonte, **tirar**, e só suavizar o que é importante): telegestão "contratada" e não "em operação"; cenários **não** vêm do SP156 (3.5.1); média sazonal = até 4 semanas; verificação do piso na central e taxa no nó (3.7, 4.6); Quadros 15 e 16 com as colunas da migração 009; Quadro 5 e 3.4 sem números sem fonte; Shikakura como exceção do recorte (2.1). `..._SP_v22.docx` = a mesma com tudo aceito.
- `..._SP_v23_revisado.docx` = v22 aceito + grupo C da auditoria (10/10/2026): objetivo b) com cadastro georreferenciado + séries públicas de pedestres; 2.1 vira **revisão narrativa** (lista de bases e termos retirada: o autor não confirma a busca); Alves, Anthony Jnr, Lana e **Reia e Cruz** reescritos conforme os resumos (2.2, 2.7, 3.2); Quadro 9 (40–440 W é a tabela de distribuição do Caderno, p. 26, que admite outras potências; ≥ 90 lm/W p. 23 e 0–10 V p. 28 conferidos); 6.3 acionamento "por decisão dos autores". `..._SP_v23.docx` = a mesma com tudo aceito.
- `..._SP_v24_revisado.docx` = v23 aceito + retirada de Catlett et al. (Array of Things) e Sanchez et al. (SmartSantander) por decisão do autor (2.1, 2.2, 3.5.2, Quadro 18, Referências); Stratumseind (2.8) sem "meteorologia" e "há mais de uma década", que o resumo de Galič e Gellert não sustenta. `..._SP_v24.docx` = a mesma com tudo aceito.
- `..._SP_v25_revisado.docx` = v24 aceito + correções da varredura (`AUDITORIA_VARREDURA_v24.md`, grupos D a G): verificação = piso no serviço e taxa no nó em 3.2, 3.7, 4.6 e Quadro 13; 1.2.3 e 1.6 sem "não se resolve por tabela"; ciclos 65,6 %/34,0 % e passo 0,008 (3.4.2, Quadro 6, 3.7); decisão–telemetria um para no máximo um; SP156/CGE fora do Quadro 1 e do 6.3; Reia e Cruz retirados; exceção de normas e documentos técnicos no 2.1; classe da via atribuída pelos autores (Quadro 7). Fora: D16/D17 (Apêndice A), F7, G8 (atualizar campos no Word), G9. `..._SP_v25.docx` = a mesma com tudo aceito.
- `..._SP_v26_revisado.docx` = v25 aceito + D16 (Quadro 21: revisão narrativa, por decisão do autor) e **Figuras 1, 2 e 3 refeitas** (sem marca de revisão nas imagens): Figura 1 com VM e contêineres (não PaaS), PostgreSQL em contêiner, painel fora da VM, verificação = piso e nó com rampa e validade; Figura 2 com comando {nivel, validade_s, piso, taxa_min}, publicação só na mudança ou renovação e rampa no nó; Figura 3 com as colunas da migração 009 e decisão–telemetria 1 : 0..1. Scripts em `Codigo/figuras/`. `..._SP_v26.docx` = a mesma com tudo aceito.
- `..._SP_v27_revisado.docx` = v26 aceito + Etapa 7 do 3.9 no estilo de lista das demais etapas (formatação marcada). `..._SP_v27.docx` = a mesma com tudo aceito.
- `..._SP_v28_revisado.docx` = v27 aceito + **reestruturação pelo roteiro do orientador** (11/10/2026): o antigo Capítulo 4 (Engenharia de Software) entrou na Metodologia como **3.12 Engenharia de software** e **3.13 Banco de dados**; 4.8–4.10 movidos para antes do banco (3.12.7–3.12.9); Resultados, Análise e Conclusões passam a ser os **Capítulos 4, 5 e 6**; Quadros renumerados (**15 = casos de teste, 16 = entidades, 17 = tabelas**); todas as referências cruzadas convertidas; sumário com quatro níveis. `..._SP_v28.docx` = a mesma com tudo aceito, **editada e aprovada pelo autor no Word** (base da v29).
- `..._SP_v29_revisado.docx` = v28 do autor + revisão de referências por um colega (feedback sobre a v18), conferida no navegador (11/10/2026): Quadro 11 com os termos da ISO/IEC 25010:2023 (Segurança operacional (safety) / (fail safe), Manutenibilidade (modificabilidade), Flexibilidade (escalabilidade)); DIZON, **Eisley**; Portaria Inmetro 62 é de **17/02/2022**; Portaria 20/2017 incluída e certificação "instituída em 2017, prazos a partir de 2019, consolidada em 2022" (Quadro 3 e 3.3); Stratumseind no passado (datas 2014–2018 **não** conferidas). Reia e Cruz já tinham saído na v25. `..._SP_v29.docx` = a mesma com tudo aceito.
- `..._SP_v30_revisado.docx` = v29 aceito + autoria das referências (feedback do orientador, 11/10/2026): as cinco notícias foram abertas e **nenhuma tem autor pessoal** (assinam SECOM, SMSU e CePIL/NIPE); as referências do município ganharam o órgão responsável (Secretaria Municipal de Serviços, de Serviços e Obras, Especial de Comunicação, de Segurança Urbana); NIPE virou "UNIVERSIDADE ESTADUAL DE CAMPINAS. Núcleo Interdisciplinar de Planejamento Energético" (citação e ordem alfabética ajustadas). Sem órgão (não confirmado): termos aditivos, portal de dados abertos e GeoSampa. `..._SP_v30.docx` = a mesma com tudo aceito.
- `..._SP_v31_revisado.docx` = v30 aceito + correções da validação das 52 referências no navegador (`VALIDACAO_REFERENCIAS_v30.md`, 11/10/2026): Perry (3.10) sem "desativação do programa" nem "edição de norma" — o artigo de ago. 2020 diz que o uso continuava e a norma estava em comitê; Grinsztajn (2.7) com árvores em geral, 45 conjuntos, porte médio; GeoSampa (3.5.2) com a data da contagem (27/09/2026; hoje a camada de segmentos responde 10.200); NBR 5123 "Versão corrigida"; Quadro 1 volta a dizer que o TR trata o acesso por API caso a caso (Anexo A, item 5). `..._SP_v31.docx` = a mesma com tudo aceito.
- `..._SP_v32_revisado.docx` = v31 aceito + grupo 2 do REVISAR (11/10/2026): 3.7 parágrafo norma × tercis (C35); 3.12.6.3 com o **exemplo real da bancada de 10/10** (decisão 92b2a978, nível 0,500, validade 887 s, rampa 5 min 15 s); restos da arquitetura antiga em 3.4.2, 3.4.5, 3.11, Quadro 13 e 3.12.6.1; **Pasolini et al. (2024)** em 2.8 e nas Referências; **Quadros 19 e 20 viram Tabelas 3 e 4, Quadros 21 e 22 viram 19 e 20**, com Lista de tabelas. `..._SP_v32.docx` = a mesma com tudo aceito.
- `..._SP_v33_revisado.docx` = v32 aceito + **hashes de commit do Quadro 20 atualizados** depois da limpeza do histórico do git (11/10/2026: pastas Docs/Estagio e Docs/Atividades_Qualidade-de-Software retiradas de todo o histórico; cópia em `Documents/Arquivos_UNIP_retirados_do_TCC2`, backup em `Documents/TCC2_backup_antes_limpeza_20261011.bundle`). Todos os commits anteriores a essa data mudaram de código; hashes citados em DIVERGENCIAS e notas antigas seguem os códigos velhos. `..._SP_v33.docx` = a mesma com tudo aceito.
- `..._SP_v34_revisado.docx` = v33 aceito + Apêndice A: parágrafo da programação em par (decisão do autor), percentuais **provisórios** da IA no Quadro 19 (o autor vai repreencher) e início do uso em 21/09/2026. `..._SP_v34.docx` = a mesma com tudo aceito; **editada pelo autor no Word** (percentuais do Quadro 19 definitivos do autor).
- `..._SP_v35_revisado.docx` = v34 do autor + início do uso de IA em **13/09/2026** e Quadro 20 ajustado à largura da página (grade 1900/3000/4171, layout fixo, cabeçalho repetido; sem marca de revisão na formatação). `..._SP_v35.docx` = a mesma com tudo aceito.
- `..._SP_v36_revisado.docx` = v35 aceito + **fotos do nó de bancada** com marcações numeradas (`Codigo/figuras/fotos_marcadas.py`, originais em `Docs/Fotos`): **Figura 1** nó montado (3.4), **Figura 2** interior do anteparo (3.4.3), **Figura 6** vista posterior no novo **Apêndice C**; as antigas Figuras 1, 2 e 3 viram **3, 4 e 5** (arquitetura, sequência, ER); legendas das figuras acima da imagem (NBR 14724), movidas sem marca de revisão. `..._SP_v36.docx` = a mesma com tudo aceito.
- `..._SP_v37.docx` = v36 com as fotos marcadas trocadas (item 10 = papel difusor nas Figuras 1 e 2); sem mudança de texto, por isso o `_v37_revisado.docx` é idêntico.
- `..._SP_v38_revisado.docx` = v37 aceito + **estado do nó antes do comando na telemetria** (DIVERGENCIAS 74, migração 010: `nivel_antes`, `lux_antes`): Quadros 14, 16 e 17, passo (8) e nota no exemplo de 3.12.6.3, parágrafo em 3.13.2; Figuras 4 e 5 regeradas (sem marca de revisão nas imagens). `..._SP_v38.docx` = a mesma com tudo aceito.
- `..._SP_v39_revisado.docx` = v38 aceito + teste de bancada de 10/10/2026, 16h (DIVERGENCIAS 74) em 3.12.9: volume 0 → 0,625 (degrau 1,5: de dia o relógio conta como início da noite, R5 + R7), ocorrência → pleno, telemetria com `nivel_antes` 0,625 e `lux_antes` 6,79; linha nova no Quadro 20 (`bancada/teste_estado_antes.py`, 3f94fe4). `..._SP_v39.docx` = a mesma com tudo aceito.
- `..._SP_v40_revisado.docx` = v39 aceito + teste refeito depois de a caixa mexer: conferência reprovada (+9,8 % a +11,0 %), **recalibração sessão 115** (duty 10 lx = 2462, 5 lx = 1275), telemetria com `lux_antes` 6,23 (−0,3 %) e 9,96 lux no pleno; Quadro 20 com a03a21f. `..._SP_v40.docx` = a mesma com tudo aceito.
- `..._SP_v41_revisado.docx` = v40 aceito + **capturas do painel** (10/10/2026, dados da VM; `Docs/Fotos/painel_*.jpg`) no fim de 3.12.6.3: **Figura 5** monitoramento e **Figura 6** decisão explicada (R5 + R7, 0,625, sem telemetria porque o alvo não mudou), com parágrafo de apresentação; o ER passa a **Figura 7** e a foto posterior a **Figura 8**; Quadro 19 diz "Figuras 3, 4 e 7". `..._SP_v41.docx` = a mesma com tudo aceito; **editada pelo autor** (marca-texto amarelo retirado).
- `..._SP_v42_revisado.docx` = v41 do autor + **Figuras 7 (consumo estimado) e 8 (registro de decisões, diagnóstico e publicações)** do painel no fim de 3.12.6.3, com parágrafo; ER = **Figura 9**, foto posterior = **Figura 10**; Quadro 19 "Figuras 3, 4 e 9". `..._SP_v42.docx` = a mesma com tudo aceito.
- `..._SP_v43_revisado.docx` = v42 aceito + item 1 do levantamento final: **3.12.1** (5 partes interessadas; elicitação só documental, declarada como limitação), **3.12.2** (iterativo e incremental guiado pela especificação; Vitor = software e montagem, Bruno e Lucas = documentação e apoio à pesquisa), **3.12.5** com o **diagrama de casos de uso = Figura 3** (`Codigo/figuras/figura_casos_uso.py`), **3.12.8** cronograma em lista pelas datas do git (transição de tema 16/08). Figuras 3–10 viram **4–11** (arquitetura 4, sequência 5, painel 6–9, ER 10, foto posterior 11); Quadro 19 "Figuras 3, 4, 5 e 10". `..._SP_v43.docx` = a mesma com tudo aceito.
- `..._SP_v44_revisado.docx` = v43 aceito + item novo em **5.3** (logo após o da integração com o Smart Sampa): requisitos elicitados só de fontes documentais (decisão do autor, C51 b). `..._SP_v44.docx` = a mesma com tudo aceito.
- `..._SP_v45_revisado.docx` = v44 aceito + operador ligado a "Diagnosticar o ponto de luz" na Figura 3 e "recebe os alertas do diagnóstico" em 3.12.5; leva também a edição do autor na v43 (amarelo retirado do parágrafo do Quadro 17). `..._SP_v45.docx` = a mesma com tudo aceito.
- `..._SP_v46_revisado.docx` = v45 aceito + **Capítulo 5 e abertura do Capítulo 6** redigidos pela IA pelo roteiro aprovado pelo autor: 5.1 (H1 aceita com ressalva, H2 aceita, H3 rejeitada), 5.2 (4 padrões, 4 anomalias, literatura: Pasolini, Buyukkinaci, Dizon, Pickering/Rudin, Nogueira, lacuna 2.9), 5.4 (município, limites da proposta, área), Cap. 6 (objetivo geral e a)–i) atingidos, hipóteses). Só faltam Resumo e Abstract. `..._SP_v46.docx` = a mesma com tudo aceito.
- `..._SP_v47_revisado.docx` = v46 aceito + **economia ante o fluxo pleno afirmada** (pedido do autor) em 5.4 e na abertura do Cap. 6: 24,3 % suíte, 37,6 % noites reais, 24,1 % bancada; a ressalva fica só ante o horário fixo. `..._SP_v47.docx` = a mesma com tudo aceito.
- `..._SP_v48_revisado.docx` = v47 aceito + **Resumo e Abstract** (aprovados pelo autor) e **todo o marca-texto amarelo retirado** (21 trechos; sem marca de revisão). Não há mais [PENDENTE]; falta só o preenchimento do Apêndice A pelos autores, fora do repositório. `..._SP_v48.docx` = a mesma com tudo aceito; **salva pelo autor no Word** (aceita e com F9).
- `..._SP_v49.docx` = v48 do autor com as **legendas em campo SEQ** (35: 20 quadros, 11 figuras, 4 tabelas) e as **Listas de quadros, figuras e tabelas como índices automáticos** (campo TOC \c; estilo Índice de ilustrações com tabulação pontilhada em 16 cm), gerada pelo próprio Word (`listas_auto.ps1`); F9 atualiza números e páginas. Sem mudança de texto: o `_v49_revisado.docx` é idêntico.
- `..._SP_v50.docx` = v49 com o estilo **Título 4** (3.12.6.1–3.12.6.3) em negrito e preto, como o Título 3 (estava no padrão do Word: azul e itálico); Título 5 sem o azul. Só estilo: `_v50_revisado.docx` idêntico. **Legenda nova: usar Referências > Inserir legenda** (rótulos Quadro, Figura, Tabela), senão ela não entra na lista. **Calibração vigente do nó: sessão 115** (o texto de 3.4.4 e os CT15–CT20 seguem a sessão 113, usada naquela sessão). **Referências a seções nas entradas v2–v27 acima seguem a numeração da época.** **Não afirmar** sem fonte: telegestão em operação, parque em fluxo pleno (nem por horário fixo: a busca em fonte oficial não achou nada; decisão do autor em 10/10/2026: o texto compara com as duas linhas de base e basta), regras "da literatura".
- `..._SP_v51_revisado.docx` = v50 + **3.12.6.4 Arquitetura de referência para operação em escala** (proposta dos autores redigida pela IA, não implantada: entrada com registro de eventos por trecho, decisão replicada, verificação repetida no adaptador de telegestão, previsão fora do caminho, dados em dois níveis, painel autenticado, orquestração em mais de uma zona), remissão no fim de 3.12.6.1, **limitação nova em 5.3** (VM única da camada gratuita escolhida pelo custo, ponto único de falha) e recomendação em 6.1 (REVISAR C54). `..._SP_v51.docx` = a mesma com tudo aceito.
- `..._SP_v52_revisado.docx` = v51 aceito + **nomes de produtos na 3.12.6.4** (Kong, Kafka, Redis, MLflow, PostgreSQL gerenciado + TimescaleDB, Keycloak/OpenID Connect, Kubernetes, Vault, OpenTelemetry/Prometheus/Grafana), como exemplos e base para estimar custo (C54). `..._SP_v52.docx` = a mesma com tudo aceito.
- `..._SP_v53_revisado.docx` = v52 aceito + **Apêndice D com o Quadro 21**: custo mensal da arquitetura de referência na AWS São Paulo, preços sob demanda da AWS Price List de 10/10/2026, **~US$ 2.976/mês** (`Codigo/custo/estimativa_aws.py`; dimensionamento da IA, C55); 3.12.6.4 e 6.1 remetem a ele; referência AMAZON WEB SERVICES (2026). Quadro 21 no apêndice para não renumerar os Quadros 15–20. `..._SP_v53.docx` = a mesma com tudo aceito; **editada pelo autor no Word** (Apêndice A: percentuais do Quadro 19 com descrição da intervenção).
- `..._SP_v54_revisado.docx` = v53 do autor + ajustes do Apêndice A: parágrafo que define o percentual do Quadro 19, Figura 3 (casos de uso) na linha dos diagramas, espaço em "100% —" e término do uso de IA em **10/10/2026**. Ainda faltam no Quadro 19 as linhas do Cap. 5/6, Resumo/Abstract, 3.12.x, 3.12.6.4/Apêndice D e fotos/painel. `..._SP_v54.docx` = a mesma com tudo aceito.
- `..._SP_v55_revisado.docx` = v54 + **seis linhas novas no Quadro 19** (Cap. 2 redação de trechos — opção B do autor; 3.12.1/.2/.5/.8; 3.12.6.4 e Apêndice D; 5.1/5.2/5.4 e abertura do Cap. 6; Resumo e Abstract; Figuras 1, 2, 6–9 e 11), **percentual em branco** para os autores preencherem após a conferência manual (C56). `..._SP_v55.docx` = a mesma com tudo aceito.
- `..._SP_v56_revisado.docx` = v55 + **conclusão do Cap. 6 em seis sentenças** (ideias e redação-base do autor, condensadas e corrigidas pela IA; classe de pedestres P3→P5 explícita; sem informação nova, conforme o roteiro) e **três recomendações novas em 6.1** (classes adicionais, meteorologia como terceira restrição, mais variáveis e o teste da inferência nebulosa) (C57). `..._SP_v56.docx` = a mesma com tudo aceito. **O autor considera a conclusão texto seu** (a IA só resumiu e corrigiu fatos do rascunho dele).
- `..._SP_v57_revisado.docx` = v56 + classe de pedestres explícita na primeira frase da proposta do **Resumo** ("para a iluminação de vias de pedestres") e do **Abstract** ("for pedestrian street lighting"). `..._SP_v57.docx` = a mesma com tudo aceito; **editada pelo autor no Word** (percentuais das seis linhas novas do Quadro 19 preenchidos).
- `..._SP_v58_revisado.docx` = v57 do autor + Quadro 19: capturas do painel atribuídas à ferramenta ("fotos dos autores e capturas do painel do protótipo… conferidos pelos autores") e espaço sobrando retirado; término do uso de IA mantido em 10/10/2026 (data da entrega, decisão do autor). Conversas do Claude Code exportadas em `Documents/Arquivo_prompts_IA_TCC2_20261010.zip` (fora do repositório). `..._SP_v58.docx` = a mesma com tudo aceito.
- `..._SP_v59_revisado.docx` = v58 + correções da checagem contra o roteiro do orientador (`CHECAGEM_ROTEIRO.md`): "A/na Tabela", GALIČ, 3.12 sem "o roteiro", justificativa do processo em 3.12.2, 262 testes em 10/10 em 3.12.9, 4.4 e 4.6 sem interpretação (leitura pelo critério), parágrafo de trabalhos em sequência no fim de 5.4, objetivos a) e b) na conclusão, lacuna e hipóteses no Resumo/Abstract (C58). Pendente do autor: autor de metodologia em 3.1 e decisão sobre a bibliografia. `..._SP_v59.docx` = a mesma com tudo aceito.
- `..._SP_v60_revisado.docx` = v59 + **Wazlawick (2009)** em 3.1 (livro lido pelo autor e recomendado pelo orientador: pesquisa empírica, estilo "apresentação de algo presumivelmente melhor", hipótese como centro) e nas Referências; seção nova **BIBLIOGRAFIA CONSULTADA** depois das Referências, com 10 documentações de ferramentas (Docker Compose, Mosquitto, ESP32 Arduino Core, FastAPI, React, PostgreSQL 16, Python 3.12, scikit-fuzzy, Tailwind, XGBoost), títulos conferidos nos sites em 10/10/2026; autor-data mantido (decisão do autor) (C59). `..._SP_v60.docx` = a mesma com tudo aceito; **salva pelo autor com F9** (sumário e listas atualizados). Segunda checagem contra o roteiro em `CHECAGEM_ROTEIRO.md`: todos os itens atendidos; ressalvas só no tamanho do Resumo (289 palavras) e no autor-data (decisão do autor).
- `..._SP_v61_revisado.docx` = v60 + **arquitetura de referência corrigida para escala** (`VALIDACAO_ARQUITETURA.md`, plano `PLANO_GRUPOS_E_ESCALA.md`): 3.12.6.4 com **grupo de controle** (postes com o mesmo conjunto de trechos; não muda nenhum nível; Jardim Helena: 34 postes → 17 grupos), coberturas atual e total (170/730 publ./s; 850/3.700 decisões/s poste a poste), segundo estágio por grupo, hora do evento, janela por grupo, previsão por trecho em lote, comando em grupo só na mudança, **failsafe de campo = agenda residente** (proposta, não ensaiada), retomada escalonada, decisões em série temporal (completas só as que mudam), backup em outra região e **células** por município (Brasil ~22 mi pontos); 5.3 com limitação nova (capacidades da telegestão não avaliadas); Apêndice D coerente (decisões no TimescaleDB, RDS só cadastro, 12 vCPU bastam por grupo; total inalterado) (C60). `..._SP_v61.docx` = a mesma com tudo aceito (**a mais recente**; F9). Ferramentas de edição do .docx agora versionadas em `ferramentas_docx/` (tc.py, aceitar.py, zipar2.py, dump.py, rev_v61.py).
- Novas mudanças no texto: com controle de alterações, sobre a versão com tudo aceito, salvando como arquivo novo (nunca sobrescrever a versão vigente).

> O arquivo antigo `TCC_Iluminacao_Adaptativa_SP_7.docx` está **obsoleto**: a numeração de seções e quadros mudou. Referências a "7.x", "Capítulo 8" ou "Quadro 13 = interfaces" em código, comentários, `DIVERGENCIAS_TCC.txt` e `LACUNAS_TCC.txt` seguem a numeração antiga e devem ser atualizadas para a tabela abaixo quando forem tocadas.

Seções mais importantes da versão vigente (numeração da v28):

| Assunto | Seção nova | (antiga) |
|---|---|---|
| Requisitos normativos (NBR 5101, 6.10) | 2.5 | — |
| Previsão: por que gradient boosting (XGBoost, Chen e Guestrin) | 2.7 | — |
| Hipóteses H1, H2, H3 | 2.10 | — |
| Arquitetura e por que a decisão fica fora do nó e fora do Smart Sampa | 3.2 | 7.2 |
| Protótipo × implantação (Quadros 2 e 3) | 3.3 | — |
| Nó de bancada (Quadros 4, 5, 6) | 3.4 a 3.4.4 | 7.3 |
| Funções de diagnóstico | 3.4.5 | 7.3.5 |
| Dados urbanos e cenários | 3.5 / 3.5.1 | — |
| **Publicação por trecho e identificação espacial** | **3.5.2** | nova |
| **Especificação da interface de integração (Quadro 18)** | **4.4** | nova |
| Previsão (Melbourne, avaliação contra persistência e média sazonal) | 3.6 | 7.5 |
| Inferência Mamdani + verificação normativa + failsafe (Quadro 7) | 3.7 | 7.6 |
| Classe P3/P5 (Quadro 8) | 3.8 | 7.7 |
| Etapas 3 a 7 da avaliação e envelope esperado | 3.9 | — |
| Dados pessoais (RNF08) | 3.10 | — |
| **Energia e linhas de base (Quadro 9, fórmula fechada)** | **3.11** | nova |
| Engenharia de software (subseção da Metodologia, pelo roteiro) | 3.12 | Cap. 4 até a v27 |
| RF (Quadro 10) · RNF (Quadro 11) | 3.12.3 · 3.12.4 | Quadros 11 e 12 |
| Decisões de arquitetura (Quadro 12) · Componentes (Quadro 13) | 3.12.6 | Quadros 9 e 10 |
| Implantação em nuvem | 3.12.6.1 | 7.2.1 |
| Contratos das interfaces (Quadro 14) | 3.12.6.2 | Quadro 13 |
| **Percurso de uma decisão (Figura 5; 4 na v36–v42; 2 até a v35: diagrama de sequência; exemplo real)** | **3.12.6.3** | nova |
| Banco: entidades (Quadro 16), ER (Figura 10; 9 na v42; 7 na v41; 5 na v36–v40; 3 até a v35) e modelo físico | 3.13.1 · 3.13.2 · 3.13.3 | 8.5 |
| Modelo físico (Quadro 17) | 3.13.3 | — |
| Casos de teste CT01–CT20 (Quadro 15) · resultado (CT15–CT20 satisfeitos) | 3.12.7 / 3.12.9 | — |
| Resultados · Análise (limitações em 5.3) · Conclusões e recomendações (6.1) | Cap. 4 · Cap. 5 · Cap. 6 | Caps. 5, 6 e 7 até a v27 |
| **Avaliação dos componentes de IA (Tabelas 3 e 4; Quadros 19 e 20 até a v31)** | **4.6** | nova |
| Matriz de uso de IA (renumerada) | Quadro 19 (21 até a v31) | Quadro 16 |
| **Reprodutibilidade (Quadro 20, 22 até a v31: programa, dados, comando e commit de cada resultado)** | **Apêndice B** | novo |

Se o código precisar divergir do TCC, **avise explicitamente** qual trecho do texto (seção/quadro da versão nova) precisa ser atualizado.

## Resumo do sistema

Fluxo: evento urbano (REST) → serviço de decisão [previsão → inferência nebulosa Mamdani → camada de verificação normativa] → comando via MQTT → ESP32 aplica PWM na fita LED e mede lux (BH1750) → telemetria via MQTT → banco → painel.

- **Saída da decisão = fração do fluxo pleno, adimensional** (1,0 = 10 lux, classe P3). Piso = P5 = 5 lux = 0,5. O serviço **nunca** emite duty, tensão ou lux — quem converte nível em duty é o nó, via tabela de calibração medida (3.3).
- **Camada de verificação** (invariante de segurança, sempre no caminho do comando; nenhum caminho da inferência chega ao nó sem passar por ela):
  1. piso: nível emitido ≥ piso da classe mínima de dimerização (lido do banco);
  2. taxa: **decréscimo** ≤ 0,1 do pleno por minuto (elevação é livre e imediata);
  - (meteorologia **retirada** do sistema — item 49 do DIVERGENCIAS; a recomendação da NBR 5101 6.10 vira limitação declarada em 5.3.)
- **Failsafe no nó (4ª regra, autoria dos autores, RNF07):** sem comando por X segundos → nível 1,0.
- A decisão grava **nível pretendido** (inferência) e **nível emitido** (após verificação) separados, mais a restrição aplicada e a versão da base de regras.
- Parâmetros normativos ficam **em tabela** (`classe_iluminacao`), não no código (RF09).
- `decisao_id` trafega no comando e volta na telemetria, que leva também o estado do nó **antes** de aplicar o comando (`nivel_antes`, `lux_antes`, migração 010, item 74). Telemetria de decisão é **1:1** com decisão; leituras periódicas sem comando **não** vão para essa tabela (3.13.2); decisão que mantém o alvo e não gera comando não tem telemetria (1 : 0..1).
- Nenhum dado pessoal, imagem, áudio ou identificador trafega ou é salvo (RNF08, 3.10).

### Publicação por trecho e identificação espacial (3.5.2, itens 54 e 56)

- A plataforma publica, por trecho, dois tipos (`POST /eventos`, um item ou pacote de até 500):
  - **volume**: `{ocorrido_em (fim do período), tipo: "volume", pessoas_media (≥ 0), periodo_s (padrão 300), trecho, origem, vigente_ate?}` — média de pessoas na área em 5 min = **ocupação, não soma de passagens**. Vale 15 min (3 períodos, `VALIDADE_VOLUME_S`); sem volume vigente → pleno.
  - **ocorrência**: `{tipo: "ocorrencia", ocorrencia: seguranca|transito|encerrada, ...}` na hora; vale até `encerrada` ou até `vigente_ate`, o que vier primeiro; sem vigência, 15 min.
  - 5 min = tempo mínimo da rampa P3→P5 (6.10.2). Envios espalhados no período; pacote recusa só o item errado. ~170 msg/s para 50 mil câmeras (cálculo, não teste).
- Trecho = segmento de logradouro do **GeoSampa**; ponto de luz = poste do GeoSampa (placa). `trecho_ponto` N:N por distância ≤ 25 m. Por ponto: **maior volume** entre os trechos; ocorrência se **qualquer** trecho reporta.
- Recorte real: Jardim Helena (16 trechos, 36 postes). BANCADA-01 = poste IP0412418 (3 trechos); SIMULADO-02 = IP0412401.
- Na implantação, o comando iria ao código cadastral na telegestão (referência: TALQ 2.7.1); o MQTT é o meio da bancada.

### Variáveis de entrada da inferência (Quadro 7) — base vigente `v4-volume` (7 regras)

volume observado (média de 5 min ÷ referência do trecho) · movimentação prevista (próxima hora) · ocorrência reportada (categórica) · faixa horária (relógio do serviço) · classe da via (atributo do ponto de luz).
- **Saída em degraus de classe** (0 = classe da via, 1 = uma abaixo, 2 = classe mínima), convertida em fração por interpolação entre as classes **lidas de `classe_iluminacao`** (`ciclo.niveis_classe`): P3 → 1,0 / 0,75 / 0,5 (P3, P4, P5). Três degraus porque a norma admite descer no máximo duas classes. Classe sem degraus → sempre pleno.
- R1 ocorrência → classe da via; R2 observada alta → classe da via; R3 prevista alta → classe da via; R4 observada média → uma abaixo; R5 observada baixa + prevista baixa → mínima; R6 observada baixa + prevista média → uma abaixo; R7 observada baixa + início da noite → uma abaixo. **Toda regra que desce exige ocorrência = não.** Uma pessoa sozinha NÃO força o pleno (P5 já é classe de pedestres).
- Observada e prevista: baixa/média/alta, **trapezoidais**, fronteiras nos **tercis** de Melbourne (0,1038 e 0,4053). A norma não dá números para pouco/muito movimento: os dois tercis são **únicos** (todas as horas, todos os sensores reunidos), aplicados sobre o nível **normalizado por trecho**; critério dos autores (limitação em 5.3); à noite, 54 % das horas ficam na faixa baixa. Reativo = prevista ← observada. Sem volume, nenhuma regra de movimentação dispara.
- Série da previsão = média horária dos volumes ÷ referência do trecho (p99 de 28 dias, mínimo 168 h; antes, 5 pessoas); maior entre os trechos. A previsão é também "segunda evidência" contra erro de contagem.
- Regras só de origem normativa ou de literatura (nunca de decisões rotuladas pelos autores); base pequena e legível (RNF05). Cada decisão grava `entrada` (inclui `niveis_classe` e `degrau`) e `ativacoes`; `GET /eventos/{id}/explicacao` monta a cadeia para o painel.

### Previsão (3.6)

- Série horária de pedestres de **Melbourne** (registrar data de extração; janela móvel de 24 meses; zero explícito = hora sem passagem).
- Atributos: atrasos de 1, 2, 3, 24 e 168 h, médias de 3 h e 24 h, hora, dia da semana, fim de semana e feriado (sem meteorologia).
- **XGBoost** (o texto cita Chen e Guestrin, 2016 — não usar LightGBM sem avisar).
- Partição **cronológica**; métricas MAE e RMSE; comparar com **persistência** e **média sazonal** (média daquela hora naquele dia da semana). Se não superar, reportar assim mesmo.

### Diagnóstico (3.4.5, RF11)

1. **Falha total:** comando > 0 e lux ≈ iluminância residual → luminária apagada (testar desligando o ramo de 12 V).
2. **Divergência** a cada ciclo: razão lux medido / lux esperado para o comando.
3. **Alerta de perda de controle:** divergência acima da tolerância por N ciclos consecutivos. Tolerância = acima da dispersão medida no ensaio de repetibilidade (não arbitrar).
- Antes de cada sessão, medir a residual com LED desligado e subtrair; descartar sessão se residual > 5 % do valor da classe (3.4.3).

### Energia (3.11, RF12) — novo

- **Bancada:** E = Σ (potência plena do segmento × duty × Δt), com potência = 14,4 W/m × comprimento medido. Comparar com a estimativa derivada do lux medido e reportar a divergência.
- **Luminária de referência (Quadro 9):** 40 W, 90 lm/W (3.600 lm), 0–10 V, potência proporcional ao nível, consumo fixo do driver ignorado. Reportar também a **440 W** (razão idêntica).
- Por decisão, com a = nível anterior, b = novo, P em W, Δt em min:
  - atenuação: d = (a − b)/0,1; E = P × [(a + b)/2 × d + b × (Δt − d)] / 60 Wh
  - elevação: E = P × b × Δt / 60 Wh
  - se a próxima decisão chega antes do fim da rampa, integrar só o trecho percorrido.
  - Conferência: P3→P5 em 5 min a 40 W = 2,50 Wh (contra 3,33 Wh em pleno).
- **Linhas de base:** (1) fluxo pleno constante; (2) atenuação por **horário fixo** (programação agendada).
- Cada regime reporta **energia + aderência ao envelope esperado** (fração dos ciclos dentro do envelope). Nunca afirmar economia anual, de parque ou em R$.

### Hipótese H3 (atenção)

5.1 exige comparar **acionamento antecipado (com previsão) × puramente reativo** (fração da janela de baixa demanda gasta em transição). As etapas de 3.9 ainda não preveem isso: o executor de cenários deve permitir rodar a mesma suíte com a previsão ligada e desligada.

## Stack (Quadro 13)

- Python 3 + FastAPI (interface de dados urbanos / REST, JSON)
- Serviço de decisão em Python: XGBoost para previsão; scikit-fuzzy (Mamdani) para inferência; módulo próprio de verificação lendo `classe_iluminacao`
- MQTT 5.0 com TLS e credencial por dispositivo (Mosquitto)
- PostgreSQL
- Painel: Vite + React + Tailwind 4 + lucide-react, consumindo a REST (publicado na Vercel; `VITE_API_URL` no build)
- Firmware: C++/Arduino para ESP32

## Contratos (Quadro 14)

- `POST /eventos` — volume ou ocorrência do trecho, item ou pacote (ver acima); exige `X-Chave-Api` (`CHAVE_API` ou `CHAVE_DEMO`, esta pública no painel — revogar após a banca)
- `GET /eventos` — coleção filtrada por intervalo de tempo e por trecho
- `GET /trechos` — cadastro espacial (vocabulário de lugares da integração)
- `GET /eventos/{id}/explicacao` — cadeia da decisão para o painel
- `GET /decisoes` — nível pretendido, nível emitido, restrição aplicada, versão da base de regras, entrada e ativações
- `GET /telemetria` — duty aplicado e lux medido, por ponto de luz
- MQTT `iluminacao/{ponto}/comando` — nível (fração do pleno) + `decisao_id`
- MQTT `iluminacao/{ponto}/telemetria` — duty aplicado + lux + nível + `nivel_antes`/`lux_antes` (estado quando o comando chegou) + `decisao_id`

## Banco (Quadro 16 + 3.13.2)

`classe_iluminacao`, `ponto_de_luz` (com placa e UTM), `trecho_via`, `trecho_ponto`, `evento_urbano` (tipo volume|ocorrencia, pessoas_media, periodo_s, ocorrência, trecho obrigatório), `versao_base_regras`, `decisao`, `telemetria` **e a tabela associativa `decisao` ↔ `evento_urbano` (N:N)** — registra em quais eventos cada decisão se apoiou. Reclassificação de via = registro novo, nunca UPDATE do existente. A seção 3.13.3 (Quadro 17) foi escrita a partir do `schema.sql`: mudança no schema exige atualizar o Quadro 17 (e a Figura 3, o diagrama entidade-relacionamento, gerada por script a partir do schema; até a v10 ela era a Figura 2).

Entidades acrescentadas pelo código (item 16 do `DIVERGENCIAS_TCC.txt`): `versao_modelo_previsao` (RNF04), `execucao_cenario` (RF10, 3.11, H3: regime + modo antecipado/reativo), `sessao_medicao` (residual, descarte 5 %), `calibracao` (duty × lux por série; origem da tabela do firmware), `alerta_diagnostico` (RF11), `luminaria_referencia` (Quadro 9). A view `auditoria_decisao` dá a razão entregue/esperado e a latência evento → telemetria.

Decisões já tomadas: luminária de referência **em tabela**; calibração **no banco, com cópia gravada no firmware**.

## Requisitos para lembrar (Quadros 10 e 11)

- RF01–RF12 (RF11 diagnóstico, RF12 energia).
- RNF01 zero violações de piso · RNF02 taxa ≤ 0,1/min · **RNF03 evento → duty aplicado no nó < 2 s** · RNF04 decisão reconstituível (reexecutar e comparar) · RNF05 regras legíveis · RNF06 TLS + credencial por nó, recusa sem credencial · RNF07 failsafe · RNF08 sem dado pessoal · **RNF09 novo nó sem alterar o serviço de decisão**.

## Implantação (decisão do autor)

Tudo sobe em **Docker (docker compose) numa VM da Oracle Cloud (Always Free)**: API de eventos, serviço de decisão (worker sempre ligado), Mosquitto com TLS, PostgreSQL e painel. O ESP32 conecta pela internet ao Mosquitto da VM (porta 8883).

> Já refletido na v2 (4.6.1 e Quadros 12 e 13): máquina virtual com contêineres, PostgreSQL em contêiner, painel estático na Vercel, nó em MQTT 3.1.1.

## Estrutura (dentro de `Codigo/`)

```
db/            schema.sql, seed.sql (classes P3–P6 do Quadro 8)
api_eventos/   FastAPI
decisao/       previsao.py, inferencia.py, verificacao.py, ciclo.py, mqtt.py, diagnostico.py, energia.py
painel/        HTML/CSS/JS (React)
firmware/      ESP32
broker/        configuração do Mosquitto (TLS, senhas/ACL por dispositivo)
cenarios/      suíte de cenários JSON + envelope esperado + executor (RF10), com modo reativo × antecipado
modelo/        notebook de treino (Melbourne) → modelo salvo
tests/         testes de RNF01, RNF02, RNF04...
docker-compose.yml
```

## Ordem de desenvolvimento combinada

1. `db/schema.sql` + `seed.sql` ✅ (revisado no passo 0 para a versão nova do TCC)
2. `decisao/verificacao.py` + testes aleatórios (100 mil casos, zero violações de piso e taxa) ✅
3. Inferência Mamdani com partições provisórias ✅ (`decisao/inferencia.py` + `decisao/regras/v0-provisoria.toml`; saída 0–1, atenuação condicionada à ausência de risco, reativo = prevista ← observada; itens 18–20 do DIVERGENCIAS)
4. API de eventos ✅ (`api_eventos/`: vocabulário fechado, extras → 422, sem autenticação por decisão do autor — reavaliar no deploy; datas voltam em UTC, o ciclo converte para America/Sao_Paulo)
5. `ciclo.py` com previsão provisória (persistência) publicando no Mosquitto local ✅ (`decisao/ciclo.py`, `servico.py`, `simulador/no_simulado.py`; evento acorda o ciclo via pg_notify; itens 23–27 do DIVERGENCIAS)
6. Firmware com MQTT/TLS, PWM calibrado e failsafe → **fluxo completo funcionando** — ✅ firmware testado com o ESP32 real (`firmware/no/no.ino`, calibração da sessão 72): fluxo completo, rampa de 5,21 min, falha induzida detectada; **falta: failsafe partindo do piso e latência com repetições**; nó em MQTT 3.1.1 (itens 45–47 do DIVERGENCIAS). Conferência antes de usar: `python -m bancada.conferir` (~1 min; o firmware do nó entra em modo manutenção pela serial, confere residual e os três níveis com a tolerância do diagnóstico e, se reprovar, recalibra e grava a tabela na memória do ESP32 sem recompilar; item 65)
6b. Logs ✅ (18/10/2026, DIVERGENCIAS 75): API com X-Request-ID, 401/422/aceitos/erros e bancada; decisão com `decisao_id` e motivo (`evento=ID`); logs dos contêineres limitados a 5 × 10 MB; 267 testes. Falta: frase em 3.12.6.1/5.3 e atualizar a VM.
7. Painel ✅ (`painel/`: Vite + React + Tailwind 4 + lucide; só leitura, atualiza a cada 2 s; **vai para a Vercel**, não para a VM; API ganhou CORS e os endpoints `/pontos` e `/alertas`; itens 37–38 do DIVERGENCIAS)
8. Treino do modelo XGBoost (Etapa 3) e troca da previsão provisória ✅ (`modelo/baixar_dados.py` + `treinar.py`; MAE 0,0468 × 0,0572 sazonal × 0,0811 persistência; tercis reais 0,1038 e 0,4053 → `decisao/regras/v1-tercis.toml`; itens 30–32 do DIVERGENCIAS)
9. Cenários (RF10, com modo reativo), diagnóstico (RF11), energia (RF12) ✅ (`cenarios/` 10 cenários com relógio virtual; `decisao/diagnostico.py`; `decisao/energia.py`; **zero violações em 26.880 decisões**; adaptativo = 67 % do pleno e 93 % do horário fixo; **H3 não confirmada**: antecipado 21,2 % × reativo 11,4 % da janela em transição; itens 33–36 do DIVERGENCIAS)
10. Deploy na VM Oracle com Docker ✅ (`docker-compose.prod.yml`, `deploy/ROTEIRO.md`; VM ARM Ubuntu 24.04, DuckDNS `tcc-iluminacao-publica.duckdns.org` + Caddy, MQTT TLS com CA própria na 8883, ACL por ponto, chave `X-Chave-Api` no POST; painel na Vercel; ESP32 ligado à VM; item 53). Migrações num banco existente: 003 → `seed_cadastro.sql` → 004 → 005 → 006 (backup antes; **nunca** `down -v` na VM). **VM em 04/10/2026:** 006 aplicada (backup `~/backup_antes_006_2026-10-04.sql`, 71 MB) e código dos endpoints `/bancada` no ar (POST sem chave → 401)
11. Identificação espacial e base por presença ✅ (substituída pela v4 no passo 12) (itens 54 e 55: `cadastro/`, base `v3-presenca`, modal "simular leitura" e aba "decisões explicadas" no painel). Suíte v3: **zero violações**; 72,1 % do pleno e **101,8 % do horário fixo** (gasta mais que a programação horária: não prometer economia sobre ela); **H3 não confirmada** (antecipado 38,8 % × reativo 19,3 %); degraus = Mamdani; aderência 100 % com envelopes largos
12. Volume de 5 min, degraus de classe e pacote ✅ (item 56: base `v4-volume`, migração 006, Quadro 18 da especificação da interface). Suíte v4: **zero violações em 53.760 decisões**; 72,5 % do pleno e **102,1 % do horário fixo** (valor após a correção de fuso do item 58) (não prometer economia sobre ele); **H3 não confirmada** (antecipado 53,9 % × reativo 52,8 %); Mamdani ≈ degraus em energia, difere só na forma da resposta na fronteira
13. Avaliação das IAs ✅ (itens 57 a 60; protocolos fixados antes em `cenarios/avaliacao_ia/` e `modelo/PROTOCOLO_ZURIQUE.md`). **Retirar as regras** (voltar ao horário fixo) custa luz: fixo ≥ 2 lux abaixo do pedido em 278 min (suíte) e 529 min (8 noites reais de Melbourne), adaptativo nunca; noites reais = 87,0 % do fixo. **Retirar a previsão** custa luz com a contagem falhando no início da noite (0,153 × 0,280). **Substitutos simples:** com a série horária, a média sazonal iguala o XGBoost no sistema, e a tabela em degraus iguala o Mamdani (menos variação e saltos, mais inversões) — declarar assim, sem maquiar. **Zurique (15 min, experimento separado):** XGBoost supera a melhor referência simples (faixa +4,0 pp, F1 +0,044; 11 de 12 pontos) e é substituível com os mesmos dados por hora. O horário fixo é avaliado no fuso local (item 58)
14. Mudanças perceptíveis ✅ (item 61; `PROTOCOLO_SUAVIDADE.md`): em 8 noites reais de Zurique (15 min), o Mamdani teve **mais** mudanças perceptíveis que a tabela e que a tabela com histerese de descida (7 × 4 × 4 a 15 %; 24 × 5 × 5 a 6 %), com a mesma energia. A pertinência nebulosa é substituível em todos os confrontos; a vantagem só apareceu no ruído sintético do item 59. Não propor novos testes para "salvar" o fuzzy. `ciclo.decidir` tem `filtro_observada` opcional, usado só pela avaliação
15. Resultados no texto ✅ parcial (item 62, v10): 5.2 (667.200 decisões verificadas, zero violações), 5.4 e 5.5 com a aderência dos três regimes (`cenarios/aderencia_regimes.py`: adaptativo 100 %, pleno 58,0 %, horário fixo 72,2 %)
16. **Falta:** sessão final de bancada (CT15–CT20: calibração, failsafe do piso, latência ~30 repetições, recusa sem credencial, segundo nó), 5.3 e energia de bancada em 5.5, 6.1, 6.2, 6.4, Capítulo 7, Resumo e Abstract (dependem da bancada e da resposta do orientador sobre o papel da inferência nebulosa), 4.1, 4.2, 4.5 e 4.9 (dependem de informação do autor); situação das lacunas em `Codigo/LACUNAS_TCC.txt`

## Coleta por minuto de Melbourne (item 67)

Na VM, `~/coleta_melbourne/` (fora do repositório e dos contêineres): cron a cada hora roda `coletar_melbourne_minuto.py` (cópia de `Codigo/modelo/`), que guarda `dados/AAAA-MM-DD.csv` e `coletas.log`. Começou em 06/10/2026. Uso previsto: experimento em 5 min para a avaliação de novembro, com protocolo fixado antes. Para conferir: `tail ~/coleta_melbourne/dados/coletas.log`.

## Decisões em aberto (perguntar ao autor antes de assumir)

- Confirmado pelo autor: passo da rampa de 5 s, failsafe de 15 s, raio de 25 m, um trecho por publicação, decisão por **volume** (não por presença), volume a cada 5 min válido 15 min, ocorrência na hora (encerrada ou prazo), pacote aceito, níveis = classes da norma. Rejeitado pelo autor (complexo demais): campos de qualidade da leitura/condição adversa e detecção de contagem suspeita — fica como limitação em 5.3.


## Hardware atual (já montado e testado)

- ESP32 DevKit 38 pinos na protoboard de 830 pontos, **USB para cima** (as legendas ficam embaixo da placa).
- BH1750 (GY-302) soldado: SDA = GPIO21, SCL = GPIO22, VCC = 3V3, endereço 0x23. Houve mau contato por solda, já resolvido.
- Módulo MOSFET D4184: TRIG/PWM = GPIO25, GND comum com o ESP32; VIN = fonte 12 V; OUT = fita LED 5050 branca de 12 V (uma cor, 2 fios).
- Na Arduino IDE, placa "DOIT ESP32 DEVKIT V1", porta COM3, core esp32 3.3.x (usa `ledcAttach` / `ledcWrite(pino, valor)`).
- Já funciona um sketch com fade de gama 2.2, PWM de 5 kHz/12 bits e leitura de lux simultânea (sem `delay` no fade).
- Pontos do TCC: PWM de 5 kHz/12 bits; comprimento do segmento ajustado até o duty pleno dar 1,5×–2× 10 lux; os duties de 10 lux e 5 lux devem ser **medidos na bancada**, não interpolados; BH1750 em modo de alta resolução 2.

## Regras para o Claude Code

- Rode os testes depois de mexer em `verificacao.py`; a camada de verificação nunca pode ter violação.
- Não coloque valores normativos fixos no código; leia do banco.
- Commits pequenos, com mensagem em português.
- **Declaração de uso de IA (Apêndice A, item 2):** o corpo teórico, a análise crítica, a inferência empírica e as conclusões precisam ser dos autores. Sempre que a IA propuser, calcular ou redigir algo desse tipo — um critério ou limiar que não vem de norma, o desenho de um experimento, uma interpretação de resultado, uma conclusão, uma justificativa de decisão de projeto ou uma fonte nova —, **acrescente um item em `REVISAR_ANTES_DE_SUBMETER.txt`** (raiz do TCC2), dizendo o que é, onde está no texto e o que o autor deve conferir. Não marque itens como revisados: só o autor marca.
- No Quadro 19 (matriz de uso de IA; Quadro 21 até a v31), todas as linhas citam **Claude Opus 5 e Claude Opus 5.5** juntos, por decisão do autor (sem separar por data).
