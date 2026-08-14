// =============================================================
// config.h — Parámetros configurables del radar de presencia
// =============================================================
//
// Editá este archivo si necesitás cambiar el nombre de la red,
// la IP de la Raspberry Pi o los pines de los radares. El código
// principal (radar_esp32.ino) no necesita tocarse.
//
// =============================================================

#ifndef CONFIG_H
#define CONFIG_H

// --- Red WiFi de la instalación ---
// La Raspberry Pi crea esta red cuando está en modo Access Point.
// Si usás una red distinta (por ejemplo tu WiFi local para pruebas),
// cambiá estos dos valores.

#define WIFI_SSID      "InstalacionElla"
#define WIFI_PASSWORD  ""

// --- Raspberry Pi (destino de los datos) ---
// IP fija de la Pi dentro de la red del Access Point y el puerto
// UDP donde escucha sentir-presencia.py.

#define PI_IP_OCTETOS  192,168,4,1
#define PUERTO_UDP     5005

// --- Pines de los radares ---
// Las salidas (OUT) de cada radar RCWL-0516 se conectan acá.
// Revisá la serigrafía de tu placa ESP32-C3 Super Mini: en la
// mayoría está marcada como "4" y "5".

#define PIN_RADAR_1  4  // radar de una cara del tapiz
#define PIN_RADAR_2  5  // radar de la otra cara del tapiz

// --- Temporización ---
// Cada cuántos milisegundos se manda el estado a la Pi y cada
// cuánto se reintenta la conexión WiFi si se cortó.

#define INTERVALO_ENVIO_MS      200
#define INTERVALO_RECONEXION_MS 30000

// --- Potencia de transmisión WiFi ---
// Bajamos la potencia a propósito: con la potencia máxima la señal
// del ESP32-C3 Super Mini se refleja contra el tapiz y se cancela,
// y la Raspberry Pi no puede decodificarla. Ver docs/04-troubleshooting.md

#define POTENCIA_TX  WIFI_POWER_8_5dBm

#endif // CONFIG_H
