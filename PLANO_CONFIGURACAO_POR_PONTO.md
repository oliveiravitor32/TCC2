# Plano: configuração por ponto, manutenção remota e teto absoluto de taxa no firmware

> Documento de passagem para outra sessão do Claude Code. Leia inteiro antes de mexer em qualquer arquivo.
> Escrito em 18/10/2026, a partir da conversa com o autor (Vitor). A versão mais recente do texto do TCC é a **v60** (`Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP_v60.docx`).

---

## 1. O que é, em linguagem simples

O sistema do TCC decide quanto cada poste deve iluminar, e um aparelho no poste (o "nó", hoje um ESP32 na bancada) executa a decisão.

A ideia desta implementação é deixar claro, e reforçar no código, que:

- **Existe um único firmware para todos os postes.** Ninguém precisa compilar um programa diferente para cada rua.
- **O que muda de uma rua para outra chega ao poste como dado (configuração):**
  - a classe de iluminação da via (P3, P4…, e no futuro M ou C);
  - o piso e a taxa máxima de descida que a norma permite;
  - a curva "nível → potência" de cada luminária, que é a calibração.
- **Essa configuração pode ser aplicada e corrigida à distância**, na instalação em massa e em manutenções futuras.
- **Mesmo que a central mande um comando errado, o poste nunca desce a luz mais rápido do que a norma permite.** Este é o "teto absoluto de taxa", gravado no próprio firmware, e é a única parte que vira código agora.

**Objetivo para o TCC:** responder às perguntas prováveis da banca:

- "e se cada rua for diferente?";
- "como se instala isso em um bairro inteiro?";
- "e se surgirem classes novas, como a de vias de carros?";
- "e se a central errar?".

A resposta mostra que a arquitetura escala sem um firmware por ponto e com a norma garantida em duas barreiras.

---

## 2. O que já existe hoje (conferido no código em 18/10/2026)

| O que varia por ponto | Onde está | Como muda hoje |
|---|---|---|
| Classe da via | `ponto_de_luz.classe` + tabela `classe_iluminacao` (`Codigo/db/schema.sql`, `seed.sql`) | Operação no banco (RF09) |
| Piso e taxa | Lidos da classe pela central (`Codigo/decisao/verificacao.py`, `ciclo.py`) e **enviados em cada comando** `{nivel, validade_s, piso, taxa_min, decisao_id}` | A classe nova vale no próximo comando |
| Validade do comando (failsafe) | No comando | Idem |
| Curva nível → duty (calibração) | Tabela `calibracao` no banco + cópia na memória do nó (`Codigo/bancada/calibrar.py`, `conferir.py`; seção 3.4.4 do texto) | Gravada no nó **pela porta serial**, sem recompilar |
| Credencial e rede do nó | `Codigo/firmware/no/segredos.h` (fora do git) | **Compilada** junto com o firmware: é a única coisa que ainda exige compilação por nó |

**Comportamento atual do firmware** (`Codigo/firmware/no/no.ino`):

- **Validação do comando** (por volta das linhas 215–220): aceita `piso` entre 0 e 1 e `taxa_min` entre 0 (exclusive) e 1.
  - Ou seja, aceitaria uma taxa de até **1,0 do pleno por minuto**, dez vezes o limite da norma.
- **Rampa** (por volta das linhas 568–575): a cada 5 s desce no máximo `taxa_min × 5/60`, arredondado para baixo a 3 casas, sem passar do alvo nem do piso.
- **Failsafe:** vencida a validade, o nó vai ao pleno (1,0).
- **Classes não dimerizáveis:** com piso 1,0 o nó fica no pleno, e isso já funciona.

O nó simulado (`Codigo/simulador/no_simulado.py`) e o nó virtual dos cenários (`Codigo/decisao/rampa.py`) reproduzem a mesma regra da rampa.

---

## 3. Escopo

### Parte A: código (decidido pelo autor: "gostei, vamos colocar")

**A1. Teto absoluto de taxa no firmware.**

- Constante `TAXA_MAX_ABSOLUTA = 0.1` (fração do pleno por minuto), no `no.ino`.
- Ao receber um comando, usar `taxa efetiva = min(taxa_min recebida, TAXA_MAX_ABSOLUTA)`.
- Se a taxa recebida for maior, **não recusar o comando** (subir de nível continua imediato, e o alvo e o piso continuam valendo). Apenas limitar a taxa e escrever um aviso na serial.
- Manter o arredondamento para baixo já existente.
- **Atenção à regra do projeto:** o CLAUDE.md diz "não coloque valores normativos fixos no código; leia do banco". Este teto é uma **exceção deliberada**, do mesmo tipo do failsafe: é um limite de segurança que precisa valer mesmo com o banco ou a central errados. A justificativa é que a NBR 5101 (6.10) aplica a mesma taxa a todas as classes. Isso precisa ficar escrito:
  - no comentário do código;
  - no texto do TCC;
  - num item novo do REVISAR.

