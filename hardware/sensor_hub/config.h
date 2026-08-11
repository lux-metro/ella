// =============================================================
// config.h — Parámetros configurables del Arduino
// =============================================================
//
// Editá este archivo si necesitás cambiar los pines o el
// intervalo de lectura de los sensores. El código principal
// (sensor_hub.ino) no necesita tocarse.
//
// =============================================================

#ifndef CONFIG_H
#define CONFIG_H

// --- Pines analógicos de los sensores ---
// Los pines analógicos del Arduino Uno van de A0 a A5.
// Cada sensor se conecta a un pin diferente.

#define PIN_TEMPERATURA  A1   // Sensor de temperatura LM35
#define PIN_LUZ          A2   // Fotoresistor (LDR) para luz ambiental

// --- Intervalo de lectura ---
// Cada cuántos milisegundos se leen los sensores y se mandan
// los datos a la Raspberry Pi. 500ms = dos veces por segundo.
// Valor mínimo recomendado: 200ms. Máximo útil: 2000ms.

#define INTERVALO_LECTURA_MS  500

// --- Velocidad de comunicación serial ---
// Tiene que coincidir con lo que lee la Raspberry Pi.
// No cambies esto a menos que también cambies serial_reader.py.

#define BAUDRATE  9600

// --- Calibración del sensor LM35 ---
// El LM35 da 10mV por grado Celsius.
// Con referencia de 5V y resolución de 10 bits (1024 pasos):
// Temperatura (°C) = valor_analogico * (5000 / 1024) / 10
// Esta constante hace esa cuenta.

#define LM35_MV_POR_PASO  (5000.0 / 1024.0)  // milivoltios por paso ADC
#define LM35_MV_POR_GRADO 10.0                // milivoltios por grado Celsius

#endif // CONFIG_H
