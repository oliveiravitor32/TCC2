# Protocolo: arquitetura de implantação (DIVERGENCIAS 71)

Fixado **antes** de executar qualquer cenário com a arquitetura nova. Os
resultados são reportados como vierem, ao lado dos da v6 com o ciclo de 5 s
(guardados em `cenarios/resultados/v6_ciclo5s/`).

## Decisão e motivo (declarados)

Decisão dos autores (08/10/2026): o sistema deve funcionar como funcionaria no
parque, e não só na bancada de um nó. O Caderno de Encargos da concessão de São
Paulo (Anexo III do edital, 7.1.1, 7.1.2 e 7.2.1) exige que a lógica rode no
controlador de cada luminária, que ele funcione sem comunicação, que a central
mande comandos isolados, em grupo ou atualização de agenda, e admite até 180 s
entre a central e a luminária. O ciclo de 5 s para todos os pontos (~120 mil
comandos/s no parque, limitação de 6.3) é substituído.

## O que muda

1. **Central decide por evento.** Volume ou ocorrência de um trecho dispara a
   decisão dos pontos daquele trecho. Uma varredura de 60 s decide de novo só os
   pontos cujo comando vence em até 5 min.
2. **Publica só o necessário.** Comando só se o alvo mudou, ou se o anterior
   vence em até 5 min e o novo vence depois dele (`rampa.deve_publicar`).
3. **Comando com validade.** `{decisao_id, nivel (alvo), validade_s, piso,
   taxa_min}`. Validade = até vencer o volume que sustenta a decisão, no máximo
   900 s. Vencida, o controlador volta ao pleno (RNF07).
4. **Rampa no controlador.** Desce no máximo `taxa_min` por minuto, a cada 5 s,
   pela mesma função `verificar`; sobe na hora; nunca abaixo do piso (segunda
   barreira). A central verifica o piso do alvo.
5. **Régua diária.** O percentil 99 de 28 dias é gravado uma vez por dia em
   `trecho_via` (migração 009). Nos cenários, é a do início da execução.
6. **RNF03:** comando efetivado no nó em até 180 s (Caderno, 7.2.1).

## O que não muda

Base de regras v6-zurique, modelo de previsão, tercis, cenários, envelopes,
métricas, regras de leitura dos protocolos da avaliação das IAs (`PROTOCOLO.md`,
`PROTOCOLO_SUBSTITUTOS.md`, `PROTOCOLO_SUAVIDADE.md`), déficit e linhas de base.

As métricas continuam sobre a **luz** a cada 5 s (agora a do controlador
virtual). Para manter a comparação, o cenário começa com o controlador no
primeiro alvo, como antes, e não ligando no pleno.

## Execuções

As mesmas da Parte C de `modelo/PROTOCOLO_MODELO_ZURIQUE.md`: suíte
(antecipado, reativo, degraus, `aderencia_regimes.py`), avaliação das IAs
(noites de Zurique, câmera, substitutos, ruído, suavidade) e déficit. Acrescenta
só a contagem de decisões e de comandos da central por execução.

## Expectativa declarada antes

Resultados próximos dos da v6, com diferenças pequenas por três motivos:
decisão só na chegada de dado (faixa horária e previsão não mudam entre
eventos), régua fixa durante a execução e ocorrência encerrada por prazo
reconhecida só no evento seguinte. Diferença maior que essas é investigada e
reportada, nunca corrigida para "voltar" ao resultado anterior.