**A2. Mesmo teto no nó simulado e no nó virtual** (`simulador/no_simulado.py`, `decisao/rampa.py`), para que simulação e bancada se comportem igual.

- Avaliar se o teto deve ficar em `decisao/config.py` como constante única.
- Conferir se isso conflita com a regra "ler do banco". Se conflitar, a referência continua sendo a do firmware, e o simulado só a espelha.

**A3. Testes** (`Codigo/tests/`):

- comando com `taxa_min` 0,5 → a rampa desce no máximo 0,008 por passo de 5 s;
- comando com `taxa_min` 0,05 → usa 0,05, porque é menor que o teto;
- a subida continua imediata;
- rodar a suíte inteira. Hoje são **262 testes aprovados**; a regra do projeto é rodar tudo depois de mexer em verificação e rampa.

**A4. Sem mudança na central** (`verificacao.py`). Ela já confere a taxa da tabela.

- Opcional: avaliar se vale uma restrição no banco (`CHECK taxa_max_decrescimo_min <= 0.1` em `classe_iluminacao`).
- **Isso exige migração nova** (011), com backup antes e nunca `docker compose down -v` na VM.
- **Perguntar ao autor antes.**

**A5. Gravar o firmware no ESP32:** quem grava é o **autor**, pela Arduino IDE (placa "DOIT ESP32 DEVKIT V1", COM3). Depois de gravado, rodar a conferência da bancada:

```
python -m bancada.conferir --vm
```

Não acessar a VM sem pedir.

### Parte B: texto do TCC (nova versão, v61, com controle de alterações)

**B1. Subseção nova "3.12.6.5 Configuração por ponto e manutenção remota"**, logo depois da 3.12.6.4. Conteúdo:

1. **Princípio:** um firmware para todos os pontos; o que varia por rua é dado. Já está previsto no RF09 e em 3.13.1 ("operação de dado e não de software").
2. **Quadro novo** com as colunas: o que varia por ponto · onde fica · como muda na bancada · como mudaria no parque · quem garante a norma. As linhas são classe, piso, taxa, curva, validade e identidade.
   - Para não renumerar os Quadros 15 a 21, pode ser preferível escrever em lista, ou pôr o quadro num apêndice novo. **Decidir com o autor.**
3. **Calibração como instrumento de instalação:**
   - na bancada, a curva é medida com sensor;
   - no parque, vem do projeto luminotécnico e da certificação da luminária;
   - **teto do ponto** = a potência que entrega o valor da classe (10 lux em P3) naquela rua;
   - **piso do ponto** = a potência que entrega o piso (5 lux);
   - a decisão continua em fração da classe (3.3).
4. **Instalação em massa pela concessionária** (proposta):
   - projeto luminotécnico agrupado por **perfil de trecho** (classe + geometria: altura do poste, espaçamento, largura da calçada);
   - na instalação, o controlador se anuncia, a central o liga à placa do GeoSampa e aplica a classe e o perfil do trecho, sem configuração manual;
   - **conferência por amostragem** com luxímetro (luminancímetro na classe M), aproveitando a campanha do indicador contratual de iluminância, que mede ao menos 100 pontos (2.5);
   - ajuste fino por ponto, à distância.
5. **Configuração e manutenção remota** (proposta):
   - padrão "estado desejado × estado relatado";
   - canal de configuração separado do canal de comando;
   - configuração versionada, aplicada só com confirmação e com volta à versão anterior;
   - só operador autenticado, com registro de cada mudança;
   - atualização remota de firmware (OTA) com pacote assinado e duas partições;
   - no parque, a configuração passa pela central de telegestão da concessionária (interface padronizada, TALQ, já citada em 3.5.2), e não diretamente do serviço de decisão ao controlador.
6. **Duas barreiras da norma:** a central recusa configuração ou comando fora da norma, e o firmware tem o **teto absoluto de taxa** (Parte A). Isso vale para qualquer classe, porque a norma usa uma taxa só.
7. **Classes novas** (M para veículos, C para conflito, P diferentes):
   - entram como dado novo, sem trocar firmware;
   - piso 1,0 para as não dimerizáveis já funciona;
   - o que muda fora do firmware é: luminância na tabela de classes (esquema do banco), fluxo de veículos como entrada (já previsto no Quadro 7), uma versão nova da base de regras e o piso da classe mais exigente em pontos que atendem pista e calçada (já em 5.3 e 6.1);
   - **única exceção:** se a norma mudar a taxa máxima geral, o teto do firmware muda, uma vez só e por OTA;
   - rodovias normalmente estão em outro contrato (estado ou concessionária rodoviária).

