# Levantamento de perguntas e pontos de ataque (v81)

Leitura completa da v81 em 17/11/2026, da capa ao Apêndice G. Nada foi alterado no TCC.

Como ler este arquivo:
- **Onde**: a seção do texto que a banca vai usar.
- **Defesa**: a resposta curta.
- **Status**: **NOVO** quando o ponto ainda não está no `ROTEIRO_RESPOSTAS_BANCA.md`; "Roteiro n" quando já está lá (responder pelo roteiro).

---

## Parte 1. Os 10 ataques mais prováveis (estudar primeiro)

| # | Ataque | Onde | Status |
|---|---|---|---|
| 1 | "Na 5.4 vocês escrevem 'sem deixar a via abaixo do nível que a situação pede', mas a Tabela 3 mostra 97 e 195 min abaixo." | 5.4, 3º parágrafo × Tabela 3 | **NOVO** (o Roteiro 9 trata só do Resumo) |
| 2 | "Vocês citam Rudin para defender modelo interpretável e usam XGBoost, que é caixa-preta." | 2.6 × 2.7 / 3.6 | **NOVO** |
| 3 | "O nível 0,521 não é classe nenhuma da norma. O sistema inventa níveis intermediários?" | 3.7 (saída em degraus) e Figura 7 | **NOVO** |
| 4 | "Se o serviço cair durante uma ocorrência, a rua fica na classe mínima por até 15 min." | 3.4, 3.5.2, RNF07 | **NOVO** |
| 5 | "Trocaram Melbourne por Zurique depois de ver o resultado. Isso é escolher o dado que dá certo." | 3.6, último parágrafo; 5.3 | Roteiro 6, mas **reforçar** este ângulo |
| 6 | "O RNF03 era < 2 s e virou 180 s. Afrouxaram o requisito?" | Quadro 11, RNF03 | **NOVO** |
| 7 | "O CT18 falhou na primeira sessão e depois mudaram o critério." | 3.12.9, fim do 1º parágrafo | **NOVO** |
| 8 | "A previsão piorou a H3. A lógica nebulosa foi igualada por uma tabela. O que sobra de IA?" | 5.1, 4.6 | Roteiros 2 e 3 |
| 9 | "As regras R3 e R6 dizem 'Literatura: Belloni'. Belloni tem essas regras?" | Apêndice G, Quadro 22 | **NOVO** |
| 10 | "Sete de dez elos estão contratados, mas o principal, a API do Smart Sampa, não existe." | 3.3, Quadro 3 e parágrafo seguinte | **NOVO** |

---

## Parte 2. Ponto a ponto, na ordem do texto

### Resumo, Introdução e Capítulo 1

**1.1 "Mais segurança que o horário fixo" (1.4)**
- *Ataque:* segurança de quem? O trabalho não mede crime nem percepção de segurança.
- *Defesa:* "segurança" aqui é a luz exigida pela norma para a situação. O horário fixo ficou 2 lux ou mais abaixo do pedido por 343 min na suíte e 30 min sob ocorrência aberta; o adaptativo, nunca (Tabela 3). Não medimos criminalidade.
- *Status:* **NOVO**

**1.2 "Nada, em operação, liga os dois" (1.3)**
- *Ataque:* como provam que não existe?
- *Defesa:* fontes públicas (contrato, Caderno, TR) não preveem esse vínculo. Afirmamos que não está documentado, não que é impossível que exista.
- *Status:* **NOVO** (é parente do Roteiro 19)

### Capítulo 2 — Revisão

**2.1 Revisão narrativa com lacuna forte (2.1 e 2.9)**
- *Status:* Roteiro 19

**2.2 Smart Sampa: analíticos de contagem "exigidos" (2.3)**
- *Ataque:* o TR exige; está funcionando? Metade das câmeras é privada.
- *Defesa:* usamos o que o contrato exige, e a 5.3 declara que a cobertura não foi levantada.
- *Status:* Roteiro 13

**2.3 Rudin × XGBoost (2.6 e 2.7)**
- *Ataque:* defendem modelo interpretável e põem um ensemble de árvores no caminho.
- *Defesa:* o XGBoost não decide o nível; ele só estima a movimentação. Essa estimativa entra nas regras como uma faixa legível (baixa, média ou alta). A decisão continua explicável regra a regra, e a verificação independe dele. O próprio 2.7 diz "erro do modelo → decisão inadequada, nunca inadmissível".
- *Status:* **NOVO**

