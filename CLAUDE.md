# Projeto: Iluminação Adaptativa (TCC) — contexto para o Claude Code

Responda sempre em **português do Brasil**. O autor é iniciante em eletrônica e intermediário em programação: explique de forma direta, passo a passo, sem enrolar.

## Fonte da verdade

A especificação vigente está em `C:\Users\vitor\Documents\GitHub\TCC2\Transicao_pre-projeto-para-TCC-Completo_TCC_Iluminacao_SP.docx` (há também o `.pdf` com o mesmo conteúdo caso seja necessário verificar algo visual ou que teve problemas em visualizar no .docx). **Siga o TCC.**

> O arquivo antigo `TCC_Iluminacao_Adaptativa_SP_7.docx` está **obsoleto**: a numeração de seções e quadros mudou. Referências a "7.x", "Capítulo 8" ou "Quadro 13 = interfaces" em código, comentários, `DIVERGENCIAS_TCC.txt` e `LACUNAS_TCC.txt` seguem a numeração antiga e devem ser atualizadas para a tabela abaixo quando forem tocadas.

Seções mais importantes da versão nova:

| Assunto | Seção nova | (antiga) |
|---|---|---|
| Requisitos normativos (NBR 5101, 6.10) | 2.5 | — |
| Previsão: por que gradient boosting (XGBoost, Chen e Guestrin) | 2.7 | — |
| Hipóteses H1, H2, H3 | 2.10 | — |
| Arquitetura e por que a decisão fica fora do nó e fora do Smart Sampa | 3.2 | 7.2 |
| Protótipo × implantação (Quadros 2 e 3) | 3.3 | — |
| Nó de bancada (Quadros 4, 5, 6) | 3.4 a 3.4.4 | 7.3 |
| Funções de diagnóstico | 3.4.5 | 7.3.5 |
| Dados urbanos e cenários | 3.5 | — |
| Previsão (Melbourne, avaliação contra persistência e média sazonal) | 3.6 | 7.5 |
| Inferência Mamdani + verificação normativa + failsafe (Quadro 7) | 3.7 | 7.6 |
| Classe P3/P5 (Quadro 8) | 3.8 | 7.7 |
| Etapas 3 a 7 da avaliação e envelope esperado | 3.9 | — |
| Dados pessoais (RNF08) | 3.10 | — |
| **Energia e linhas de base (Quadro 9, fórmula fechada)** | **3.11** | nova |
| RF (Quadro 10) · RNF (Quadro 11) | 4.3 · 4.4 | Quadros 11 e 12 |
| Decisões de arquitetura (Quadro 12) · Componentes (Quadro 13) | 4.6 | Quadros 9 e 10 |
| Implantação em nuvem | 4.6.1 | 7.2.1 |
| Contratos das interfaces (Quadro 14) | 4.6.2 | Quadro 13 |
| Banco: entidades (Quadro 15), ER e modelo físico | 4.7.1 · 4.7.2 · 4.7.3 | 8.5 |
| Casos de teste (ainda PENDENTE no texto) | 4.8 / 4.10 | — |

Se o código precisar divergir do TCC, **avise explicitamente** qual trecho do texto (seção/quadro da versão nova) precisa ser atualizado.

## Resumo do sistema

Fluxo: evento urbano (REST) → serviço de decisão [previsão → inferência nebulosa Mamdani → camada de verificação normativa] → comando via MQTT → ESP32 aplica PWM na fita LED e mede lux (BH1750) → telemetria via MQTT → banco → painel.

- **Saída da decisão = fração do fluxo pleno, adimensional** (1,0 = 10 lux, classe P3). Piso = P5 = 5 lux = 0,5. O serviço **nunca** emite duty, tensão ou lux — quem converte nível em duty é o nó, via tabela de calibração medida (3.3).
- **Camada de verificação** (invariante de segurança, sempre no caminho do comando; nenhum caminho da inferência chega ao nó sem passar por ela):
  1. piso: nível emitido ≥ piso da classe mínima de dimerização (lido do banco);
  2. taxa: **decréscimo** ≤ 0,1 do pleno por minuto (elevação é livre e imediata);
  3. meteorologia adversa (chuva, neblina, nevoeiro) → nível 1,0.