**B2. 3.4**, regras do firmware: acrescentar o teto absoluto de taxa à regra da rampa ("segunda barreira"). Conferir também 3.7, parágrafo da taxa, e o passo (7) de 3.12.6.3.

**B3. 5.3 Limitações**, itens novos:

- a credencial do nó ainda é compilada por dispositivo;
- a conferência e a recalibração só funcionam pela porta serial, localmente;
- não há canal de configuração versionado nem atualização remota de firmware;
- a garantia do piso é em **fração da classe** e só vale em lux se a curva do ponto estiver certa, por isso a conferência por amostragem é indispensável;
- a instalação em massa e a configuração remota são propostas não ensaiadas.

**B4. 6.1 Recomendações:**

- implantar o canal de configuração versionado e o comissionamento por perfil de trecho;
- provisionar a identidade do controlador por certificado de fábrica;
- implantar OTA assinado.

**B5. Se o Quadro 21 do Apêndice D for afetado** (por exemplo, componente "serviço de configuração"), avaliar com o autor. O mais simples é **não** mexer no custo.

**B6. Apêndice A, Quadro 19 (declaração de IA):** acrescentar uma linha para a 3.12.6.5, com o percentual **em branco** para os autores preencherem.

---

## 4. Regras do projeto que a outra sessão precisa seguir

- **Português do Brasil**, explicação simples. O autor é iniciante em eletrônica.
- **Texto:**
  - toda mudança vira **versão nova** com controle de alterações (`..._SP_v61_revisado.docx`) mais a versão aceita (`..._SP_v61.docx`);
  - nunca sobrescrever uma versão existente;
  - conferir se não há arquivo de bloqueio `~$` do Word aberto;
  - manter **no máximo as 3 últimas versões** na pasta (remover a mais antiga com `git rm`);
  - as ferramentas usadas até aqui (Python + lxml: `tc.py`, `zipar2.py`, `aceitar.py`) estão nas pastas de rascunho de sessões anteriores. Exemplo: `C:\Users\vitor\AppData\Local\Temp\claude\C--Users-vitor-Documents-GitHub-TCC2\65ae83b0-b2ca-4025-8d00-c6b6776896e9\scratchpad\`.
- **Legendas e listas:** as legendas são campos SEQ e as listas são automáticas. Quadro, figura ou tabela nova precisa de legenda em campo SEQ, senão não entra na lista. Avisar o autor para apertar **F9** no Word.
- **Atualizar o `CLAUDE.md`**, seção "Fonte da verdade", com a entrada da v61.
- **REVISAR_ANTES_DE_SUBMETER.txt:** acrescentar um item para todo texto, critério ou decisão de projeto redigido pela IA. Aqui, a 3.12.6.5 inteira e a exceção do teto absoluto à regra "ler do banco". **Nunca marcar itens como revisados**: só o autor marca.
- **Não afirmar sem fonte:** o que a concessionária de fato implantou não é conhecido. Escrever tudo da Parte B como **proposta dos autores, não implantada nem ensaiada**.
- **Git:** commits pequenos, em português, **sem push** (o autor faz o push).
- **VM:** pedir autorização antes de acessar. Nunca `docker compose down -v`. Backup antes de qualquer migração.
- **Segredos:** `segredos.h`, `.env`, `bancada/chave_vm.txt` e `simulador/senha_simulado02.txt` nunca vão para o git e nunca aparecem em saída.
- **Quadro 19:** todas as linhas citam "Claude Opus 5 e Claude Opus 5.5" juntos.

---

## 5. Ordem sugerida

1. Ler este plano, o `CLAUDE.md` e os trechos citados de `no.ino`, `rampa.py`, `no_simulado.py` e `verificacao.py`.
2. **Confirmar com o autor:**
   - a forma do item novo de 3.12.6.5 (lista, quadro no corpo, que renumeraria quadros, ou quadro em apêndice);
   - se quer a restrição no banco (A4).
3. Parte A: código e testes (A1 a A3), commit. Pedir ao autor que grave o firmware (A5).
4. Parte B: v61 do texto (B1 a B6), REVISAR, CLAUDE.md, commit.
5. Relatório final ao autor:
   - o que mudou;
   - o resultado dos testes;
   - o que ele precisa fazer (gravar o ESP32, F9, ler o item novo do REVISAR).

---

## 6. Fora do escopo (registrado para não esquecer)

- **Logs na API e correlação por `evento_id`/`decisao_id`:** avaliados em 17/10/2026. A API não tem logs próprios, e o serviço de decisão já registra bastante. É um plano separado, ainda não autorizado.
- **Experimento com os dados por minuto de Melbourne** (setembro e outubro de 2026, 99 sensores, mais a coleta da VM): aguarda decisão do autor sobre reabrir o texto.
- **Provisionamento por certificado de fábrica e OTA:** ficam só como proposta no texto, sem implementação.
