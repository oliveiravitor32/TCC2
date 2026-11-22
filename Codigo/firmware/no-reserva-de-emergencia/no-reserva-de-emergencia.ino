// RESERVA DE EMERGENCIA do no de iluminacao - so para demonstracao, FORA do
// TCC (como o modo de teste do painel). Copia de firmware/no/no.ino com duas
// diferencas, para o segundo ESP32 funcionar longe do notebook:
//
//   A. CALIBRACAO AUTOMATICA ao ligar: mede a residual, confere o pleno, a
//      classe intermediaria e o piso pela tabela gravada (mesma tolerancia
//      da conferencia) e, se reprovar, recalibra sozinho (duty de 10 lx e de
//      5 lx MEDIDOS + varredura) e grava a tabela na memoria. Caixa aberta
//      (residual > 5 % da classe) = nao calibra e mantem a tabela. Com
//      RECALIBRAR_SEMPRE = true (padrao), recalibra a CADA boot, sem
//      conferir antes; com false, so quando reprova ou com o BOOT apertado.
//      Nada disso vai para o banco: nao e resultado (3.4.4 descreve a calibracao pelo computador).
//   B. WI-FI SO COM REDES CONHECIDAS: a de WIFI_SSID, o hotspot combinado
//      (WIFI_RESERVA_SSID) e a salva pelo portal; fica com a mais forte que
//      aparecer e tenta em loop ate conectar, de novo a cada reset. NUNCA
//      tenta redes fora dessa lista. Sem Wi-Fi por 2 min, abre tambem o
//      PORTAL: rede "TCC-NO-RESERVA" (senha PORTAL_SENHA); pelo celular,
//      abrir http://192.168.4.1, escolher a rede e digitar a senha.
//
// LED azul da placa: piscando rapido = calibrando; piscando devagar =
// procurando Wi-Fi; aceso = conectado; 3 piscadas longas depois da
// calibracao = aviso (caixa aberta, fita fraca ou forte demais; ver a serial).
//
// Usa a MESMA credencial do broker que a BANCADA-01: so um dos dois ESP32
// pode ficar ligado por vez (o broker derruba o mais antigo).
//
// ---- texto original do no.ino ----
// Firmware do no de iluminacao (TCC 3.4, 4.6.1, Quadro 14).
//
// O no NAO decide. Ele e o controlador da arquitetura de implantacao
// (DIVERGENCIAS 71; Caderno de Encargos 7.1.1: a logica roda no controlador):
//   1. assina iluminacao/{ponto}/comando e recebe {decisao_id, nivel,
//      validade_s, piso, taxa_min}; o nivel e o ALVO, ja verificado na central;
//   2. sobe na hora; desce ate o alvo em RAMPA, a cada 5 s, no maximo
//      taxa_min por minuto, e nunca abaixo do piso (segunda barreira). A conta
//      e a mesma da camada de verificacao (decisao/verificacao.py,
//      decisao/rampa.py), com 3 casas;
//   3. converte o nivel (fracao do fluxo pleno) em ciclo de trabalho pela
//      tabela de calibracao MEDIDA na bancada (calibracao.h, 3.3), aplica o
//      PWM (5 kHz, 12 bits) e mede a iluminancia (BH1750);
//   4. publica em iluminacao/{ponto}/telemetria {decisao_id, duty, lux, nivel,
//      medido_em} - o decisao_id liga a leitura a decisao (4.6.2) e o nivel e o
//      que estava aplicado (no meio da rampa, ainda nao e o alvo);
//   5. FAILSAFE (RNF07): vencida a validade do comando (contada no relogio do
//      proprio no, a partir do recebimento) sem comando novo, vai ao pleno.
//   6. MANUTENCAO pela serial (bancada/conferir.py e bancada/calibrar.py):
//      conferencia e recalibracao sem trocar de sketch. Enquanto dura, o no
//      ignora os comandos do servico e o failsafe (quem controla a luz e a
//      conferencia) e publica o estado "manutencao". Sai com "X" ou sozinho
//      depois de 20 s sem conversa na serial, voltando ao pleno.
//
// Protocolo serial (115200, uma linha por comando; respostas iniciadas por
// "OK", "L", "FIM", "ID" ou "ERRO"; linhas de log comecam por outra coisa):
//   ?                 -> "ID no v1 <ponto> sessao <n>"
//   D <n>             -> aplica duty n (0..4095)          -> "OK D <n>"
//   N <nivel>         -> aplica o nivel pela tabela        -> "OK N <nivel> <duty>"
//   M <k>             -> k leituras (1..50)                -> "L <lux>" x k, "FIM"
//   T <n> <sessao>    -> comeca tabela nova de n pontos    -> "OK T <n>"
//   P <nivel> <duty>  (n vezes)                            -> "OK P <i>"
//   T FIM             -> confere e grava na memoria (NVS)  -> "OK T <n> <sessao>"
//   X                 -> sai da manutencao                 -> "OK X"
//
// A tabela gravada pela serial vale sobre a de calibracao.h, que fica como
// registro e como padrao de fabrica; "T 0 0" seguido de "T FIM" apaga a
// gravada e volta a de calibracao.h.
//
// Configuracao em segredos.h (copie de segredos.exemplo.h).
//
// MQTT: usa o cliente nativo do ESP32 (esp-mqtt), que dispensa instalar
// biblioteca. No nucleo Arduino ele vem com o protocolo 3.1.1 (o 5 esta
// desligado na compilacao do nucleo); o broker e o servico usam MQTT 5 e os
// dois conversam normalmente. QoS 1, last will e TLS existem no 3.1.1.
//
// Ligacoes: BH1750 SDA=21, SCL=22, VCC=3V3, 0x23 | D4184 TRIG=25, GND comum.

