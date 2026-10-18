# Plano: decisão por grupo de postes e arquitetura em escala real

> Documento para entregar a outra sessão do Claude Code. Leia antes o `CLAUDE.md` da raiz (regras do projeto) e o `VALIDACAO_ARQUITETURA.md` (a análise que originou este plano).

## 1. O que é, em linguagem simples

Hoje o sistema decide o nível de luz **poste a poste**. Cada vez que uma rua (trecho) publica um volume, o serviço decide de novo para cada poste ligado àquela rua e manda um comando para cada um.

Na bancada isso funciona. Numa cidade inteira, não:
- **Volume de decisões:** são 663 mil postes e cerca de 3.700 decisões por segundo.
- **Rede de telegestão:** a renovação de validade dá cerca de 1.000 comandos por segundo **para sempre**. As redes reais de telegestão (LoRaWAN, NB-IoT, malha) não aguentam esse volume de mensagens descendo até a luminária.
- **Armazenamento:** as decisões ocupam centenas de GB por dia.

A implementação muda a **unidade de decisão** de "poste" para **"grupo de postes"**:

- **O que é um grupo:** o conjunto de postes que enxergam **exatamente as mesmas ruas** (associação de até 25 m que já existe na tabela `trecho_ponto`).
- **Cada poste pertence a um único grupo.** Os grupos dividem os postes sem sobreposição.
- **A plataforma de monitoramento não muda nada.** Continua publicando por rua, como no Quadro 18. Quem descobre os grupos é o nosso serviço, a partir do nosso cadastro.
- **Mesmo nível dentro do grupo.** Todos os postes do grupo recebem o mesmo nível, sempre pelo lado seguro: o maior volume entre as ruas do grupo e o pleno se houver ocorrência em qualquer uma delas.
- **Sem cascata.** A decisão de um grupo só lê dados das ruas, nunca o nível de outro grupo. O efeito de um evento vai só até os postes a até 25 m da rua dele, e para aí.

No recorte real do Jardim Helena (`Codigo/cadastro/dados/recorte_jardim_helena.json`), 34 postes associados formaram **17 grupos**, cada poste em um só.

## 2. Objetivo

1. **Protótipo:** decidir e comandar por grupo, mantendo o que já foi provado:
   - zero violações de piso e de taxa;
   - failsafe (sem comando, o nó vai ao pleno);
   - latência abaixo de 2 s na bancada;
   - auditoria completa (RNF04).
2. **Texto do TCC:** corrigir a **3.12.6.4** (arquitetura de referência), o **Apêndice D** (custo) e a **5.3** (limitações). A versão atual da proposta tem pontos que não se sustentam em escala de cidade; ver os pontos A a H do `VALIDACAO_ARQUITETURA.md`.
3. **Escala para muitos municípios ou para o país:** descrever no texto o modelo de **"células"**.
   - Cada município, ou região, roda a sua própria cópia completa: API, decisão, banco e adaptador para a central da sua concessionária.
   - Só a base de regras, a tabela de classes da norma e os modelos vêm de um registro comum, com versões.
   - Se uma célula cai, só aquele município volta para a agenda dos controladores.

## 3. Restrições do projeto (obrigatórias)

- **Idioma:** responder em português do Brasil e explicar de forma simples, porque o autor é iniciante em eletrônica.
- **Testes:** rodar a suíte com `Codigo/.venv/Scripts/python.exe -m pytest -q` (hoje são 262 testes). A camada de verificação **nunca** pode ter violação.
- **Normas fora do código:** não pôr valores normativos fixos no código; ler sempre da tabela `classe_iluminacao`.
- **Commits:** pequenos, com mensagem em português, **sem push** (o autor faz o push).
- **Texto do TCC:**
  - sempre uma versão nova, `..._SP_v61_revisado.docx` (com controle de alterações) e `..._SP_v61.docx` (tudo aceito);
  - **nunca sobrescrever** a v60;
  - antes de gerar, verificar se existe arquivo `~$` de bloqueio do Word;
  - manter só as 3 últimas versões na pasta;
  - atualizar o `CLAUDE.md` a cada rodada.
