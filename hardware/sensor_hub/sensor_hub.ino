// =============================================================
// sensor_hub.ino — Firmware del Arduino para la instalación *ella*
// =============================================================
//
// Este programa hace una sola cosa: leer sensores físicos
// y mandar los valores a la Raspberry Pi por comunicación serial.
//
// Sensores que lee:
//   - Temperatura ambiente (pin A1, sensor LM35)
//   - Luz ambiental (pin A2, fotoresistor LDR)
//
// Formato de salida (una línea por lectura, en formato JSON):
//   {"temperature":225,"light":300,"ok":true}
//
// Donde:
//   temperature → temperatura en décimas de °C (225 = 22.5°C)
//   light       → valor crudo 0-1023 (mayor = más luminoso)
//   ok          → siempre true si el Arduino está funcionando
//
// =============================================================

#include "config.h"

// --- Variables globales ---
// Guardamos el momento del último envío para no usar delay()
// delay() bloquea el Arduino; millis() permite hacer otras cosas mientras espera.
unsigned long ultimaLectura = 0;

// =============================================================
// setup() — Se ejecuta UNA VEZ cuando el Arduino arranca
// =============================================================
void setup() {
  // Iniciar comunicación serial con la velocidad definida en config.h
  Serial.begin(BAUDRATE);

  // Esperar a que el puerto serial esté listo
  // (Esto es necesario en algunos modelos de Arduino)
  while (!Serial) {
    ;  // esperar
  }

  // Mensaje de inicio (útil para saber cuándo arrancó el Arduino)
  Serial.println("{\"status\":\"iniciando\",\"version\":\"1.0\"}");
}

// =============================================================
// loop() — Se ejecuta REPETIDAMENTE para siempre
// =============================================================
void loop() {
  // Obtener el tiempo actual en milisegundos desde que arrancó el Arduino
  unsigned long ahora = millis();

  // Verificar si pasó suficiente tiempo desde la última lectura
  if (ahora - ultimaLectura >= INTERVALO_LECTURA_MS) {
    // Actualizar el registro de cuándo fue la última lectura
    ultimaLectura = ahora;

    // Leer los sensores
    int valorTemperatura = leerTemperatura();
    int valorLuz        = leerLuz();

    // Mandar los datos en formato JSON por el puerto serial
    enviarDatos(valorTemperatura, valorLuz);
  }

  // Acá podría haber otro código que corra entre lecturas,
  // sin bloquear el loop principal.
}

// =============================================================
// leerTemperatura() — Lee el sensor de temperatura LM35
// =============================================================
// Retorna temperatura en décimas de grado Celsius.
// Ejemplo: 225 significa 22.5°C
int leerTemperatura() {
  int valorADC = analogRead(PIN_TEMPERATURA);

  // Convertir el valor digital a temperatura
  // El LM35 da 10mV por grado. Con 5V de referencia y 10 bits:
  float milivolts = valorADC * LM35_MV_POR_PASO;
  float temperatura = milivolts / LM35_MV_POR_GRADO;

  // Convertir a décimas de grado (multiplicar por 10 para evitar decimales en JSON)
  return (int)(temperatura * 10);
}

// =============================================================
// leerLuz() — Lee el fotoresistor (LDR)
// =============================================================
// Retorna un valor entre 0 y 1023.
// Con un divisor de voltaje estándar: 0 = oscuridad, 1023 = luz máxima
int leerLuz() {
  return analogRead(PIN_LUZ);
}

// =============================================================
// enviarDatos() — Serializa los datos en JSON y los envía
// =============================================================
void enviarDatos(int temperatura, int luz) {
  // Construir el string JSON manualmente (sin librería externa)
  // Formato: {"temperature":225,"light":300,"ok":true}
  Serial.print("{");
  Serial.print("\"temperature\":");
  Serial.print(temperatura);
  Serial.print(",\"light\":");
  Serial.print(luz);
  Serial.print(",\"ok\":true");
  Serial.println("}");
  // println agrega un salto de línea al final, que sirve como delimitador
}