#include <WiFi.h>
#include <Wire.h>
#include <BH1750.h>
#include <time.h>
#include <Preferences.h>
#include <WiFiMulti.h>
#include <WebServer.h>
#include <DNSServer.h>
#include "mqtt_client.h"

#include "calibracao.h"
#include "segredos.h"

// ---- Parametros ------------------------------------------------------------
const int PINO_PWM = 25;
const int FREQ_PWM = 5000;
const int BITS_PWM = 12;
const int DUTY_MAX = 4095;

// Passo da rampa (DIVERGENCIAS 1 e 71): com 0,1/min e 3 casas, 5 s da a
// rampa P3 -> P5 em 5,2 min, a mesma da central e dos cenarios.
const unsigned long PASSO_RAMPA_MS = 5000;

// O BH1750 mede continuamente: as leituras logo apos trocar o duty ainda sao
// de conversoes iniciadas ANTES da troca. Mesma regra da calibracao
// (bancada/calibrar.py, DIVERGENCIAS item 44).
const int LEITURAS_DESCARTADAS = 2;

const char *TOPICO_COMANDO    = "iluminacao/" PONTO "/comando";
const char *TOPICO_TELEMETRIA = "iluminacao/" PONTO "/telemetria";
const char *TOPICO_ESTADO     = "iluminacao/" PONTO "/estado";

// Sem conversa na serial por este tempo, a manutencao termina sozinha: o no
// nunca fica preso fora do controle do servico (cabo puxado, script parado).
const unsigned long TIMEOUT_MANUTENCAO_MS = 20000;
const int MAX_PONTOS_TABELA = 48;

// ---- Estado ----------------------------------------------------------------
struct Comando {
  char decisao_id[40];
  float nivel;              // alvo
  unsigned long validade_s;
  float piso;
  float taxa_min;           // decrescimo maximo por minuto
  bool imediato;            // modo de teste do painel: sem rampa (piso vale)
};

BH1750 sensor(0x23);
esp_mqtt_client_handle_t cliente = nullptr;
QueueHandle_t filaComandos;  // o evento MQTT roda em outra tarefa: fila entre elas

float nivelAtual = 1.0f;
int dutyAtual = 0;
unsigned long ultimoComando = 0;  // millis() do recebimento
unsigned long validadeMs = 0;
unsigned long ultimoPasso = 0;
float alvo = 1.0f, pisoCmd = 1.0f, taxaCmd = 0.0f;
bool emFailsafe = true;           // ate o primeiro comando, o no esta no pleno
char decisaoPendente[40] = "";    // telemetria ainda devida
int leiturasADescartar = 0;
float ultimaLux = -1;
// Estado quando o comando pendente chegou, antes de aplica-lo (migracao 010):
// e onde a rampa anterior terminou. Vai junto da telemetria dessa decisao.
float nivelAntesPendente = -1;
float luxAntesPendente = -1;
// Sem sensor no inicio, nao se le: a biblioteca imprimiria "Device is not
// configured" a cada volta do loop e afogaria o serial.
bool sensorOk = false;

// Tabela em uso: a gravada na NVS, se houver; senao, a de calibracao.h.
PontoCalibracao tabela[MAX_PONTOS_TABELA];
int nTabela = 0;
int sessaoTabela = 0;
PontoCalibracao tabelaNova[MAX_PONTOS_TABELA];  // em recepcao pela serial
int nNova = -1, recebidosNova = 0, sessaoNova = 0;
Preferences prefs;

bool emManutencao = false;
unsigned long ultimaSerial = 0;
String linhaSerial;

// ---- Nivel -> duty -----------------------------------------------------------
// Interpolacao linear entre pontos MEDIDOS da tabela. Os niveis 1,0 e do
// piso caem exatamente nos duties medidos (3.4.2); so os intermediarios sao
// interpolados, entre vizinhos medidos a poucos % de distancia (item 29).
int dutyDoNivel(float nivel) {
  if (nivel <= tabela[0].nivel) return tabela[0].duty;
  for (int i = 1; i < nTabela; i++) {
    if (nivel <= tabela[i].nivel) {
      const PontoCalibracao &a = tabela[i - 1], &b = tabela[i];
      float f = (nivel - a.nivel) / (b.nivel - a.nivel);
      return (int)lroundf(a.duty + f * (b.duty - a.duty));
    }
  }
  // Acima de 1,0 nao existe: o maximo e o duty MEDIDO do pleno, nunca 4095.
  return tabela[nTabela - 1].duty;
}

// Mesma regra para a tabela de fabrica e para a recebida: comeca em (0, 0),
// termina em 1,0 e cresce estritamente nas duas colunas.
bool tabelaValida(const PontoCalibracao *t, int n) {
  if (n < 2 || n > MAX_PONTOS_TABELA) return false;
  if (t[0].nivel != 0.0f || t[0].duty != 0 || fabsf(t[n - 1].nivel - 1.0f) > 1e-4f) return false;
  for (int i = 1; i < n; i++) {
    if (t[i].nivel <= t[i - 1].nivel || t[i].duty <= t[i - 1].duty || t[i].duty > DUTY_MAX)
      return false;
  }
  return true;
}

void carregarTabela() {
  prefs.begin("calibracao", true);
  int n = prefs.getInt("n", 0);
  if (n > 0 && n <= MAX_PONTOS_TABELA &&
      prefs.getBytes("pontos", tabela, sizeof(PontoCalibracao) * n) == sizeof(PontoCalibracao) * n &&
      tabelaValida(tabela, n)) {
    nTabela = n;
    sessaoTabela = prefs.getInt("sessao", 0);
    prefs.end();
    return;
  }
  prefs.end();
  memcpy(tabela, CALIBRACAO, sizeof(PontoCalibracao) * N_CALIBRACAO);
  nTabela = N_CALIBRACAO;
  sessaoTabela = CALIBRACAO_SESSAO;
}