- **Failsafe no nó (4ª regra, autoria dos autores, RNF07):** sem comando por X segundos → nível 1,0.
- A decisão grava **nível pretendido** (inferência) e **nível emitido** (após verificação) separados, mais a restrição aplicada e a versão da base de regras.
- Parâmetros normativos ficam **em tabela** (`classe_iluminacao`), não no código (RF09).
- `decisao_id` trafega no comando e volta na telemetria. Telemetria de decisão é **1:1** com decisão; leituras periódicas sem comando **não** vão para essa tabela (4.7.2).
- Nenhum dado pessoal, imagem, áudio ou identificador trafega ou é salvo (RNF08, 3.10).

### Variáveis de entrada da inferência (Quadro 7)

movimentação observada · movimentação prevista (próxima janela) · ocorrência reportada (categórica) · condição meteorológica (categórica) · faixa horária (relógio do serviço) · classe da via (atributo do ponto de luz).
Movimentação observada e prevista: conjuntos baixa/média/alta, **trapezoidais**, fronteiras nos **tercis** da série normalizada **por ponto de medição**. Regras só de origem normativa ou de literatura (nunca de decisões rotuladas pelos autores); base pequena e legível (RNF05).

### Previsão (3.6)

- Série horária de pedestres de **Melbourne** (registrar data de extração; janela móvel de 24 meses; zero explícito = hora sem passagem).
- Atributos: contagens das janelas anteriores + hora, dia da semana, feriado + meteorologia.
- **XGBoost** (o texto cita Chen e Guestrin, 2016 — não usar LightGBM sem avisar).
- Partição **cronológica**; métricas MAE e RMSE; comparar com **persistência** e **média sazonal** (média daquela hora naquele dia da semana). Se não superar, reportar assim mesmo.

### Diagnóstico (3.4.5, RF11)

1. **Falha total:** comando > 0 e lux ≈ iluminância residual → luminária apagada (testar desligando o ramo de 12 V).
2. **Divergência** a cada ciclo: razão lux medido / lux esperado para o comando.
3. **Alerta de perda de controle:** divergência acima da tolerância por N ciclos consecutivos. Tolerância = acima da dispersão medida no ensaio de repetibilidade (não arbitrar).
- Antes de cada sessão, medir a residual com LED desligado e subtrair; descartar sessão se residual > 5 % do valor da classe (3.4.3).

### Energia (3.11, RF12) — novo

- **Bancada:** E = Σ (potência plena do segmento × duty × Δt), com potência = 14,4 W/m × comprimento medido. Comparar com a estimativa derivada do lux medido e reportar a divergência.
- **Luminária de referência (Quadro 9):** 40 W, 90 lm/W (3.600 lm), 0–10 V, potência proporcional ao nível, consumo fixo do driver ignorado. Reportar também a **440 W** (razão idêntica).
- Por decisão, com a = nível anterior, b = novo, P em W, Δt em min:
  - atenuação: d = (a − b)/0,1; E = P × [(a + b)/2 × d + b × (Δt − d)] / 60 Wh
  - elevação: E = P × b × Δt / 60 Wh
  - se a próxima decisão chega antes do fim da rampa, integrar só o trecho percorrido.
  - Conferência: P3→P5 em 5 min a 40 W = 2,50 Wh (contra 3,33 Wh em pleno).
- **Linhas de base:** (1) fluxo pleno constante; (2) atenuação por **horário fixo** (programação agendada).
- Cada regime reporta **energia + aderência ao envelope esperado** (fração dos ciclos dentro do envelope). Nunca afirmar economia anual, de parque ou em R$.

### Hipótese H3 (atenção)

