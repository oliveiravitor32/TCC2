# Protocolo: XGBoost contra outros modelos de aprendizado (DIVERGENCIAS 68)

Fixado **antes** de qualquer treino dos modelos comparados. O resultado é
reportado como vier, inclusive se outro modelo empatar ou superar o XGBoost.

**Pergunta:** na mesma tarefa, com os mesmos dados e os mesmos atributos, o
XGBoost (2.7, 3.6) supera um modelo linear e outro modelo de árvores, a Random
Forest? Responde à pergunta "por que XGBoost e não outro modelo?", que a
referência de 2.7 (árvores contra redes neurais) não cobre.

## Dados, partição e atributos

Exatamente os de `modelo/treinar.py` e de `modelo/resultados/metricas.json`
(5.1): série horária de Melbourne extraída em 23/09/2026 (sha256 2e8f9fc9...),
49 pontos utilizáveis, nível normalizado pelo percentil 99 do ponto, partição
cronológica com os 20 % finais como teste (corte em 27/04/2026 18:00), mesmos
13 atributos. O XGBoost é o **modelo salvo** em `modelo/modelo_previsao.json`, o
mesmo que o sistema usa; não é retreinado.

## Modelos comparados (sem ajuste de hiperparâmetros)

- **Regressão linear** (mínimos quadrados, scikit-learn `LinearRegression`), com
  hora e dia da semana em codificação de uma coluna por categoria, e os demais
  atributos como estão.
- **Random Forest** (scikit-learn `RandomForestRegressor`): 200 árvores,
  `min_samples_leaf=5`, `max_features=0.5`, `max_samples=0.3`, `random_state=37`.
  Treinada no mesmo conjunto de treino do XGBoost (treino + validação).
- **XGBoost**: o modelo salvo (o único com parada antecipada sobre validação,
  como está no sistema; registrado como assimetria a favor dele).
- Referências já existentes, como controle: persistência e média sazonal.

Nenhum modelo tem os hiperparâmetros ajustados para este teste. Os valores da
Random Forest acima são escolhas usuais declaradas aqui, antes de rodar, para
que o treino caiba em memória e em minutos (`max_samples`).

## Métricas (conjunto de teste)

1. MAE e RMSE, em todas as horas (como 5.1) e à noite (18h às 06h).
2. **Acerto da faixa** à noite: fração dos casos em que a faixa prevista
   (baixa, média, alta, pelos tercis do sistema, 0,1038 e 0,4053) é a faixa
   real do alvo — é a grandeza que as regras usam.
3. **Por ponto**: em quantos dos 49 pontos o XGBoost tem MAE menor que cada
   outro modelo.
4. Tempo de treino e de previsão de cada modelo, no mesmo computador.

## Leitura

- O XGBoost é **superior** a um modelo se tiver MAE (todas as horas) menor em
  pelo menos **2 %** relativos **e** MAE menor na maioria dos 49 pontos.
- Se a diferença de MAE for menor que 2 %, os dois são **equivalentes** em
  erro; nesse caso, o texto diz isso e a escolha passa a ser justificada pelos
  tempos medidos e pela referência de 2.7, sem afirmar superioridade.
- Se outro modelo tiver MAE menor em pelo menos 2 % **e** na maioria dos
  pontos, o XGBoost é **inferior** a ele, e isso vai para o texto.