**2.4 Grinsztajn descarta deep learning sem testar LSTM (2.7)**
- *Defesa:* é escolha apoiada em referência revisada por pares; dentro das árvores, comparamos RF e regressão linear nos nossos dados (4.1).
- *Status:* **NOVO** (baixa probabilidade)

**2.5 Nogueira: "percepção já contratada e em operação" (2.8)**
- *Ataque:* não é exagero, se a contagem por trecho não existe?
- *Defesa:* as câmeras e os analíticos estão contratados; a publicação por trecho é o que especificamos (Quadro 18).
- *Status:* **NOVO**

### Capítulo 3 — Metodologia

**3.1 "Sete de dez elos contratados" (3.3)**
- *Ataque:* o elo "publicação do estado da via" está como "interoperabilidade exigida; interface não publicada", e é o elo de que tudo depende.
- *Defesa:* o texto não diz que ele existe. Diz que a interoperabilidade é exigida em contrato, e é por isso que especificamos a interface. É uma dependência declarada (1.3 e 5.3).
- *Status:* **NOVO**

**3.2 A bancada define 10 lux pelo próprio sensor (3.4.4)**
- *Ataque:* é circular.
- *Defesa:* sim, e de propósito. O que importa é a razão; erro de escala constante se cancela (3.4.4). Não afirmamos exatidão absoluta.
- *Status:* Roteiro 8

**3.3 Failsafe de até 15 min (3.4, 3.5.2, RNF07)**
- *Ataque:* se o serviço cair e surgir uma ocorrência, o nó fica no nível antigo até vencer a validade.
- *Defesa:*
  - o pior nível possível é a classe mínima P5, que ainda é uma classe da norma;
  - a validade acompanha a do volume (15 min); com o serviço no ar, a ocorrência sobe a luz na hora;
  - em campo, a proposta é a agenda residente (3.12.6.4).
  - Validade menor significa mais mensagens; foi escolha, não descuido.
- *Status:* **NOVO**

**3.4 Raio de 25 m e "17 de 36 postes em três ou mais trechos" (3.5.2)**
- *Ataque:* parâmetro arbitrário que muda o resultado.
- *Defesa:* está declarado como critério dos autores (5.3). O efeito é conservador: mais trechos significa mais chance de ficar no pleno, nunca menos luz. E o raio é gravado na associação e pode ser ajustado por dado.
- *Status:* **NOVO**

**3.5 Troca Melbourne → Zurique depois do resultado (3.6)**
- *Ataque:* escolheram o dado favorável.
- *Defesa:*
  - o texto declara a troca e a ordem;
  - o experimento que a justificou (Tabela 4) teve protocolo fixado antes;
  - o achado de Melbourne fica no texto;
  - o commit do protocolo é anterior ao do resultado (Quadro 20).
- *Status:* Roteiro 6 (reforçar)

**3.6 Régua inicial de 5 pessoas (3.6 e 5.3)**
- *Ataque:* número inventado.
- *Defesa:* vale só nos primeiros 7 dias de um trecho e está declarado em 5.3. Pelo lado seguro: se a referência for baixa, o nível normalizado sobe e a luz também.
- *Status:* **NOVO** (baixa probabilidade)

**3.7 XGBoost só 3,0 % melhor que a Random Forest (4.1)**
- *Ataque:* por que não a RF, que treina em metade do tempo?
- *Defesa:* a regra dos 2 % foi fixada antes do treino, e o XGBoost ganhou em 11 de 12 pontos. Ganho pequeno, declarado. A RF seria aceitável; a arquitetura troca o modelo sem mexer nas regras (RNF05).
- *Status:* **NOVO**

**3.8 "Zurique sem atributo de feriado" × "atributo feriado" (5.3 × 3.6)**
- *Ataque:* contradição.
- *Defesa:* são dois modelos diferentes. O "sem feriado" é o do experimento da Tabela 4; o modelo em operação tem feriado (3.6).
- *Status:* **NOVO** (pode confundir)