- **REVISAR:** toda proposta de desenho, critério ou texto redigido pela IA vira item novo em `REVISAR_ANTES_DE_SUBMETER.txt`. Só o autor marca esses itens.
- **VM:** pedir autorização antes de acessar. Fazer backup do banco antes de qualquer migração. **Nunca** rodar `docker compose down -v`.
- **Segredos:** os arquivos `segredos.h`, `.env`, `bancada/chave_vm.txt` e `simulador/senha_simulado02.txt` nunca vão para o git e nunca são impressos.
- **Não alterar** os resultados já publicados nos Capítulos 4 e 5. A mudança de unidade de decisão é **proposta para escala**. Se o protótipo mudar, declarar isso e rodar de novo o que for afetado.

## 4. Plano de trabalho

### Etapa 0: avaliar antes de fazer (obrigatória)
- Ler `VALIDACAO_ARQUITETURA.md`, seções 3 a 6.
- Ler a v60 nas seções 3.5.2, 3.7, 3.12.6.1 a 3.12.6.4, 3.13, 5.3 e no Apêndice D.
- Ler `Codigo/decisao/ciclo.py`, `servico.py`, `Codigo/db/schema.sql` e `Codigo/cadastro/associar.py`.
- **Perguntar ao autor**, antes de codificar:
  1. **Escopo:** (a) só o texto (proposta), ou (b) texto e protótipo decidindo por grupo?
  2. **Tipo de grupo:** grupo pelo conjunto de ruas (fino), ou grupo/circuito da concessionária (grosso, menos economia)? Recomendação: o fino no protótipo, com o texto dizendo que o grosso também funciona.
  3. **Bancada:** se o protótipo mudar, refazer CT15 a CT20? Envolve o nó físico e a VM.

### Etapa 1: grupos no cadastro (só se o escopo for b)
- Migração `Codigo/db/migracoes/011_grupo_controle.sql`:
  - tabela `grupo_controle` (id, conjunto de trechos ordenado, hash do conjunto, instante do cálculo);
  - coluna `ponto_de_luz.grupo_id` **obrigatória**, o que garante um grupo por poste.
- Função que calcula os grupos a partir de `trecho_ponto`: postes com o mesmo conjunto de trechos ficam no mesmo grupo. Ela roda só quando o cadastro muda, nunca durante a operação.
- Atualizar `schema.sql`, `seed_cadastro.sql`, o Quadro 16, o Quadro 17 e a Figura 10. O diagrama é gerado por `Codigo/figuras/figura3_er.py`.
- **Testes:**
  - cada poste em exatamente um grupo;
  - recalcular duas vezes dá o mesmo resultado;
  - no recorte do Jardim Helena, 17 grupos.

### Etapa 2: decisão por grupo (só se o escopo for b)
- Em `decisao/ciclo.py` e `servico.py`:
  - o evento de um trecho gera "reavaliar" para os **grupos** que contêm o trecho;
  - decide-se uma vez por grupo, com as entradas = maior volume e qualquer ocorrência entre os trechos do grupo. É a mesma regra de hoje, aplicada ao grupo.
- **Agregação:** se vários trechos do mesmo grupo publicarem em poucos segundos, decidir uma vez só (janela curta configurável).
- **Previsão por trecho:** calculada uma vez por trecho a cada bloco de 15 min, guardada e reaproveitada. Medido: XGBoost ~2,0 ms por chamada; Mamdani ~0,8 ms.
- **Comando por grupo:** um comando no tópico de cada poste do grupo, enquanto existir o MQTT de bancada, ou um tópico de grupo. Comando só quando o nível muda ou na renovação.
- **Camada de verificação:** continua no caminho do comando, sobre o nível do grupo, com o piso lido da classe. Se o grupo tiver postes de classes diferentes, vale o piso **mais alto**.
- **Teste de invariante:** a decisão de um grupo nunca lê o nível de outro grupo (sem cascata).
- **Auditoria:** a decisão grava `grupo_id` e os postes atingidos; a telemetria continua por poste.
- Rodar de novo a suíte de cenários (`python -m cenarios.executar --serie`, também com `--reativo` e com `--degraus`) e conferir:
  - zero violações;
  - energia e aderência próximas das da Tabela 2;
  - qualquer diferença registrada em `DIVERGENCIAS_TCC.txt`.

