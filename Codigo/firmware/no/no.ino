// Firmware do no de iluminacao (TCC 3.4, 4.6.1, Quadro 14).
//
// O no NAO decide. Ele:
//   1. assina iluminacao/{ponto}/comando e recebe {decisao_id, nivel};
//   2. converte o nivel (fracao do fluxo pleno) em ciclo de trabalho pela
//      tabela de calibracao MEDIDA na bancada (calibracao.h, 3.3);
//   3. aplica o PWM (5 kHz, 12 bits) e mede a iluminancia (BH1750);
//   4. publica em iluminacao/{ponto}/telemetria {decisao_id, duty, lux,
//      medido_em} - o decisao_id liga a leitura a decisao (4.6.2);
//   5. FAILSAFE (RNF07): sem comando por 15 s, vai sozinho ao nivel pleno.
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
#include "mqtt_client.h"

#include "calibracao.h"
#include "segredos.h"

// ---- Parametros ------------------------------------------------------------
const int PINO_PWM = 25;
const int FREQ_PWM = 5000;
const int BITS_PWM = 12;
const int DUTY_MAX = 4095;

// RNF07: 3 x o periodo do ciclo de decisao (5 s). Ver DIVERGENCIAS item 2.
const unsigned long TIMEOUT_FAILSAFE_MS = 15000;

// O BH1750 mede continuamente: as leituras logo apos trocar o duty ainda sao
// de conversoes iniciadas ANTES da troca. Mesma regra da calibracao
// (bancada/calibrar.py, DIVERGENCIAS item 44).
const int LEITURAS_DESCARTADAS = 2;

const char *TOPICO_COMANDO    = "iluminacao/" PONTO "/comando";
const char *TOPICO_TELEMETRIA = "iluminacao/" PONTO "/telemetria";
const char *TOPICO_ESTADO     = "iluminacao/" PONTO "/estado";

// ---- Estado ----------------------------------------------------------------
struct Comando {
  char decisao_id[40];
  float nivel;
};

BH1750 sensor(0x23);
esp_mqtt_client_handle_t cliente = nullptr;
QueueHandle_t filaComandos;  // o evento MQTT roda em outra tarefa: fila entre elas

float nivelAtual = 1.0f;
int dutyAtual = 0;
unsigned long ultimoComando = 0;
bool emFailsafe = true;           // ate o primeiro comando, o no esta no pleno
char decisaoPendente[40] = "";    // telemetria ainda devida
int leiturasADescartar = 0;
float ultimaLux = -1;

// ---- Nivel -> duty -----------------------------------------------------------
// Interpolacao linear entre pontos MEDIDOS da tabela. Os niveis 1,0 e do
// piso caem exatamente nos duties medidos (3.4.2); so os intermediarios sao
// interpolados, entre vizinhos medidos a poucos % de distancia (item 29).
int dutyDoNivel(float nivel) {
  if (nivel <= CALIBRACAO[0].nivel) return CALIBRACAO[0].duty;
  for (int i = 1; i < N_CALIBRACAO; i++) {
    if (nivel <= CALIBRACAO[i].nivel) {
      const PontoCalibracao &a = CALIBRACAO[i - 1], &b = CALIBRACAO[i];
      float f = (nivel - a.nivel) / (b.nivel - a.nivel);
      return (int)lroundf(a.duty + f * (b.duty - a.duty));
    }
  }
  // Acima de 1,0 nao existe: o maximo e o duty MEDIDO do pleno, nunca 4095.
  return CALIBRACAO[N_CALIBRACAO - 1].duty;
}

void aplicarNivel(float nivel) {
  nivel = constrain(nivel, 0.0f, 1.0f);
  nivelAtual = nivel;
  dutyAtual = dutyDoNivel(nivel);
  ledcWrite(PINO_PWM, dutyAtual);
  leiturasADescartar = LEITURAS_DESCARTADAS;
}