// 3 casas, como NUMERIC(4,3) e a verificacao da central.
float tresCasas(float x) { return lroundf(x * 1000.0f) / 1000.0f; }

void aplicarNivel(float nivel) {
  nivel = constrain(nivel, 0.0f, 1.0f);
  nivelAtual = nivel;
  dutyAtual = dutyDoNivel(nivel);
  ledcWrite(PINO_PWM, dutyAtual);
  leiturasADescartar = LEITURAS_DESCARTADAS;
}

// ---- Carga dos topicos -------------------------------------------------------
// JSON pequeno e de formato fixo: extraido a mao, sem biblioteca extra.
bool extrairNumero(const char *buf, const char *chave, float &saida) {
  const char *n = strstr(buf, chave);
  if (!n) return false;
  n = strchr(n + strlen(chave), ':');
  if (!n) return false;
  char *depois;
  saida = strtof(n + 1, &depois);
  return depois != n + 1;
}

bool extrairComando(const char *dados, int tam, Comando &c) {
  char buf[220];
  if (tam <= 0 || tam >= (int)sizeof(buf)) return false;
  memcpy(buf, dados, tam);
  buf[tam] = '\0';

  const char *p = strstr(buf, "\"decisao_id\"");
  if (!p) return false;
  p = strchr(p + 12, ':');
  if (!p) return false;
  p = strchr(p, '"');
  if (!p) return false;
  const char *fim = strchr(p + 1, '"');
  if (!fim || fim - p - 1 >= (int)sizeof(c.decisao_id)) return false;
  memcpy(c.decisao_id, p + 1, fim - p - 1);
  c.decisao_id[fim - p - 1] = '\0';

  float v;
  if (!extrairNumero(buf, "\"nivel\"", v) || v < 0 || v > 1) return false;
  c.nivel = v;
  if (!extrairNumero(buf, "\"validade_s\"", v) || v < 1) return false;
  c.validade_s = (unsigned long)v;
  if (!extrairNumero(buf, "\"piso\"", v) || v < 0 || v > 1) return false;
  c.piso = v;
  if (!extrairNumero(buf, "\"taxa_min\"", v) || v <= 0 || v > 1) return false;
  c.taxa_min = v;
  // Opcional (modo de teste do painel): "imediato": true -> sem rampa.
  const char *im = strstr(buf, "\"imediato\"");
  c.imediato = im && strstr(im, "true") != nullptr;
  return true;
}

void carimboAgora(char *saida, size_t tam) {
  // Sem hora sincronizada (NTP), manda vazio: o servidor usa a hora de
  // recebimento, e a latencia do RNF03 ja e medida so com relogios do
  // servidor (DIVERGENCIAS item 25).
  time_t agora = time(nullptr);
  if (agora < 1700000000) { saida[0] = '\0'; return; }
  struct tm utc;
  gmtime_r(&agora, &utc);
  strftime(saida, tam, "%Y-%m-%dT%H:%M:%SZ", &utc);
}

void publicarTelemetria(const char *decisao_id, float lux) {
  if (!cliente) return;
  char quando[32], antes[64] = "", carga[280];
  carimboAgora(quando, sizeof(quando));
  // Estado antes do comando: so se havia leitura (o primeiro comando apos
  // ligar pode chegar antes da primeira medicao do sensor).
  if (nivelAntesPendente >= 0 && luxAntesPendente >= 0) {
    snprintf(antes, sizeof(antes), ",\"nivel_antes\":%.3f,\"lux_antes\":%.2f",
             nivelAntesPendente, luxAntesPendente);
  }
  int n = snprintf(carga, sizeof(carga),
                   "{\"decisao_id\":\"%s\",\"duty\":%.4f,\"lux\":%.2f,\"nivel\":%.3f%s%s%s%s}",
                   decisao_id, dutyAtual / (float)DUTY_MAX, lux, nivelAtual, antes,
                   quando[0] ? ",\"medido_em\":\"" : "", quando, quando[0] ? "\"" : "");
  esp_mqtt_client_publish(cliente, TOPICO_TELEMETRIA, carga, n, 1, 0);  // QoS 1, sem retain
}

// ---- MQTT ------------------------------------------------------------------
static void aoEventoMqtt(void *, esp_event_base_t, int32_t id, void *dados) {
  auto ev = (esp_mqtt_event_handle_t)dados;
  switch ((esp_mqtt_event_id_t)id) {
    case MQTT_EVENT_CONNECTED:
      Serial.println("MQTT conectado");
      esp_mqtt_client_subscribe(ev->client, TOPICO_COMANDO, 1);
      // Estado retido: o servico marca o ponto como operante (LACUNA 2).
      esp_mqtt_client_publish(ev->client, TOPICO_ESTADO, "online", 0, 1, 1);
      break;
    case MQTT_EVENT_DISCONNECTED:
      Serial.println("MQTT desconectado (o cliente tenta de novo sozinho)");
      break;
    case MQTT_EVENT_DATA: {
      Comando c;
      if (extrairComando(ev->data, ev->data_len, c)) {
        xQueueSend(filaComandos, &c, 0);
      } else {
        Serial.println("comando malformado ignorado");
      }
      break;
    }
    case MQTT_EVENT_ERROR:
      Serial.println("MQTT: erro de conexao (broker, TLS ou credencial)");
      break;
    default:
      break;
  }
}

