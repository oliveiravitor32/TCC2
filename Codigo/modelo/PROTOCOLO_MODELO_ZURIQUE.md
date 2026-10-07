# Protocolo: troca do modelo principal para a série de 15 min de Zurique (DIVERGENCIAS 69)

Fixado **antes** de qualquer treino, código ou execução desta troca. Os
resultados são reportados como vierem, inclusive se o modelo novo não superar as
referências no sistema.

## Decisão e motivo (declarados)

A troca é **decisão dos autores, tomada depois de ver** dois resultados já no
texto: o experimento de Zurique (item 60, Quadro 20), em que o XGBoost só supera
as referências simples com dado sub-horário, e a auditoria da preparação (item
68), que achou o percentil 99 e os tercis calculados sobre a série inteira,
inclusive o teste. A série horária de Melbourne deixa de ser a do modelo
principal e passa a constar como a série do primeiro treino, com os resultados
anteriores mantidos no histórico do repositório.

## Parte A — o modelo

### Dados

- Arquivo de Zurique já usado no item 60 (sha256 `34a41dce...`, baixado em
  30/09/2026, licença CC0). Pedestres = FUSS_IN + FUSS_OUT.
- Janela 01/01/2016 a 31/12/2019; pontos com ≥ 730 dias entre o primeiro e o
  último registro e cobertura ≥ 95 % (os mesmos 14 do item 60).
- Partição cronológica: treino até 31/12/2018, teste = 2019; validação = últimos
  10 % do treino (parada antecipada).

### Preparação (checklist; cada passo reporta a contagem no relatório)

1. **Integridade:** nulos (descartados), negativos (descartados), carimbos
   repetidos por ponto (contados).
2. **Horário de verão:** DATUM é hora local. No dia em que o relógio volta, a
   hora repetida aparece com carimbos repetidos: os valores repetidos de um
   mesmo carimbo são **combinados pela média**, e não somados, para não dobrar
   a contagem. No dia em que o relógio avança, a hora inexistente fica ausente.
3. **Faltantes:** grade completa de 15 min por ponto; intervalo ausente não é
   preenchido, e as linhas que dependem dele (atrasos, médias, alvo) são
   descartadas.
4. **Sensor travado:** sequência de **zero** com ≥ 8 h que inclua horário entre
   08h e 20h é marcada como falha do sensor e tratada como ausente (passo 3).
   Zero de madrugada não é marcado.
5. **Valores atípicos:** normalização pelo percentil 99 do ponto **calculado só
   no treino**, com o nível limitado a 1. Reporta-se quantos intervalos ficam
   acima do p99 e acima de 2 × p99. Nenhum é removido: o corte em 1 é o
   tratamento.
6. **Realocação de sensor:** para cada ponto, a mediana mensal do nível; mês com
   mediana fora de 0,5 a 2 vezes a mediana do ponto é listado no relatório.
   **Só se reporta**, sem excluir.
7. **Feriados:** calendário do cantão de Zurique codificado (Ano-Novo,
   Berchtoldstag 2/1, Sexta-Feira Santa, Segunda de Páscoa, 1º de Maio,
   Ascensão, Segunda de Pentecostes, 1º de Agosto, Natal, Santo Estêvão).
   Meios feriados locais (Sechseläuten, Knabenschiessen) não entram: aproximação
   declarada.

### Atributos e alvo

- Atrasos de 1, 2, 3, 4, 8, 96 e 672 intervalos; médias de 1 h, 3 h e 24 h;
  hora; quarto de hora; seno e cosseno da fração do dia; dia da semana; fim de
  semana; **feriado** (novo em relação ao item 60).
- Alvo: nível médio dos próximos 60 minutos, refeito a cada 15 minutos.
- XGBoost com os hiperparâmetros de `modelo/treinar.py`, semente 37.
- **Tercis** das partições (3.7): percentis 1/3 e 2/3 do nível, todos os pontos
  e todas as horas, **só no treino**.

### Comparações (teste, 2019)

Persistência (última hora), média sazonal (treino; ponto, dia da semana,
horário), semana anterior, regressão linear e Random Forest (mesmas
configurações de `PROTOCOLO_COMPARACAO_MODELOS.md`).

Métricas: MAE e RMSE em todas as horas e à noite (18h às 06h); acerto da faixa
à noite pelos tercis novos; F1 do "vai subir" à noite; por ponto, em quantos o
XGBoost tem MAE menor.

### Leitura

- Contra a regressão linear e a Random Forest: a regra de 2 % de
  `PROTOCOLO_COMPARACAO_MODELOS.md` (superior, equivalente ou inferior).
- Contra as referências simples: a regra do item 60 (não substituível se, à
  noite, superar a melhor referência simples em acerto da faixa por ≥ 2 pontos
  percentuais e em F1 do "vai subir" por ≥ 0,02).

## Parte B — o serviço

- A série de previsão passa de média horária para **blocos de 15 min**: média
  dos volumes de 5 min do bloco, dividida pela referência do trecho = percentil
  99 das médias de 15 min dos últimos 28 dias, calculada com ao menos 672
  blocos (7 dias); antes disso, o valor inicial de cinco pessoas, como hoje.
- Sem histórico para os atrasos, o serviço continua recorrendo à persistência.
- Em operação, o atributo de feriado usa o calendário nacional brasileiro, como
  hoje.
- Nova versão da base de regras (`v5-zurique`): as **mesmas sete regras** da
  v4, só com os tercis novos. Nenhuma regra, peso ou forma de pertinência muda.
- A camada de verificação não é tocada. Todos os testes têm de passar.

## Parte C — o que é executado de novo

Com o modelo novo, a base v5 e os protocolos já registrados, **sem alterar suas
métricas nem suas regras de leitura**:

1. Suíte de cenários (5.2, 5.4, 5.5): `cenarios/executar.py --serie`, com
   `--reativo` e `--degraus`, e `cenarios/aderencia_regimes.py`.
2. Avaliação das IAs (5.6): `PROTOCOLO.md`, `PROTOCOLO_SUBSTITUTOS.md` e
   `PROTOCOLO_SUAVIDADE.md`. A única troca de dado é a da Parte 1 de
   `PROTOCOLO.md`: as 8 noites reais passam a ser de **Zurique**, sorteadas no
   teste (2019) com a mesma semente (57) e a mesma regra (2 pontos mais e 2
   menos movimentados à noite, cada um com uma noite de dia útil e uma de
   sábado, com ao menos 8 dias de teste antes, para o atraso de 672 intervalos).
   O volume de 5 min repete o valor do bloco de 15 min.
3. Déficit em relação ao nível pedido (`deficit.py`).

## Parte D — o que não muda

A camada de verificação, os casos CT01 a CT20 (a bancada testou o percurso, a
latência e o failsafe, e não a previsão), a calibração e a especificação da
interface.

Nenhum ponto, janela, atributo, limiar, métrica, noite ou regra de leitura é
trocado depois de ver o resultado.