**3.9 Nível 0,521 e degrau 1,92 (3.7, Figura 7)**
- *Ataque:* a norma fala em classes, e 0,521 não é classe.
- *Defesa:*
  - a norma limita o mínimo (duas classes abaixo) e a velocidade de descida; ela não obriga parar só nos degraus;
  - qualquer nível ≥ piso é admissível, e o verificador garante isso;
  - a UNI 11248 italiana tem um modo contínuo entre classes (Pasolini, 2.8);
  - quem quiser degraus puros usa a tabela, que a 4.6 mostrou equivalente.
- *Status:* **NOVO** (provável para quem conhece a norma)

**3.10 Rampa de 0,05 corrigida para 0,017 depois do efeito observado (3.7)**
- *Ataque:* ajustaram parâmetro olhando o resultado.
- *Defesa:* foi restabelecida a regra fixada na primeira versão (um quarto da faixa mais estreita), e não um valor novo; a ordem está declarada.
- *Status:* **NOVO**

**3.11 Belloni como origem de R3 e R6 (Quadro 22)**
- *Ataque:* Belloni trata de tráfego de veículos e não escreve essas regras.
- *Defesa:* a origem citada é o princípio de antecipar a demanda, não o texto da regra. Os limiares são critério nosso (tercis), declarado em 3.7 e 5.3.
- *Status:* **NOVO** (cuidado: não dizer que "a regra é da literatura")

**3.12 Horário fixo 0 h–5 h escolhido pelos autores (3.11)**
- *Ataque:* escolheram uma linha de base conveniente.
- *Defesa:*
  - é a programação agendada que o Caderno prevê;
  - com ela o adaptativo até gasta 6,7 % mais na suíte, ou seja, não é uma base escolhida para nos favorecer;
  - não afirmamos que São Paulo usa esse horário.
- *Status:* **NOVO**

**3.13 Interpretação da taxa "1/10 do pleno por minuto" e passo de 0,008 (Quadro 6)**
- *Defesa:* 0,1 por minuto dividido por 12 passos = 0,00833; arredondado para baixo, dá 0,008, sempre do lado seguro.
- *Status:* **NOVO** (fácil)

**3.14 Elicitação só documental (3.12.1)**
- *Status:* declarado em 5.3; pergunta provável de engenharia de software. **NOVO** no roteiro.
- *Defesa:* sem acesso a operador nem concessionária; os requisitos vêm de contrato e norma, e cada um tem caso de teste.

**3.15 Cronograma termina em 10/10, mas há trabalho até novembro (3.12.8)**
- *Ataque:* o cronograma está incompleto.
- *Defesa:* depois de 10/10 vieram ajustes do texto, grupos de controle (testes de 18/10) e as recomendações do orientador. Se perguntarem, dizer isso.
- *Status:* **NOVO** (baixa probabilidade)

**3.16 RNF03: de < 2 s para 180 s (Quadro 11)**
- *Ataque:* afrouxaram o requisito.
- *Defesa:* 180 s é o prazo que o Caderno exige da telegestão (item 7.2.1), uma fonte externa em vez de um número nosso. Mesmo assim, o medido foi de 1,03 a 1,47 s, abaixo dos 2 s antigos.
- *Status:* **NOVO**

**3.17 CT18 falhou na sessão de 4–5/10 (3.12.9)**
- *Ataque:* mudaram o critério depois da falha.
- *Defesa:*
  - a mudança foi da arquitetura (comando só na mudança + validade), decidida antes da sessão de 10/10 e registrada (DIVERGENCIAS 71);
  - na arquitetura nova, o CT18 passou;
  - a falha antiga está no texto, não foi escondida.
- *Status:* **NOVO**

**3.18 RNF09 testado com nó simulado (CT20)**
- *Ataque:* o segundo nó não é físico.
- *Defesa:* o RNF09 é sobre o serviço não mudar de código. Para o serviço, um assinante simulado e um físico são idênticos (mesmo tópico, mesma credencial por ponto).
- *Status:* **NOVO**