void iniciarMqtt() {
  esp_mqtt_client_config_t cfg = {};
  cfg.broker.address.uri = MQTT_URI;
  if (MQTT_CA_PEM) cfg.broker.verification.certificate = MQTT_CA_PEM;
  cfg.credentials.client_id = "no-" PONTO;
  if (strlen(MQTT_USUARIO)) {
    cfg.credentials.username = MQTT_USUARIO;
    cfg.credentials.authentication.password = MQTT_SENHA;
  }
  // Last will: se o no cair, o broker publica "offline" por ele.
  cfg.session.last_will.topic = TOPICO_ESTADO;
  cfg.session.last_will.msg = "offline";
  cfg.session.last_will.msg_len = 7;
  cfg.session.last_will.qos = 1;
  cfg.session.last_will.retain = 1;
  cfg.session.keepalive = 30;

  cliente = esp_mqtt_client_init(&cfg);
  esp_mqtt_client_register_event(cliente, MQTT_EVENT_ANY, aoEventoMqtt, nullptr);
  esp_mqtt_client_start(cliente);
}

// ---- Wi-Fi: redes conhecidas + portal (reserva de emergencia) ---------------
// So entra em redes desta lista: a de casa (WIFI_SSID), o hotspot combinado
// (WIFI_RESERVA_SSID) e a salva pelo portal. O WiFiMulti procura as redes,
// fica com a mais forte DA LISTA e tenta; sem nenhuma, tenta de novo depois.
const int LED_PLACA = 2;           // LED azul da DevKit
const int PINO_BOOT = 0;           // botao BOOT
const unsigned long PORTAL_APOS_MS = 120000;   // 2 min sem Wi-Fi -> portal
const unsigned long INTERVALO_REDES_MS = 10000;
const char *PORTAL_SSID = "TCC-NO-RESERVA";

WiFiMulti redes;
WebServer servidor(80);
DNSServer dns;
bool portalAberto = false;
String redeSalvaSsid, redeSalvaSenha;
String opcoesPortal;               // <option> das redes vistas ao abrir o portal

void prepararRedes() {
  redes.addAP(WIFI_SSID, WIFI_SENHA);
  redes.addAP(WIFI_RESERVA_SSID, WIFI_RESERVA_SENHA);
  prefs.begin("wifi", true);
  redeSalvaSsid = prefs.getString("ssid", "");
  redeSalvaSenha = prefs.getString("senha", "");
  prefs.end();
  if (redeSalvaSsid.length()) {
    redes.addAP(redeSalvaSsid.c_str(), redeSalvaSenha.c_str());
    Serial.printf("rede salva pelo portal: \"%s\"\n", redeSalvaSsid.c_str());
  }
  Serial.printf("redes conhecidas: \"%s\", \"%s\"%s\n", WIFI_SSID, WIFI_RESERVA_SSID,
                redeSalvaSsid.length() ? " e a do portal" : "");
}