6.1 exige comparar **acionamento antecipado (com previsão) × puramente reativo** (fração da janela de baixa demanda gasta em transição). As etapas de 3.9 ainda não preveem isso: o executor de cenários deve permitir rodar a mesma suíte com a previsão ligada e desligada.

## Stack (Quadro 13)

- Python 3 + FastAPI (interface de dados urbanos / REST, JSON)
- Serviço de decisão em Python: XGBoost para previsão; scikit-fuzzy (Mamdani) para inferência; módulo próprio de verificação lendo `classe_iluminacao`
- MQTT 5.0 com TLS e credencial por dispositivo (Mosquitto)
- PostgreSQL
- Painel: HTML + CSS + JS em React, consumindo a REST
- Firmware: C++/Arduino para ESP32

## Contratos (Quadro 14)

- `POST /eventos` — carimbo de tempo, tipo, valor, abrangência, origem
- `GET /eventos` — coleção filtrada por intervalo de tempo
- `GET /decisoes` — nível pretendido, nível emitido, restrição aplicada, versão da base de regras
- `GET /telemetria` — duty aplicado e lux medido, por ponto de luz
- MQTT `iluminacao/{ponto}/comando` — nível (fração do pleno) + `decisao_id`
- MQTT `iluminacao/{ponto}/telemetria` — duty aplicado + lux + `decisao_id`

## Banco (Quadro 15 + 4.7.2)

`classe_iluminacao`, `ponto_de_luz`, `evento_urbano`, `versao_base_regras`, `decisao`, `telemetria` **e a tabela associativa `decisao` ↔ `evento_urbano` (N:N)** — registra em quais eventos cada decisão se apoiou. Reclassificação de via = registro novo, nunca UPDATE do existente. A seção 4.7.3 (modelo físico) está PENDENTE no texto e deve ser escrita a partir do `schema.sql` real.

Entidades acrescentadas pelo código (item 16 do `DIVERGENCIAS_TCC.txt`): `versao_modelo_previsao` (RNF04), `execucao_cenario` (RF10, 3.11, H3: regime + modo antecipado/reativo), `sessao_medicao` (residual, descarte 5 %), `calibracao` (duty × lux por série; origem da tabela do firmware), `alerta_diagnostico` (RF11), `luminaria_referencia` (Quadro 9). A view `auditoria_decisao` dá a razão entregue/esperado e a latência evento → telemetria.

Decisões já tomadas: luminária de referência **em tabela**; calibração **no banco, com cópia gravada no firmware**.

## Requisitos para lembrar (Quadros 10 e 11)

- RF01–RF12 (RF11 diagnóstico, RF12 energia).
- RNF01 zero violações de piso · RNF02 taxa ≤ 0,1/min · **RNF03 evento → duty aplicado no nó < 2 s** · RNF04 decisão reconstituível (reexecutar e comparar) · RNF05 regras legíveis · RNF06 TLS + credencial por nó, recusa sem credencial · RNF07 failsafe · RNF08 sem dado pessoal · **RNF09 novo nó sem alterar o serviço de decisão**.

## Implantação (decisão do autor)

Tudo sobe em **Docker (docker compose) numa VM da Oracle Cloud (Always Free)**: API de eventos, serviço de decisão (worker sempre ligado), Mosquitto com TLS, PostgreSQL e painel. O ESP32 conecta pela internet ao Mosquitto da VM (porta 8883).

> **Divergência a avisar no texto:** 4.6.1 e os Quadros 12 e 13 falam em "plataforma como serviço" e "PostgreSQL em instância gerenciada". Com a VM + Docker, esses trechos precisam passar a dizer "máquina virtual em nuvem com contêineres" e "PostgreSQL em contêiner". O argumento de 4.6.1 (nó comandado de fora da rede local) continua válido.

## Estrutura (dentro de `Codigo/`)