**3.19 Painel com chave pública (3.12.6.1 e 5.3)**
- *Ataque:* qualquer pessoa pode publicar eventos na demonstração.
- *Defesa:* o pior caso é luz a mais, porque toda publicação passa pela verificação. A chave é revogada após a banca; na arquitetura de referência vira JWT por usuário.
- *Status:* **NOVO**

**3.20 Faixa horária: "de tarde conta como início da noite" (3.12.9)**
- *Ataque:* o relógio está errado?
- *Defesa:* a faixa é medida em horas desde as 18 h. Fora da noite o sistema não opera em campo (a luz fica apagada pelo fotocontrolador); o ensaio de tarde só mostrou o efeito da R7.
- *Status:* **NOVO**

### Capítulo 4 — Resultados

**4.1 667.200 passos (4.2)**
- *Status:* Roteiro 5

**4.2 "A verificação nunca corrigiu o piso" (4.2)**
- *Status:* Roteiro 4; ver também o item 4 da Preparação (caso ao vivo).
- **Atenção:** no painel não aparece "restrição: piso", porque a inferência nunca pede abaixo de 0,5. Mostrar pelo teste CT05 / `verificar`.

**4.3 Adaptativo fora do envelope: 0,556 contra máximo de 0,55 (4.4)**
- *Ataque:* o próprio sistema violou o envelope de vocês.
- *Defesa:* 0,006 acima do teto, por 5 e 15 min, acima do envelope e não abaixo: mais luz, e não menos. O piso nunca foi violado.
- *Status:* **NOVO**

**4.4 Sincronia de relógios (4.3)**
- *Ataque:* publicação com hora no futuro é descartada. Em campo, isso quebra?
- *Defesa:* a especificação pressupõe relógios sincronizados (NTP), como qualquer sistema distribuído; está declarado.
- *Status:* **NOVO**

**4.5 Nó reiniciado fica 10 min no pleno (4.3)**
- *Status:* declarado (lado seguro). **NOVO** no roteiro.

**4.6 Energia de bancada 75,9 % × fórmula 75 % (4.5)**
- *Ataque:* sem leitura de lux na rampa, não há verificação cruzada.
- *Defesa:* declarado; na sessão anterior, com leitura a cada passo, a divergência foi de 1,3 %.
- *Status:* **NOVO**

**4.7 Economia de 37,6 % sem intervalo de confiança (4.5, 5.4)**
- *Status:* Roteiro 17

**4.8 Tabela 3: a média sazonal teve menos minutos abaixo (150 × 195)**
- *Ataque:* então a média sazonal é melhor que o XGBoost no sistema?
- *Defesa:*
  - o critério fixado antes era o acerto da contenção (70,7 % × 62,4 %);
  - os 195 min estão todos a menos de 2 lux;
  - o XGBoost gasta menos energia;
  - é uma troca e está reportada como veio.
- *Status:* **NOVO**

### Capítulo 5 — Análise

**5.1 H1 aceita "com ressalva" (5.1)**
- *Status:* Roteiro 10

**5.2 H3 rejeitada e métrica que conta "uma abaixo" como transição (3.9 e 5.1)**
- *Ataque:* a métrica foi feita para rejeitar?
- *Defesa:* foi definida antes, e a ressalva está escrita em 3.9. Mesmo assim, reportamos a rejeição sem trocar a métrica.
- *Status:* Roteiro 3 (acrescentar este ângulo)

**5.3 Frase da 5.4 (ver Parte 1, item 1)**
- *Defesa a usar:* "a frase quer dizer: nunca 2 lux ou mais abaixo. O déficit existe, é de 0,8 lux em média, e está na Tabela 3, no Resumo e na 5.3."
- **Admitir** que a frase da 5.4 ficou mais forte do que o Resumo corrigido.
- *Status:* **NOVO**

**5.4 Comparação com Buyukkinaci (40 %) (5.2)**
- *Ataque:* comparam pedestre com veículo e outra norma.
- *Defesa:* a ressalva está no próprio parágrafo; é ordem de grandeza.
- *Status:* **NOVO**

**5.5 Atenuação piora a contagem (5.3)**
- *Status:* Roteiro 12

**5.6 Termo aditivo: quem são vocês para propor? (5.4)**
- *Status:* Roteiro 14