// ---- Carga dos topicos -------------------------------------------------------
// JSON pequeno e de formato fixo: extraido a mao, sem biblioteca extra.
bool extrairComando(const char *dados, int tam, Comando &c) {
  char buf[160];
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

  const char *n = strstr(buf, "\"nivel\"");
  if (!n) return false;
  n = strchr(n + 7, ':');
  if (!n) return false;
  char *depois;
  c.nivel = strtof(n + 1, &depois);
  return depois != n + 1;
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
  char quando[32], carga[200];
  carimboAgora(quando, sizeof(quando));
  int n = snprintf(carga, sizeof(carga),
                   "{\"decisao_id\":\"%s\",\"duty\":%.4f,\"lux\":%.2f%s%s%s}",
                   decisao_id, dutyAtual / (float)DUTY_MAX, lux,
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

// ---- Diagnostico de Wi-Fi ----------------------------------------------------
// Chamado quando a conexao falha: lista as redes que o ESP32 enxerga. Ele so
// opera em 2,4 GHz; se a rede configurada nao aparece, ou e de 5 GHz ou o
// sinal nao chega. Se aparece, o problema e nome ou senha.
void diagnosticarWifi() {
  Serial.printf("status do Wi-Fi: %d (1 = rede nao encontrada, 4 = conexao recusada, "
                "6 = desconectado)\n", WiFi.status());
  Serial.println("redes que o ESP32 enxerga (so 2,4 GHz):");
  // O scan falha em silencio se o radio ainda estiver tentando conectar
  // ("sta is connecting"): interrompe a tentativa antes de procurar.
  WiFi.disconnect();
  delay(200);
  int n = WiFi.scanNetworks();
  if (n < 0) Serial.printf("  o scan falhou (codigo %d)\n", n);
  bool achou = false;
  for (int i = 0; i < n; i++) {
    bool eh = WiFi.SSID(i) == WIFI_SSID;
    achou |= eh;
    Serial.printf("  %s \"%s\"  sinal %d dBm  canal %d%s\n", eh ? ">>" : "  ",
                  WiFi.SSID(i).c_str(), WiFi.RSSI(i), WiFi.channel(i),
                  WiFi.encryptionType(i) == WIFI_AUTH_WPA2_ENTERPRISE ? "  (corporativa)" : "");
  }
  if (n == 0) Serial.println("  nenhuma rede encontrada (confira se o hotspot/roteador esta em 2,4 GHz)");
  if (achou) {
    Serial.println("-> a rede configurada APARECE: confira a SENHA (maiusculas, espacos).");
  } else {
    Serial.printf("-> a rede \"%s\" NAO aparece: ela e de 5 GHz, o nome esta diferente "
                  "(maiusculas contam) ou o sinal nao chega.\n", WIFI_SSID);
  }
  WiFi.scanDelete();
  WiFi.begin(WIFI_SSID, WIFI_SENHA);  // o scan interrompe a tentativa; recomeca
}

// ---- Setup / loop ------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.printf("\nno %s | calibracao da sessao %d\n", PONTO, CALIBRACAO_SESSAO);

  // Luz primeiro: ao energizar, o no fica no PLENO ate receber comando
  // (LACUNA 3). Nunca comeca apagado.
  ledcAttach(PINO_PWM, FREQ_PWM, BITS_PWM);
  aplicarNivel(1.0f);

  Wire.begin(21, 22);
  if (!sensor.begin(BH1750::CONTINUOUS_HIGH_RES_MODE_2)) {
    Serial.println("ERRO: BH1750 nao encontrado (a luz segue funcionando)");
  }
  sensor.setMTreg(BH1750_MTREG_MAX);  // o mesmo modo da calibracao

  filaComandos = xQueueCreate(8, sizeof(Comando));

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  Serial.print("conectando ao Wi-Fi");
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) {
    delay(250);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" ok, IP " + WiFi.localIP().toString());
  } else {
    Serial.println(" falhou (segue tentando; a luz fica no pleno)");
    diagnosticarWifi();
  }

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

void loop() {
  // 1. Comandos recebidos.
  Comando c;
  while (xQueueReceive(filaComandos, &c, 0) == pdTRUE) {
    if (decisaoPendente[0]) {
      // Chegou comando novo antes da leitura do anterior: aquela decisao
      // fica sem telemetria (a relacao e 1:1, mas nao obrigatoria).
      Serial.printf("decisao %s sem telemetria (substituida)\n", decisaoPendente);
    }
    aplicarNivel(c.nivel);
    strncpy(decisaoPendente, c.decisao_id, sizeof(decisaoPendente) - 1);
    ultimoComando = millis();
    if (emFailsafe) Serial.println("comando recebido: saindo do failsafe");
    emFailsafe = false;
    Serial.printf("nivel %.3f -> duty %d (%s)\n", c.nivel, dutyAtual, c.decisao_id);
  }

  // 2. Failsafe (RNF07): sem comando, pleno.
  if (!emFailsafe && millis() - ultimoComando > TIMEOUT_FAILSAFE_MS) {
    aplicarNivel(1.0f);
    emFailsafe = true;
    decisaoPendente[0] = '\0';
    Serial.println("FAILSAFE: sem comando ha 15 s -> nivel 1,0");
  }

  // 3. Leitura do sensor e telemetria da decisao pendente.
  if (sensor.measurementReady(false)) {
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
