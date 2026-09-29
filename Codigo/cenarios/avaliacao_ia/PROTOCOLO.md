# Protocolo da avaliação das IAs (DIVERGENCIAS 57)

Fixado **antes** de qualquer execução e versionado junto com os cenários
(`gerar.py`, `sorteio.json`). Os resultados são reportados como vierem, inclusive
se nenhuma IA mostrar ganho.

**Pergunta:** se a previsão (XGBoost) ou a inferência nebulosa fossem retiradas,
o sistema perderia algo mensurável?

- Retirar a previsão = modo **reativo** (a inferência recebe o volume observado no
  lugar do previsto, com a mesma base de regras).
- Retirar a lógica nebulosa = modo **degraus** (a mesma base como tabela, sem
  pertinência parcial).

## Parte 1 — noites reais de Melbourne (`melbourne/`)

- 8 noites (18h–06h) de 4 sensores sorteados com semente 57: 2 do grupo mais
  movimentado à noite e 2 do menos movimentado, cada um com uma noite de dia útil e
  uma de sábado. Todas no **período de teste** do modelo (corte em 2026-04-27 18h,
  com 8 dias de folga para que o histórico de 168 h também seja de teste).
- Histórico e volume reais, normalizados como no treino (contagem ÷ p99 do sensor,
  limitado a 1). A série é horária: o volume de 5 min repete o valor da hora.
- Modos: antecipado, reativo, degraus antecipado, degraus reativo.

Métricas:

1. **Violações** de piso e de taxa (esperado: zero).
2. **Energia** (REF-40W) em relação ao pleno e ao horário fixo.
3. **H3 primária** — a métrica de 3.9, sem alteração: fração dos ciclos da janela
   de baixa demanda (volume observado abaixo do tercil inferior, sem ocorrência)
   com nível acima da classe mínima + 0,02.
4. **H3 secundária** — atraso até a classe mínima: em cada episódio de baixa
   demanda (ciclos consecutivos com volume observado abaixo do tercil, com ao
   menos 30 min), minutos do início do episódio até o nível emitido chegar à
   classe mínima + 0,02 (ou a duração do episódio, se não chegar).
5. **Acerto da contenção pela previsão** — ciclos em que o modo antecipado
   mantém o nível acima do reativo (a previsão "segura" a luz). Fração desses
   ciclos em que o volume **real** da hora seguinte ficou no tercil médio ou alto,
   isto é, em que segurar estava certo. Referência: a mesma fração calculada sobre
   todos os ciclos de volume observado baixo (o acerto de segurar sempre).
6. **Forma da resposta** (Mamdani × degraus): variação total do nível, inversões
   de sentido e subidas bruscas (≥ 0,1 num passo), por noite e no agregado.

## Parte 2 — câmera errando (`camera/`)

- Dois pares sintéticos (histórico = perfil sintético da suíte): início da noite
  (18h) e madrugada (01h), 4 h cada. No par, o **controle** publica o movimento
  real; a **falha** publica volume zero entre os minutos 30 e 150, com o mesmo
  movimento real.
- Modos: antecipado e reativo.

Métricas, na janela da falha:

7. **Luz perdida pela falha** — média de (nível do controle − nível da falha) e
   minutos na classe mínima enquanto o controle está acima dela.
8. **Custo da proteção** — a entrada da falha é idêntica à de uma rua realmente
   vazia. A energia a mais do antecipado sobre o reativo nessa janela é o que a
   previsão gasta quando a rua está de fato vazia.

## Regras de leitura

- Nenhuma métrica, janela, sensor ou noite é trocada depois de ver o resultado.
- Ganho da previsão = métricas 3/4 melhores no antecipado, ou métrica 5 acima da
  referência, ou métrica 7 menor no antecipado (com o custo da métrica 8 ao lado).
- Ganho da lógica nebulosa = métrica 6 com resposta mais gradual sem piorar 1–3.
