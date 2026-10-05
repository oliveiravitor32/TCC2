# Roteiro da sessão final de bancada (CT15 a CT20)

Casos do Quadro 17 (4.8) que dependem do nó real e da VM. O resultado de cada
um entra em 4.10, 5.3 e 5.5. Os critérios são os do Quadro 17, fixados antes
da sessão: não mude o critério depois de ver o número.

Tempo total: cerca de 1 h 30 min, a maior parte esperando a rampa do CT18.

## Antes de começar

1. ESP32 ligado no USB, com o `no.ino` atual gravado, e a bancada fechada.
2. `Codigo/bancada/chave_vm.txt` com a `CHAVE_API` da VM.
3. **Monitor Serial fechado** (a conferência usa a COM3).
4. PowerShell na pasta `Codigo`. Todos os comandos abaixo são rodados ali.

## 0. Conferência (abre a sessão de medição na VM)

```powershell
.venv\Scripts\python -m bancada.conferir --vm
```

Tem de sair **APROVADA**. Se reprovar, aceite recalibrar. Anote o número da
sessão: é ela que dá a residual descontada em todas as medições seguintes.

## CT19 — recusa sem credencial (RNF06) · ~10 s

```powershell
.venv\Scripts\python -m bancada.sessao_ct credencial
```

Tenta entrar no broker da VM sem credencial, com senha errada e com a
credencial do nó. Aprovado: as duas primeiras **recusadas** e a terceira
**aceita** com TLS. (Já rodado em 04/10/2026: APROVADO, TLS 1.3.)

## CT15 e CT17 — fluxo completo e latência (RF05, RF06, RNF03) · ~12 min

```powershell
.venv\Scripts\python -m bancada.sessao_ct latencia
```

Publica 30 ocorrências, uma a cada 20 s, no trecho do BANCADA-01, e mede, para
cada uma, o tempo da gravação do evento até a telemetria chegar na VM, além do
lux medido contra o esperado.

- **CT17 aprovado:** todas as 30 abaixo de 2 s.
- **CT15 aprovado:** em todas, o lux corresponde ao nível emitido, dentro da
  tolerância do diagnóstico.

A latência medida vai até a **telemetria**, que inclui a leitura do sensor
(até ~1,3 s). É um limite superior do tempo até o duty aplicado. Se passar de
2 s, não mude nada: anote e me mande o arquivo, porque a explicação entra no
texto.

## CT16 — falha total detectada (RF11) · ~3 min

1. Num terminal, deixe rodando:

   ```powershell
   .venv\Scripts\python -m bancada.sessao_ct alertas
   ```

2. **Desligue a fonte de 12 V** da fita (tire da tomada). O ESP32 continua
   ligado pelo USB.
3. Em cerca de 15 s (três ciclos) deve aparecer `falha_total ABERTO`.
4. **Religue a fonte.** Deve aparecer `ENCERRADO`.
5. `Ctrl+C` para parar e gravar o registro.

## CT18 — failsafe partindo do piso (RNF07) · ~10 a 30 min

1. Leve o nó ao piso (publica volume zero a cada 5 min e acompanha):

   ```powershell
   .venv\Scripts\python -m bancada.sessao_ct piso
   ```

   A descida leva no mínimo 5 min (rampa da norma). Rode num horário de pouco
   movimento **previsto** (de madrugada é o mais seguro): com previsão média,
   a regra R6 segura a luz uma classe acima do piso.

2. Quando aparecer **NO PISO**, abra o Monitor Serial e, **na VM**, pare o
   serviço de decisão:

   ```bash
   docker compose -f docker-compose.prod.yml stop decisao
   ```

3. No serial: em até 15 s deve aparecer `FAILSAFE: sem comando ha 15 s -> nivel 1,0`
   e as linhas `failsafe: nivel 1,000 ... lux ~10`. Copie essas linhas
   (com o lux de antes e de depois) para um arquivo: são a evidência.
   Aprovado: nó no pleno em até 15 s, **medido pelo sensor**.
4. Volte o serviço:

   ```bash
   docker compose -f docker-compose.prod.yml start decisao
   ```

## CT20 — segundo ponto de luz sem mudar o serviço (RNF09) · ~5 min

O segundo nó é o **simulado** (o lux dele é sintético; o caso testa só que o
serviço comanda um ponto novo sem alteração de código).

1. **Na VM**, uma vez, dê credencial ao SIMULADO-02 (mostra a senha uma vez só;
   guarde):

   ```bash
   ./deploy/novo_no.sh SIMULADO-02
   ```

   Se disser que já tem credencial, use a senha guardada antes.

2. **No notebook**, ligue o nó simulado na VM:

   ```powershell
   $env:MQTT_HOST = "tcc-iluminacao-publica.duckdns.org"
   $env:MQTT_PORTA = "8883"
   $env:MQTT_USUARIO = "SIMULADO-02"
   $env:MQTT_SENHA = "SENHA_DO_PASSO_1"
   $env:MQTT_CA = "ca_vm.crt"
   .venv\Scripts\python -m simulador.no_simulado --ponto SIMULADO-02
   ```

3. Aprovado: no painel, o SIMULADO-02 passa a receber decisões e a mostrar
   telemetria, sem nenhum `git pull` nem rebuild do serviço na VM.

## Depois da sessão

Mande os arquivos de `bancada/resultados/` (`ct*_*.json`, a conferência e o
texto do serial do CT18). Com eles eu redijo 4.10 (resultado de CT15 a CT20),
5.3 (latência e diagnóstico) e a energia de bancada em 5.5.