// Uma volta: procura, escolhe a mais forte da lista e tenta por ate `ms`.
bool tentarRedes(uint32_t ms) {
  bool ok = redes.run(ms) == WL_CONNECTED;
  if (ok) {
    Serial.printf("Wi-Fi CONECTADO em \"%s\", IP %s, sinal %d dBm\n", WiFi.SSID().c_str(),
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
  } else {
    Serial.println("nenhuma rede conhecida respondeu; tenta de novo em 10 s");
  }
  return ok;
}

String escapar(const String &s) {
  String r;
  for (char c : s) {
    if (c == '<') r += "&lt;"; else if (c == '>') r += "&gt;";
    else if (c == '"') r += "&quot;"; else if (c == '&') r += "&amp;"; else r += c;
  }
  return r;
}

void paginaPortal() {
  String h = F("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
               "<title>No reserva</title><body style='font-family:sans-serif;max-width:420px;margin:20px auto;padding:0 12px'>"
               "<h2>No de iluminacao - Wi-Fi</h2><form method=post action=/salvar>"
               "<p>Rede:<br><select name=ssid style='width:100%;padding:8px'>");
  h += opcoesPortal;
  h += F("</select></p><p>Ou digite o nome:<br><input name=outra style='width:100%;padding:8px'></p>"
         "<p>Senha:<br><input name=senha type=password style='width:100%;padding:8px'></p>"
         "<p><button style='width:100%;padding:10px'>Salvar e conectar</button></p></form>"
         "<p><a href=/>atualizar a lista</a></p>");
  servidor.send(200, "text/html", h);
}

void salvarPortal() {
  String ssid = servidor.arg("outra");
  if (!ssid.length()) ssid = servidor.arg("ssid");
  String senha = servidor.arg("senha");
  if (!ssid.length()) { servidor.send(400, "text/plain", "escolha uma rede"); return; }
  prefs.begin("wifi", false);
  prefs.putString("ssid", ssid);
  prefs.putString("senha", senha);
  prefs.end();
  redeSalvaSsid = ssid; redeSalvaSenha = senha;
  redes.addAP(redeSalvaSsid.c_str(), redeSalvaSenha.c_str());
  servidor.send(200, "text/html",
                "<meta charset=utf-8><body style='font-family:sans-serif'>Salvo: <b>" + escapar(ssid) +
                "</b>. O no tenta conectar agora; o portal fecha quando conseguir.");
  Serial.printf("portal: rede \"%s\" salva\n", ssid.c_str());
  WiFi.begin(redeSalvaSsid.c_str(), redeSalvaSenha.c_str());
}

void abrirPortal() {
  if (portalAberto) return;
  // Lista as redes antes de abrir (com o portal aberto, o scan atrapalha).
  int n = WiFi.scanNetworks();
  opcoesPortal = "";
  for (int i = 0; i < n; i++) {
    String s = escapar(WiFi.SSID(i));
    if (s.length()) opcoesPortal += "<option>" + s + "</option>";
  }
  WiFi.scanDelete();
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(PORTAL_SSID, PORTAL_SENHA);
  dns.start(53, "*", WiFi.softAPIP());  // qualquer endereco cai no portal
  servidor.on("/", paginaPortal);
  servidor.on("/salvar", HTTP_POST, salvarPortal);
  servidor.onNotFound(paginaPortal);
  servidor.begin();
  portalAberto = true;
  Serial.printf("PORTAL aberto: rede \"%s\", abra http://%s no celular\n", PORTAL_SSID,
                WiFi.softAPIP().toString().c_str());
}

void fecharPortal() {
  if (!portalAberto) return;
  servidor.stop();
  dns.stop();
  WiFi.softAPdisconnect(true);
  WiFi.mode(WIFI_STA);
  portalAberto = false;
  Serial.println("portal fechado (Wi-Fi conectado)");
}

// ---- Manutencao pela serial ------------------------------------------------
void publicarEstado(const char *estado) {
  if (cliente) esp_mqtt_client_publish(cliente, TOPICO_ESTADO, estado, 0, 1, 1);
}

void entrarManutencao() {
  if (emManutencao) return;
  emManutencao = true;
  decisaoPendente[0] = '\0';
  publicarEstado("manutencao");
  Serial.println("# manutencao: comandos do servico ignorados");
}

void sairManutencao() {
  if (!emManutencao) return;
  emManutencao = false;
  nNova = -1;
  // Volta ao pleno e espera o servico: e o mesmo estado do failsafe, de modo
  // que a rampa recomeca do pleno (CT07).
  aplicarNivel(1.0f);
  emFailsafe = true;
  Comando descartado;
  while (xQueueReceive(filaComandos, &descartado, 0) == pdTRUE) {}
  publicarEstado("online");
  Serial.println("# manutencao encerrada: nivel 1,0, aguardando o servico");
}

float lerLuxBloqueando() {
  if (!sensorOk) return -1;
  unsigned long limite = millis() + 2000;
  while (!sensor.measurementReady(false)) {
    if (millis() > limite) return -1;
    delay(10);
  }
  return sensor.readLightLevel();
}

void tratarSerial(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  if (cmd == "?") {
    Serial.printf("ID no v1 %s sessao %d\n", PONTO, sessaoTabela);
    return;
  }
  entrarManutencao();
  if (cmd == "X") {
    Serial.println("OK X");
    sairManutencao();
  } else if (cmd.startsWith("D ")) {
    long n = cmd.substring(2).toInt();
    if (n < 0 || n > DUTY_MAX) { Serial.println("ERRO duty fora de 0..4095"); return; }
    dutyAtual = n;
    ledcWrite(PINO_PWM, n);
    Serial.printf("OK D %ld\n", n);
  } else if (cmd.startsWith("N ")) {
    float nivel = cmd.substring(2).toFloat();
    if (nivel < 0 || nivel > 1) { Serial.println("ERRO nivel fora de 0..1"); return; }
    aplicarNivel(nivel);
    Serial.printf("OK N %.4f %d\n", nivel, dutyAtual);
  } else if (cmd.startsWith("M ")) {
    long k = cmd.substring(2).toInt();
    if (k < 1 || k > 50) { Serial.println("ERRO k fora de 1..50"); return; }
    for (long i = 0; i < k; i++) {
      float lux = lerLuxBloqueando();
      if (lux < 0) { Serial.println("ERRO leitura do sensor falhou"); return; }
      Serial.printf("L %.2f\n", lux);
    }
    Serial.println("FIM");
  } else if (cmd == "T FIM") {
    if (nNova < 0 || recebidosNova != nNova) { Serial.println("ERRO tabela incompleta"); return; }
    if (nNova > 0 && !tabelaValida(tabelaNova, nNova)) {
      nNova = -1;
      Serial.println("ERRO tabela invalida");
      return;
    }
    prefs.begin("calibracao", false);
    if (nNova == 0) {
      prefs.clear();
      prefs.end();
      carregarTabela();
    } else {
      prefs.putBytes("pontos", tabelaNova, sizeof(PontoCalibracao) * nNova);
      prefs.putInt("sessao", sessaoNova);
      prefs.putInt("n", nNova);
      prefs.end();
      memcpy(tabela, tabelaNova, sizeof(PontoCalibracao) * nNova);
      nTabela = nNova;
      sessaoTabela = sessaoNova;
    }
    nNova = -1;
    Serial.printf("OK T %d %d\n", nTabela, sessaoTabela);
  } else if (cmd.startsWith("T ")) {
    int n = 0, sessao = 0;
    if (sscanf(cmd.c_str() + 2, "%d %d", &n, &sessao) != 2 || n < 0 || n > MAX_PONTOS_TABELA) {
      Serial.println("ERRO cabecalho de tabela");
      return;
    }
    nNova = n; recebidosNova = 0; sessaoNova = sessao;
    Serial.printf("OK T %d\n", n);
  } else if (cmd.startsWith("P ")) {
    float nivel; int duty;
    if (nNova < 0 || recebidosNova >= nNova ||
        sscanf(cmd.c_str() + 2, "%f %d", &nivel, &duty) != 2) {
      Serial.println("ERRO ponto de tabela");
      return;
    }
    tabelaNova[recebidosNova++] = {nivel, duty};
    Serial.printf("OK P %d\n", recebidosNova);
  } else {
    Serial.println("ERRO comando desconhecido");
  }
}

void lerSerial() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') {
      ultimaSerial = millis();
      tratarSerial(linhaSerial);
      linhaSerial = "";
    } else if (ch != '\r' && linhaSerial.length() < 120) {
      linhaSerial += ch;
    }
  }
  if (emManutencao && millis() - ultimaSerial > TIMEOUT_MANUTENCAO_MS) {
    Serial.println("# 20 s sem serial");
    sairManutencao();
  }
}

