# Protocolo: previsão com dados de 15 minutos (Zurique) — DIVERGENCIAS 60

Fixado **antes** de qualquer treino. O resultado é reportado como vier.

**Pergunta:** com dados de resolução melhor que a horária, o XGBoost supera
referências simples **nos termos da decisão** (a faixa de movimento que as regras
usam)? É um experimento separado: não altera o modelo, os tercis nem as regras do
sistema.

## Dados

- Contagem automática de pedestres e bicicletas da cidade de Zurique, valores de
  15 minutos (Open Data Zürich, licença CC0), arquivo de todos os anos baixado em
  30/09/2026. Pedestres = FUSS_IN + FUSS_OUT.
- Janela: 01/01/2016 a 31/12/2019 (período em que a rede teve mais pontos, antes
  da pandemia).
- Pontos: os que, dentro da janela, têm ao menos 730 dias entre o primeiro e o
  último registro e cobertura ≥ 95 %.
- Normalização por ponto, como em 3.6: contagem ÷ percentil 99 do ponto no treino,
  limitada a 1. Intervalo ausente não é inventado: linhas que dependem dele são
  descartadas.
- Partição cronológica: treino até 31/12/2018, teste = 2019. Os últimos 10 % do
  treino servem de validação para a parada antecipada.

## Duas resoluções, sobre os mesmos dados

1. **15 min**: alvo = nível médio dos próximos 60 minutos (4 intervalos), refeito a
   cada 15 minutos.
2. **1 hora** (os mesmos dados somados por hora, como a série de Melbourne): alvo =
   nível da próxima hora.

## Modelos

- XGBoost com os mesmos hiperparâmetros de `modelo/treinar.py`.
  - 15 min: atrasos de 1, 2, 3, 4, 8, 96 e 672 intervalos; médias de 1 h, 3 h e
    24 h; hora, quarto de hora (seno/cosseno), dia da semana, fim de semana.
  - 1 hora: atrasos de 1, 2, 3, 24 e 168 h; médias de 3 h e 24 h; mesmos atributos
    de calendário.
  - Sem atributo de feriado (calendário suíço não codificado) nas duas resoluções.
- Referências simples:
  - **persistência**: a última hora observada;
  - **média sazonal**: média do alvo no treino, por ponto, dia da semana e horário;
  - **semana anterior**: o alvo do mesmo horário sete dias antes.

## Métricas (teste; primária = noite, 18h às 06h; secundária = todas as horas)

1. MAE e RMSE.
2. **Acerto da faixa**: fração dos casos em que a faixa prevista (baixa, média,
   alta, pelos tercis do nível no treino) é a faixa real do alvo.
3. **"Vai subir"**: só nos casos em que o nível corrente está na faixa baixa.
   Positivo real = alvo fora da faixa baixa. Mede-se precisão, revocação e F1 de
   cada previsor. É a situação da regra R6 (segurar a luz antes de o movimento
   voltar).

## Leitura

- O XGBoost **não é substituível** numa resolução se, à noite, superar a melhor
  referência simples em **acerto da faixa por ≥ 2 pontos percentuais e** em **F1
  do "vai subir" por ≥ 0,02**.
- Caso contrário, é **substituível** nessa resolução.
- A resolução ajuda se a vantagem do XGBoost sobre a melhor referência for maior
  em 15 min do que em 1 hora.

Nenhum ponto, janela, atributo, métrica ou limiar é trocado depois do resultado.
