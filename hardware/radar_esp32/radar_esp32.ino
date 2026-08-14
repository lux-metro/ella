/*
  radar_esp32.ino

  Este programa va DENTRO del ESP32-C3 Super Mini (se lo subís con el
  programa Arduino IDE). Lo que hace es:

    1) Conectarse a la red WiFi que crea la Raspberry Pi.
    2) Leer todo el tiempo los dos sensores de radar RCWL-0516.
    3) Mandarle a la Raspberry, por WiFi, un mensaje cada 200ms
       diciendo si hay movimiento ("1") o no ("0").

  Los parámetros configurables (red, IP, pines, tiempos) están en
  config.h.
*/

#include <WiFi.h>
#include <WiFiUdp.h>

#include "config.h"

// ============================ CONFIGURACIÓN ============================

IPAddress piIP(PI_IP_OCTETOS);

// ========================================================================

WiFiUDP udp;
unsigned long ultimoEnvio = 0;
unsigned long ultimoIntento = 0;

// Reset real del radio: apagarlo y encenderlo en modo STA. Esto corta
// cualquier intento de conexión atascado (el "cannot set config") que
// ignora a WiFi.disconnect() y deja el radio ocupado por minutos.
void reiniciarRadio() {
  WiFi.mode(WIFI_OFF);
  delay(300);
  WiFi.mode(WIFI_STA);
  delay(300);
}

const char* descifrarTipo(wifi_auth_mode_t tipo) {
  switch (tipo) {
    case WIFI_AUTH_OPEN: return "abierta";
    case WIFI_AUTH_WEP: return "WEP";
    case WIFI_AUTH_WPA_PSK: return "WPA";
    case WIFI_AUTH_WPA2_PSK: return "WPA2";
    case WIFI_AUTH_WPA_WPA2_PSK: return "WPA/WPA2";
    case WIFI_AUTH_WPA2_ENTERPRISE: return "WPA2-Ent";
    case WIFI_AUTH_WPA3_PSK: return "WPA3";
    case WIFI_AUTH_WPA2_WPA3_PSK: return "WPA2/WPA3";
    case WIFI_AUTH_WAPI_PSK: return "WAPI";
    default: return "?";
  }
}

void conectarWiFi() {
  reiniciarRadio();

  Serial.print("Conectando a: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setTxPower(POTENCIA_TX);   // BAJAR potencia: si no, la señal se refleja y se cancela, y el AP no la decodifica

  unsigned long inicio = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - inicio < 20000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("Fallo. WiFi.status() = ");
    Serial.println(WiFi.status());

    // Scan con el radio recién reiniciado para que el resultado sea
    // confiable (si el radio está ocupado "conectando", el scan devuelve -2).
    reiniciarRadio();
    int n = WiFi.scanNetworks();
    if (n <= 0) {
      Serial.print("Scan falló (código ");
      Serial.print(n);
      Serial.println("). ¿Está el access point en 2.4 GHz?");
      return;
    }
    Serial.print("Scan: ");
    Serial.print(n);
    Serial.println(" red(es) visible(s):");
    for (int i = 0; i < n; i++) {
      Serial.print("  ");
      Serial.print(WiFi.SSID(i));
      Serial.print(" ch=");
      Serial.print(WiFi.channel(i));
      Serial.print(" ");
      Serial.print(descifrarTipo(WiFi.encryptionType(i)));
      Serial.print(" (");
      Serial.print(WiFi.RSSI(i));
      Serial.println(" dBm)");
    }
  } else {
    Serial.println("Conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);

  // Usamos INPUT_PULLDOWN en vez de INPUT: así, si un pin queda sin
  // conectar (por ejemplo porque todavía no pusiste el segundo radar),
  // el ESP32 lo lee de forma estable en LOW en vez de leer ruido al
  // azar. Cuando el radar SÍ está conectado, esto no afecta la lectura.
  pinMode(PIN_RADAR_1, INPUT_PULLDOWN);
  pinMode(PIN_RADAR_2, INPUT_PULLDOWN);

  WiFi.setSleep(false);   // evita interferencia del modem-sleep (otro fix reportado)
  conectarWiFi();
}

void enviarEstado(bool hayMovimiento) {
  String mensaje = hayMovimiento ? "1" : "0";

  udp.beginPacket(piIP, PUERTO_UDP);
  udp.print(mensaje);
  udp.endPacket();

  Serial.println("Mandado: " + mensaje);
}

void loop() {
  // Si se corta el WiFi, intentamos reconectar solos, pero esperando
  // 30s entre intentos para que el radio termine el intento anterior.
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - ultimoIntento >= INTERVALO_RECONEXION_MS) {
      ultimoIntento = millis();
      conectarWiFi();
    }
    delay(20);
    return;
  }

  int lecturaRadar1 = digitalRead(PIN_RADAR_1);
  int lecturaRadar2 = digitalRead(PIN_RADAR_2);

  // Con que UNO de los dos radares detecte algo, ya consideramos
  // que hay movimiento (porque el tapiz puede colgar de cualquier lado).
  bool hayMovimiento = (lecturaRadar1 == HIGH) || (lecturaRadar2 == HIGH);

  unsigned long ahora = millis();
  if (ahora - ultimoEnvio >= INTERVALO_ENVIO_MS) {
    ultimoEnvio = ahora;
    enviarEstado(hayMovimiento);
  }

  delay(20);
}