```
db/            schema.sql, seed.sql (classes P3–P6 do Quadro 8)
api_eventos/   FastAPI
decisao/       previsao.py, inferencia.py, verificacao.py, ciclo.py, mqtt.py, diagnostico.py, energia.py
painel/        HTML/CSS/JS (React)
firmware/      ESP32
broker/        configuração do Mosquitto (TLS, senhas/ACL por dispositivo)
cenarios/      suíte de cenários JSON + envelope esperado + executor (RF10), com modo reativo × antecipado
modelo/        notebook de treino (Melbourne) → modelo salvo
tests/         testes de RNF01, RNF02, RNF04...
docker-compose.yml
```

## Ordem de desenvolvimento combinada

1. `db/schema.sql` + `seed.sql` ✅ (revisado no passo 0 para a versão nova do TCC)
2. `decisao/verificacao.py` + testes aleatórios (100 mil casos, zero violações de piso e taxa) ✅
3. Inferência Mamdani com partições provisórias ✅ (`decisao/inferencia.py` + `decisao/regras/v0-provisoria.toml`; saída 0–1, atenuação condicionada à ausência de risco, reativo = prevista ← observada; itens 18–20 do DIVERGENCIAS)
4. API de eventos ✅ (`api_eventos/`: vocabulário fechado, extras → 422, sem autenticação por decisão do autor — reavaliar no deploy; datas voltam em UTC, o ciclo converte para America/Sao_Paulo)
5. `ciclo.py` com previsão provisória (persistência) publicando no Mosquitto local
6. Firmware com MQTT/TLS, PWM calibrado e failsafe → **fluxo completo funcionando**
7. Painel
8. Treino do modelo XGBoost (Etapa 3) e troca da previsão provisória
9. Cenários (RF10, com modo reativo), diagnóstico (RF11), energia (RF12)
10. Deploy na VM Oracle com Docker

## Decisões em aberto (perguntar ao autor antes de assumir)

- **Passo da rampa:** sugestão de um passo a cada 5 s (o Quadro 6 fala em ≈0,017 lux/s, ou seja, passo de 1 s). Cada passo gera uma linha em `decisao`.
- **Relógio de cenário:** a previsão usa janelas horárias, mas a rampa é em tempo real. Os cenários precisam de tempo acelerado para eventos/previsão e tempo real para a rampa.
- **Timeout do failsafe** (sugestão: 3× o período do ciclo).
- **N ciclos consecutivos** do alerta de perda de controle (RF11).
- **Horário da linha de base de atenuação fixa** (ex.: 0h–5h em P5).

## Hardware atual (já montado e testado)

- ESP32 DevKit 38 pinos na protoboard de 830 pontos, **USB para cima** (as legendas ficam embaixo da placa).
- BH1750 (GY-302) soldado: SDA = GPIO21, SCL = GPIO22, VCC = 3V3, endereço 0x23. Houve mau contato por solda, já resolvido.
- Módulo MOSFET D4184: TRIG/PWM = GPIO25, GND comum com o ESP32; VIN = fonte 12 V; OUT = fita LED 5050 branca de 12 V (uma cor, 2 fios).
- Na Arduino IDE, placa "DOIT ESP32 DEVKIT V1", porta COM3, core esp32 3.3.x (usa `ledcAttach` / `ledcWrite(pino, valor)`).
- Já funciona um sketch com fade de gama 2.2, PWM de 5 kHz/12 bits e leitura de lux simultânea (sem `delay` no fade).
- Pontos do TCC: PWM de 5 kHz/12 bits; comprimento do segmento ajustado até o duty pleno dar 1,5×–2× 10 lux; os duties de 10 lux e 5 lux devem ser **medidos na bancada**, não interpolados; BH1750 em modo de alta resolução 2.

## Regras para o Claude Code

- Rode os testes depois de mexer em `verificacao.py`; a camada de verificação nunca pode ter violação.
- Não coloque valores normativos fixos no código; leia do banco.
- Commits pequenos, com mensagem em português.
