# Protocolo: base v6-zurique, rampa proporcional aos tercis (DIVERGENCIAS 70)

Fixado **antes** de criar a base v6 e de executar qualquer cenário com ela. Os
resultados são reportados como vierem.

## Decisão e motivo (declarados)

Decisão dos autores, tomada **depois** de ver os resultados da v5 (item 69):
com os tercis de Zurique (0,0693 e 0,2946) e a rampa fixa de ±0,05 herdada da
v4, a faixa baixa "pura" foi de 0 a 0,054 (Melbourne) para 0 a 0,019, e o
volume de rua vazia dos cenários (0,02) passou a cair na rampa: a luz ficou em
0,60 em vez de 0,50, a aderência caiu para 95,5 % e a energia da suíte subiu
para 106,6 % do horário fixo.

O ±0,05 nunca teve regra declarada. A v0 tinha: com faixas de 1/3, a rampa era
0,0833, isto é, **1/4 da largura da faixa**. A v6 restabelece essa regra.

## A regra

    meia_largura_rampa = 1/4 × (largura da faixa mais estreita)

com as faixas definidas pelos tercis f1 e f2: baixa [0, f1], média [f1, f2] e
alta [f2, 1]. Arredondada a quatro casas.

Com os tercis da v5: faixas de 0,0693, 0,2253 e 0,7054; a mais estreita é a
baixa; **meia_largura_rampa = 0,0173**.

## O que muda e o que não muda

- Muda: só `meia_largura_rampa`, de 0,05 para 0,0173.
- Não muda: os tercis, as sete regras, os conjuntos de saída e de faixa
  horária, o modelo de previsão, o serviço, a camada de verificação.

## Execuções e leitura

Os mesmos comandos e protocolos da Parte C de
`modelo/PROTOCOLO_MODELO_ZURIQUE.md` (suíte, avaliação das IAs, substitutos,
ruído, suavidade, déficit), sem alterar métricas nem regras de leitura. Os
cenários de ruído são gerados de novo em volta dos mesmos tercis.

Os resultados da v5 ficam em `cenarios/resultados/v5_zurique/` e são
reportados ao lado dos da v6. Se a v6 piorar alguma métrica em relação à v5,
isso também é reportado.

Nenhum tercil, regra, cenário, métrica ou critério é trocado depois do
resultado.
