# Protocolo: as IAs contra substitutos simples (DIVERGENCIAS 59)

Fixado **antes** de qualquer execução. Os resultados são reportados como vierem.

**Pergunta:** existe algo simples que faça o mesmo que cada IA, com o mesmo resultado?
Esse é o critério do orientador: a IA precisa ser uma escolha de arquitetura, não
um enfeite que uma regra trivial substituiria.

## Teste 1: XGBoost × média sazonal

- Substituto: `MediaSazonal` (`decisao/previsao.py`). O nível da próxima hora é o
  daquela mesma hora nas semanas anteriores, calculado só com o histórico do
  próprio ponto e sem treino. É a referência "média sazonal" de 3.6 levada para
  dentro do sistema. Os cenários trazem 168 h de histórico, então na prática ela
  usa **uma semana**. O XGBoost recebe o mesmo histórico.
- Cenários: os mesmos do item 57, sem alteração (`melbourne/` e `camera/`).
- Modo: antecipado, base v4-volume (Mamdani).
- Métricas (as do PROTOCOLO.md, sem alteração):
  - Melbourne: 1 (violações), 2 (energia), 3 e 4 (H3), 5 (acerto da contenção),
    mais o déficit do item 58 (minutos abaixo do nível pedido).
  - Câmera: 7 (luz perdida) e 8 (custo).
- **Leitura:**
  - O XGBoost **não é substituível** se, nas noites reais, tiver acerto da
    contenção maior ou déficit menor que a média sazonal, sem gastar mais de 2 pp
    de energia a mais.
  - Se empatar ou perder, fica **substituível**.
  - Declarado antes: na câmera, o histórico sintético repete a mesma semana, e a
    média sazonal acerta por construção. Esse par, portanto, não decide nada.

## Teste 2: Mamdani × tabela com contagem ruidosa na fronteira

- Cenários novos (`ruido/`, gerados por `gerar_substitutos.py`), 3 h cada, volume a
  cada 5 min sorteado de normal(fronteira; 0,03), limitado a [0, 1]:
  - fronteira baixa (tercil 0,1038), madrugada 01h, sementes 591, 592 e 593;
  - fronteira alta (tercil 0,4053), início da noite 19h, sementes 591, 592 e 593.
- Modos: antecipado (Mamdani) × antecipado degraus (tabela), ambos com XGBoost.
- Métricas: 1 (violações), 2 (energia), 6 (variação total, inversões de sentido,
  subidas bruscas ≥ 0,1 num passo).
- **Leitura:**
  - O Mamdani **não é substituível** se tiver menos inversões **e** menor variação
    total que a tabela no agregado dos 6 cenários, sem violações e com diferença
    de energia de no máximo 2 pp.
  - Caso contrário, fica **substituível**.

Nenhum cenário, semente, métrica ou critério é trocado depois de ver o resultado.