// ---- Calibracao automatica (reserva de emergencia) ---------------------------
// A mesma conta de bancada/conferir.py e bancada/calibrar.py, feita no proprio
// ESP32, sem o computador e sem gravar no banco (nao e resultado).
// Classe P3 do ponto BANCADA-01: os mesmos valores de calibracao.h.
const float LUX_CLASSE = 10.0f;     // nivel 1,0 (P3)
const float LUX_PISO = 5.0f;        // nivel 0,5 (P5)
const float RESIDUAL_MAX = 0.05f;   // fracao da classe (3.4.3)
const float TOLERANCIA = 0.034f;    // a da ultima conferencia (sessao 124)
const float TETO_MIN = 1.5f, TETO_MAX = 2.0f;  // 3.4.2
const int SESSAO_AUTO = 9000;       // sessao "9000" = gravada por este firmware
const bool RECALIBRAR_SEMPRE = true; // recalibra a cada boot (decisao do autor)
bool avisoCalibracao = false;

void piscarLed() { digitalWrite(LED_PLACA, (millis() / 100) % 2); }

// Media de k leituras depois de descartar as anteriores a troca de duty.
float medirDuty(int duty, int k = 3) {
  ledcWrite(PINO_PWM, duty);
  dutyAtual = duty;
  delay(300);
  for (int i = 0; i < LEITURAS_DESCARTADAS; i++) { lerLuxBloqueando(); piscarLed(); }
  float soma = 0;
  int ok = 0;
  for (int i = 0; i < k; i++) {
    float l = lerLuxBloqueando();
    piscarLed();
    if (l >= 0) { soma += l; ok++; }
  }
  return ok ? soma / ok : -1;
}

// Bissecao no hardware: o duty e o que o sensor mede.
int buscarDuty(float alvoLiquido, float residual, int lo, int hi) {
  while (hi - lo > 1) {
    int meio = (lo + hi) / 2;
    if (medirDuty(meio) - residual < alvoLiquido) lo = meio; else hi = meio;
  }
  float eLo = fabsf(medirDuty(lo) - residual - alvoLiquido);
  float eHi = fabsf(medirDuty(hi) - residual - alvoLiquido);
  return eLo < eHi ? lo : hi;
}

// Confere 1,0 / 0,75 / 0,5 pela tabela em uso (como bancada/conferir.py).
bool conferirTabela(float residual) {
  const float niveis[] = {1.0f, 0.75f, 0.5f};
  bool aprovada = true;
  for (float n : niveis) {
    float liquido = medirDuty(dutyDoNivel(n), 5) - residual;
    float esperado = n * LUX_CLASSE;
    float desvio = (liquido - esperado) / esperado;
    bool ok = fabsf(desvio) <= TOLERANCIA;
    aprovada &= ok;
    Serial.printf("  nivel %.3f (duty %d): %.2f lx de %.2f (%+.1f%%) %s\n", n, dutyDoNivel(n),
                  liquido, esperado, desvio * 100, ok ? "ok" : "FORA");
  }
  return aprovada;
}

bool recalibrar(float residual) {
  float teto = medirDuty(DUTY_MAX, 5) - residual;
  Serial.printf("teto liquido %.2f lx (%.2fx)\n", teto, teto / LUX_CLASSE);
  if (teto < LUX_CLASSE * 1.02f) {
    Serial.println("ERRO: nem o duty maximo chega a 10 lx (mau contato na fita? LED longe do sensor?)."
                   " Tabela mantida.");
    return false;
  }
  if (teto / LUX_CLASSE < TETO_MIN || teto / LUX_CLASSE > TETO_MAX) {
    Serial.println("AVISO: teto fora de 1,5x-2,0x (3.4.2); calibra assim mesmo (so demonstracao)");
    avisoCalibracao = true;
  }
  int dPleno = buscarDuty(LUX_CLASSE, residual, 0, DUTY_MAX);
  int dPiso = buscarDuty(LUX_PISO, residual, 0, dPleno);
  Serial.printf("duty 10 lx = %d | duty 5 lx = %d (medidos)\n", dPleno, dPiso);

  // Varredura de 128 em 128 ate o pleno, mais os dois duties medidos.
  PontoCalibracao t[MAX_PONTOS_TABELA];
  int n = 0;
  t[n++] = {0.0f, 0};
  for (int d = 128; d < dPleno && n < MAX_PONTOS_TABELA - 2; d += 128) {
    float nivel = (medirDuty(d) - residual) / LUX_CLASSE;
    if (d > dPiso && t[n - 1].duty < dPiso) {
      t[n++] = {LUX_PISO / LUX_CLASSE, dPiso};  // piso no lugar exato
    }
    if (d == dPiso) continue;
    float limite = d < dPiso ? LUX_PISO / LUX_CLASSE : 1.0f;  // ruido nao cruza o piso
    if (nivel > t[n - 1].nivel && nivel < limite && d > t[n - 1].duty) {
      t[n++] = {roundf(nivel * 10000) / 10000, d};
    }
  }
  if (t[n - 1].duty < dPiso) t[n++] = {LUX_PISO / LUX_CLASSE, dPiso};
  t[n++] = {1.0f, dPleno};
  if (!tabelaValida(t, n)) {
    Serial.println("ERRO: curva medida nao ficou monotona; tabela mantida.");
    return false;
  }
  int sessao = SESSAO_AUTO + (sessaoTabela >= SESSAO_AUTO ? sessaoTabela - SESSAO_AUTO + 1 : 0);
  prefs.begin("calibracao", false);
  prefs.putBytes("pontos", t, sizeof(PontoCalibracao) * n);
  prefs.putInt("sessao", sessao);
  prefs.putInt("n", n);
  prefs.end();
  memcpy(tabela, t, sizeof(PontoCalibracao) * n);
  nTabela = n;
  sessaoTabela = sessao;
  Serial.printf("tabela nova gravada na memoria (%d pontos, sessao %d)\n", n, sessao);
  return true;
}