### Etapa 3: texto do TCC (v61), em qualquer escopo
- **3.12.6.4:**
  - unidade de decisão = grupo de controle (definição, um poste por grupo, sem cascata);
  - previsão por trecho a cada 15 min, em lote;
  - fila em dois estágios **dentro do serviço** (por trecho → por grupo), com um único dono por grupo;
  - comando em grupo só na mudança;
  - failsafe de campo = agenda residente do controlador, com sinal de vida por gateway ou grupo;
  - registro completo só das decisões que mudam o nível, em série temporal comprimida;
  - retomada escalonada após falha, com prioridade para ocorrências;
  - hora do evento, e não da chegada, com descarte do que já venceu;
  - backup em outra região;
  - **células** por município, com registro comum de regras e modelos.
- **Apêndice D:**
  - declarar que o custo vale para a cobertura atual (~50 mil câmeras);
  - com as decisões de grupo, a mesma infraestrutura atende a cobertura total de São Paulo;
  - recalcular com `Codigo/custo/estimativa_aws.py` se o dimensionamento mudar.
- **5.3:** limitação nova. A capacidade real da central e da rede de telegestão da concessionária não é pública e não foi avaliada. Dentro de um grupo, todos os postes ficam no nível do mais exigente, o que custa um pouco de economia.
- **3.3:** só se necessário, uma remissão ao compromisso já declarado para comando de circuito.
- **Escala nacional:** ~22 milhões de pontos no país (ABCIP, 2024a, já nas Referências), ~33 vezes São Paulo. Os números são **ordem de grandeza, não teste de carga**, e o texto precisa dizer isso.
- Atualizar o `CLAUDE.md` e o `REVISAR`. Gerar a v61 com as ferramentas usadas nas rodadas anteriores: edição do XML com controle de alterações e aceite. Conferir em PDF exportado pelo Word.

### Etapa 4: bancada e VM (só se o escopo for b e o autor autorizar)
- Backup do banco na VM, aplicar a migração 011, atualizar o código por bundle (como nas rodadas anteriores).
- Conferir a bancada com `python -m bancada.conferir --vm` e repetir os CT afetados.

## 5. Números de referência (já calculados)

| Grandeza | Valor |
|---|---|
| Pontos de luz em SP (GeoSampa) | 662.945 |
| Trechos em SP (GeoSampa) | 218.768 |
| Pontos por trecho / trechos por ponto (Jardim Helena) | 5,1 / 2,3 |
| Grupos no Jardim Helena | 17 para 34 postes (~2 postes por grupo) |
| Decisões/s em SP, cobertura total, por poste | ~3.700 |
| Decisões/s em SP, por grupo e com janela de 5 min | ~1.100 |
| Previsões/s, por trecho a cada 15 min | ~243 |
| Comandos/s, por grupo e só na mudança | dezenas a ~100 (antes ~1.000) |
| Custo de CPU medido por decisão | 0,8 ms (Mamdani) + 2,0 ms (XGBoost) |
| Brasil | ~22 milhões de pontos (~33 × SP) |

## 6. Critérios de pronto
- [ ] O autor respondeu às 3 perguntas da Etapa 0.
- [ ] (Escopo b) Cada poste em exatamente um grupo, com teste.
- [ ] (Escopo b) Decisão sem cascata, com teste.
- [ ] (Escopo b) Os 262+ testes passam; a suíte tem zero violações.
- [ ] (Escopo b) Divergências registradas.
- [ ] v61 com 3.12.6.4, Apêndice D e 5.3 corrigidos, com controle de alterações.
- [ ] Item novo no REVISAR, `CLAUDE.md` atualizado, commits sem push.