**5.7 "Transponível a outros serviços municipais" (5.4, último parágrafo antes dos desdobramentos)**
- *Ataque:* generalização sem prova.
- *Defesa:* está como indicação para a área, e não como resultado.
- *Status:* **NOVO** (baixa probabilidade)

### Capítulo 6 e apêndices

**6.1 "A previsão superou as referências" na conclusão × "substituível" (Tabela 4, Melbourne)**
- *Defesa:* no modelo em operação (Zurique, 15 min), superou. Com dado horário, não. A própria conclusão diz "só com dados de 15 min".
- *Status:* **NOVO**

**6.2 Custo de US$ 3 mil/mês sem economia em R$ para comparar (Apêndice D)**
- *Ataque:* vale a pena?
- *Defesa:* de propósito, não convertemos economia em R$ (3.11): faltaria um perfil anual real. A conta de retorno é recomendação, não resultado.
- *Status:* Roteiro 23 (reforçar)

**6.3 Quadro 19: 100 % de intervenção em quase tudo (Apêndice A)**
- *Status:* Roteiro 15. Estar pronto para dizer, com exemplo, o que cada um conferiu ou refez.

**6.4 Quadro 20 com hashes de commit (Apêndice B)**
- *Ataque:* a banca pode abrir o repositório e pedir para rodar um comando.
- *Preparo:* testar antes um comando curto, por exemplo `python -m cenarios.avaliacao_ia.deficit` ou o pytest do CT05.
- *Status:* **NOVO**

**6.5 Particionamento "testado em banco descartável" (Apêndice F)**
- *Ataque:* teste de verdade ou só criou as tabelas?
- *Defesa:* o teste conferiu quatro coisas: a gravação na partição do mês, o *pruning* da consulta de um dia, o uso da partição padrão e a retirada de um mês por DETACH/DROP. Não foi teste de carga.
- *Status:* **NOVO**

**6.6 Meteorologia fora, sendo recomendação da 6.10 (5.3 e Apêndice E)**
- *Status:* Roteiro 23

---

## Parte 3. Perguntas técnicas "de prova oral" (respostas de uma linha)

1. **O que é o Mamdani?** Regras SE–ENTÃO com conjuntos nebulosos: mínimo para o E, máximo para agregar, centroide para tirar um número.
2. **Por que trapézio?** É simples e legível, com rampa só perto do tercil (Pickering).
3. **O que é o p99?** O valor abaixo do qual ficam 99 % dos blocos de 15 min do trecho em 28 dias; vira o "1" da escala.
4. **Por que três faixas?** Porque a norma admite três classes para o ponto: a da via e até duas abaixo (6.10.2).
5. **Por que QoS 1 e sem retain no comando?** Para entregar ao menos uma vez sem fazer o nó que reconecta aplicar decisão velha; o `decisao_id` absorve duplicata.
6. **Por que a decisão fora do nó?** Muda a regra sem regravar firmware, e o nó fica simples e substituível (3.2).
7. **Por que fora do Smart Sampa?** Por três motivos:
   - LGPD por arquitetura;
   - a integração seria absorvida pela plataforma;
   - governança: quem responde pela luz precisa auditar.
8. **Como o nó converte nível em duty?** Pela tabela de calibração medida (sessão 115), com interpolação linear entre pontos medidos.
9. **O que é o grupo de controle?** Postes ligados exatamente aos mesmos trechos; recebem a mesma decisão, calculada uma vez, com resultado idêntico ao ponto a ponto.
10. **Diferença entre nível pretendido e nível emitido?** Pretendido é o que a inferência pediu; emitido é o que passou pela verificação. Gravar os dois torna a correção mensurável.

---

## Parte 4. O que vale ajustar no roteiro (sugestão, nada feito)

- **Item 4 da Preparação individual:** o caso ao vivo deve ser o CT05 / `verificar` no terminal, e não o painel; o painel não mostra "restrição: piso".
- **Respostas novas sugeridas:** acrescentar ao roteiro as da Parte 1 marcadas como **NOVO**, nesta ordem:
  - 5.4;
  - Rudin × XGBoost;
  - nível 0,521;
  - failsafe de 15 min;
  - RNF03 de 180 s;
  - CT18;
  - Belloni;
  - "7 de 10 elos".