void autoCalibrar(bool forcar) {
  if (!sensorOk) {
    Serial.println("CALIBRACAO PULADA: sem sensor.");
    avisoCalibracao = true;
  } else {
    Serial.println("== calibracao automatica ==");
    float residual = medirDuty(0, 10);
    Serial.printf("residual %.2f lx\n", residual);
    if (residual < 0 || residual > RESIDUAL_MAX * LUX_CLASSE) {
      Serial.println("CAIXA ABERTA (residual > 5 % da classe): nao calibra; tabela mantida.");
      avisoCalibracao = true;
    } else if (!forcar && conferirTabela(residual)) {
      Serial.println("conferencia APROVADA: tabela mantida");
    } else {
      Serial.println(forcar ? "recalibrando (forcado)..." : "conferencia REPROVADA: recalibrando...");
      if (recalibrar(residual)) {
        Serial.println(conferirTabela(residual) ? "conferencia final APROVADA"
                                                : "conferencia final ainda FORA (ver a serial)");
      } else {
        avisoCalibracao = true;
      }
    }
  }
  if (avisoCalibracao) {  // 3 piscadas longas
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PLACA, HIGH); delay(700);
      digitalWrite(LED_PLACA, LOW); delay(400);
    }
  }
  digitalWrite(LED_PLACA, LOW);
}

// ---- Setup / loop ------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(200);
  carregarTabela();
  Serial.printf("\nno %s | calibracao da sessao %d (%s)\n", PONTO, sessaoTabela,
                sessaoTabela == CALIBRACAO_SESSAO ? "calibracao.h" : "gravada pela serial");

  // Luz primeiro: ao energizar, o no fica no PLENO ate receber comando
  // (LACUNA 3). Nunca comeca apagado.
  ledcAttach(PINO_PWM, FREQ_PWM, BITS_PWM);
  aplicarNivel(1.0f);

  Wire.begin(21, 22);
  sensorOk = sensor.begin(BH1750::CONTINUOUS_HIGH_RES_MODE_2);
  if (sensorOk) {
    sensor.setMTreg(BH1750_MTREG_MAX);  // o mesmo modo da calibracao
  } else {
    Serial.println("ERRO: BH1750 nao encontrado - confira VCC=3V3, GND, SDA=21, SCL=22 e a solda.");
    Serial.println("      A luz segue funcionando; sem leitura, nao ha telemetria nem conferencia.");
  }

  filaComandos = xQueueCreate(8, sizeof(Comando));

  // A. Calibracao automatica (o no controla a propria luz enquanto isso).
  pinMode(LED_PLACA, OUTPUT);
  pinMode(PINO_BOOT, INPUT_PULLUP);
  // Decisao do autor (22/11/2026): recalibra SEMPRE que liga, sem depender
  // da conferencia. Para voltar a so recalibrar quando reprovar, troque
  // RECALIBRAR_SEMPRE para false (o BOOT pressionado continua forcando).
  bool forcar = RECALIBRAR_SEMPRE || digitalRead(PINO_BOOT) == LOW;
  if (forcar) Serial.println("recalibracao forcada (a cada boot)");
  autoCalibrar(forcar);
  aplicarNivel(1.0f);  // volta ao pleno ate o primeiro comando (LACUNA 3)

  // B. Wi-Fi pelas redes conhecidas (sem conseguir, o loop segue tentando).
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  prepararRedes();
  Serial.println("procurando redes conhecidas...");
  tentarRedes(15000);

  configTime(0, 0, "pool.ntp.org", "time.google.com");  // hora UTC para medido_em
  // Com TLS, o certificado do broker so e aceito com a data certa: com o
  // relogio em 1970, ele parece "ainda nao valido". Espera o NTP ate 15 s;
  // sem hora, conecta mesmo assim (a reconexao automatica tenta de novo).
  Serial.print("acertando o relogio (NTP)");
  for (int i = 0; i < 30 && time(nullptr) < 1700000000; i++) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(time(nullptr) >= 1700000000 ? " ok" : " sem resposta; segue");
  iniciarMqtt();
}

