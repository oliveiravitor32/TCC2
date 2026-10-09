# Protocolo: sensibilidade da régua ao percentil (item 72)

Fixado **antes** de executar. **Teste a posteriori:** o percentil 99 já está em
uso desde o item 30 (Melbourne) e no modelo de Zurique (item 69). O teste não
escolhe o percentil; ele mede se a escolha muda o que o sistema faz. Se mudar
muito, isso é reportado e o 99 **não** é trocado por causa do resultado.

## Pergunta

Trocar o percentil 99 da régua por outro percentil alto muda a classificação do
movimento (faixas baixa, média e alta) que as regras usam?

## Dados

Série de Zurique em 15 min, com a mesma preparação do modelo principal
(`treinar_zurique.preparar()`: horário de verão, sensor travado, pontos com
cobertura). Treino até 31/12/2018 e teste em 2019, como no modelo.

## Percentis comparados

95; **99** (o usado); 99,5; 99,9. Em 28 dias (2.688 blocos), eles ficam
definidos por cerca de 134, 27, 13 e 3 blocos acima.

## Medidas

1. **Concordância de faixa com o p99.** Para cada percentil *p*: régua por ponto
   = percentil *p* do treino; nível = pessoas ÷ régua, limitado a 1; tercis
   recalculados sobre o nível do treino (eles são definidos nessa escala);
   faixa de cada bloco do teste. Concordância = fração dos blocos do teste
   com a mesma faixa que com o p99. Todos os blocos e só os noturnos (18h às
   6h).
2. **Saturação.** Fração dos blocos do teste com nível = 1.
3. **Estabilidade da régua em operação.** Para cada ponto e cada dia de 2019, a
   régua como o serviço a calcula: percentil *p* dos blocos dos 28 dias
   anteriores (mínimo de 672 blocos). Variação relativa de um dia para o
   seguinte; reporta-se a mediana e o percentil 95 entre todos os pontos e dias.
4. **Concordância de faixa em operação.** Faixa dos blocos noturnos de 2019 com
   a régua de 28 dias de cada percentil e os tercis do item 1; concordância
   com a do p99.

## Regra de leitura (critério dos autores, fixado antes)

A escolha é **pouco sensível** se a concordância noturna (medidas 1 e 4) do p95 e
do p99,5 com o p99 for de pelo menos 90 %. Abaixo disso, ela é **sensível**, e o
texto o diz. O p99,9 entra para mostrar a instabilidade (medida 3), não na
regra.

## O que não muda

O modelo de previsão não é retreinado. As regras, os tercis em uso
(0,0693 e 0,2946) e os resultados dos cenários também não mudam.

Comando: `python -m modelo.sensibilidade_percentil` → `modelo/resultados/sensibilidade_percentil.json`.
