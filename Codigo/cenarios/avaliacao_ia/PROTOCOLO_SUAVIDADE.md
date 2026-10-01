# Protocolo: inferência nebulosa × tabela em mudanças perceptíveis (DIVERGENCIAS 61)

Fixado **antes** de qualquer execução. O resultado é reportado como vier.

**Pergunta:** com contagem real de resolução sub-horária, a inferência nebulosa
produz menos mudanças de luz **perceptíveis** que alternativas simples, sem perder
em energia nem em luz entregue?

Motivação: nos testes anteriores (itens 57 e 59) a série real era horária (o
volume de 5 min repetia o valor da hora) e a métrica de inversões contava igual um
ajuste de 0,2 lux e um salto de 2,5 lux.

## Cenários (`suavidade/`, gerados por `gerar_suavidade.py`)

- Série de Zurique de 15 min (a mesma do item 60, mesmo arquivo e mesma
  normalização: contagem ÷ percentil 99 do ponto no treino, limitada a 1).
- 8 noites reais (18h–06h) de 2019, o ano de teste do item 60: 4 pontos sorteados
  com semente 61 entre os 12 com dados no teste — 2 da metade mais movimentada à
  noite e 2 da menos —, cada um com uma noite de segunda a quinta e uma de sábado.
- Histórico: as 168 horas reais anteriores (média horária do nível de 15 min).
- Volume publicado a cada 5 min com o valor do intervalo de 15 min corrente.

## Concorrentes (todos com a previsão do modelo em operação, base v4-volume)

1. **Inferência nebulosa** (Mamdani), como no sistema.
2. **Tabela em degraus**: a mesma base, corte seco no tercil.
3. **Tabela com histerese de descida**: sobe de faixa no tercil, na hora; só desce
   quando o volume cai 0,05 abaixo do tercil (a mesma meia rampa da base nebulosa).
   É a correção simples que um projetista aplicaria à tabela, sem lógica nebulosa.

## Métricas

- **Principal — mudanças perceptíveis:** número de passos do ciclo (5 s) em que o
  nível emitido varia, em relação ao nível anterior, ao menos **15 %** (limiar em
  que metade das pessoas detecta a variação; Akashi e Neches, 2004) e, como limiar
  rigoroso, ao menos **6 %** (Shikakura, Morikawa e Nakamura, 2003). Os limiares
  vêm de estudos em escritório; não há valor medido para via pública (declarado).
- **Controle:**
  - violações de piso e de taxa (esperado: zero);
  - energia em relação ao pleno;
  - minutos com o nível 0,2 do pleno (2 lux na P3) ou mais abaixo do que a situação
    pede, com o pedido calculado sobre o volume **publicado no cenário** (classe da
    via com volume alto; uma classe abaixo com volume médio), igual para os três;
  - atraso médio até a classe mínima nos episódios de baixa demanda (reportado, sem
    entrar no critério).

## Leitura

- A inferência nebulosa **não é substituível** se, no agregado das 8 noites, tiver
  ao menos **20 % menos** mudanças perceptíveis que a **melhor** das duas tabelas,
  nos **dois** limiares, com energia no máximo 2 pontos percentuais acima da dela e
  sem mais minutos 2 lux abaixo do pedido que ela.
- Caso contrário — inclusive se as três empatarem em zero —, é **substituível**.
- Os 20 % e os 2 pontos são critério dos autores, fixado antes do resultado.

Nenhum ponto, noite, limiar, concorrente ou critério é trocado depois do resultado.