// Sem Wi-Fi: tenta as redes conhecidas a cada 10 s, para sempre; depois de
// 2 min sem nenhuma, abre tambem o portal. Com alguem usando o portal, pausa
// as tentativas (a busca de redes troca de canal e derruba o celular).
void vigiarWifi() {
  static bool conectadoAntes = false;
  static unsigned long semWifiDesde = 0, ultimaTentativa = 0;
  bool conectado = WiFi.status() == WL_CONNECTED;

  if (conectado) {
    digitalWrite(LED_PLACA, HIGH);
    if (!conectadoAntes) {
      Serial.printf("Wi-Fi CONECTADO em \"%s\", IP %s\n", WiFi.SSID().c_str(),
                    WiFi.localIP().toString().c_str());
      fecharPortal();
    }
    conectadoAntes = true;
  } else {
    if (conectadoAntes || semWifiDesde == 0) {
      if (conectadoAntes) Serial.println("Wi-Fi CAIU (luz vai ao pleno pelo failsafe se nao houver comando)");
      semWifiDesde = millis();
    }
    conectadoAntes = false;
    digitalWrite(LED_PLACA, (millis() / 500) % 2);  // pisca devagar
    if (!portalAberto && millis() - semWifiDesde >= PORTAL_APOS_MS) abrirPortal();
    bool alguemNoPortal = portalAberto && WiFi.softAPgetStationNum() > 0;
    if (!alguemNoPortal && millis() - ultimaTentativa >= INTERVALO_REDES_MS) {
      tentarRedes(8000);
      ultimaTentativa = millis();
    }
  }
  if (portalAberto) {
    dns.processNextRequest();
    servidor.handleClient();
  }
}

void loop() {
  vigiarWifi();
  // 0. Serial: conferencia e recalibracao (bancada/conferir.py).
  lerSerial();
  if (emManutencao) {
    // Quem controla a luz e a conferencia: comandos do servico descartados,
    // sem failsafe e sem telemetria de decisao.
    Comando descartado;
    while (xQueueReceive(filaComandos, &descartado, 0) == pdTRUE) {}
    delay(5);
    return;
  }

  // 1. Comandos recebidos.
  Comando c;
  while (xQueueReceive(filaComandos, &c, 0) == pdTRUE) {
    if (decisaoPendente[0]) {
      // Chegou comando novo antes da leitura do anterior: aquela decisao
      // fica sem telemetria (a relacao e 1:1, mas nao obrigatoria).
      Serial.printf("decisao %s sem telemetria (substituida)\n", decisaoPendente);
    }
    // Antes de aplicar: o nivel em que o no estava e a ultima luz medida.
    nivelAntesPendente = nivelAtual;
    luxAntesPendente = ultimaLux;
    alvo = c.nivel;
    pisoCmd = ceilf(c.piso * 1000.0f - 1e-3f) / 1000.0f;  // piso para CIMA, como a central
    taxaCmd = c.taxa_min;
    validadeMs = c.validade_s * 1000UL;
    ultimoComando = millis();
    // Subir e na hora; descer e no passo da rampa (abaixo).
    float alvoEfetivo = max(alvo, pisoCmd);
    if (alvoEfetivo >= nivelAtual || c.imediato) aplicarNivel(alvoEfetivo);
    if (c.imediato) Serial.println("MODO TESTE: comando imediato, sem rampa");
    ultimoPasso = millis();
    strncpy(decisaoPendente, c.decisao_id, sizeof(decisaoPendente) - 1);
    if (emFailsafe) Serial.println("comando recebido: saindo do failsafe");
    emFailsafe = false;
    Serial.printf("alvo %.3f validade %lu s; nivel %.3f duty %d (%s)\n",
                  c.nivel, c.validade_s, nivelAtual, dutyAtual, c.decisao_id);
  }

  // 2. Failsafe (RNF07): comando vencido sem renovacao -> pleno. A subtracao
  //    de unsigned long continua certa quando o millis() da a volta (49 dias).
  if (!emFailsafe && millis() - ultimoComando >= validadeMs) {
    aplicarNivel(1.0f);
    emFailsafe = true;
    decisaoPendente[0] = '\0';
    Serial.printf("FAILSAFE: comando vencido (%lu s sem renovacao) -> nivel 1,0\n",
                  validadeMs / 1000);
  }

  // 3. Rampa: a cada 5 s, desce no maximo taxa x 5 s / 60 (arredondada para
  //    BAIXO a 3 casas, como a verificacao), sem passar do alvo nem do piso.
  if (!emFailsafe && millis() - ultimoPasso >= PASSO_RAMPA_MS) {
    ultimoPasso += PASSO_RAMPA_MS;
    float alvoEfetivo = max(alvo, pisoCmd);
    if (nivelAtual > alvoEfetivo) {
      float queda = floorf(taxaCmd * (PASSO_RAMPA_MS / 1000.0f) / 60.0f * 1000.0f + 1e-3f) / 1000.0f;
      float novo = tresCasas(max(alvoEfetivo, nivelAtual - queda));
      aplicarNivel(novo);
      Serial.printf("  rampa: nivel %.3f (alvo %.3f)\n", novo, alvoEfetivo);
    }
  }

  // 4. Leitura do sensor e telemetria da decisao pendente.
  if (sensorOk && sensor.measurementReady(false)) {
    float lux = sensor.readLightLevel();
    if (lux >= 0) {
      ultimaLux = lux;
      // Em failsafe nao ha decisao a responder, entao nao ha telemetria. O
      // RNF07 pede a MEDICAO do estado assumido pelo no: fica no serial.
      static unsigned long ultimoRelato = 0;
      if (emFailsafe && millis() - ultimoRelato >= 2000) {
        ultimoRelato = millis();
        Serial.printf("  failsafe: nivel 1,000 duty %d lux %.2f (%lu s sem comando)\n",
                      dutyAtual, lux, (millis() - ultimoComando) / 1000);
      }
      if (leiturasADescartar > 0) {
        leiturasADescartar--;  // ainda e luz de antes da troca
      } else if (decisaoPendente[0]) {
        publicarTelemetria(decisaoPendente, lux);
        Serial.printf("  telemetria: duty %.4f lux %.2f\n", dutyAtual / (float)DUTY_MAX, lux);
        decisaoPendente[0] = '\0';
      }
    }
  }
  delay(5);
}
