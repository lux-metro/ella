// ============================================
// TEST 2: Test de todos los pines (continuidad de la soldadura)
// ============================================
// Este programa NO necesita LEDs ni resistencias, solo un
// cable jumper.
//
// COMO SE USA:
//  1) Subi este programa y abri el Monitor Serie
//     (Herramientas > Monitor Serie, velocidad 115200)
//  2) Conecta un extremo de un cable jumper a un pin GND
//     de la placa (hay varios, cualquiera sirve)
//  3) Con el otro extremo del jumper, toca cada uno de los
//     pines de la lista de aca abajo, UNO POR VEZ, dejando
//     un segundo de contacto antes de pasar al siguiente
//  4) En el Monitor Serie va a aparecer un mensaje cada vez
//     que un pin cambia de estado. Si tocas el pin 4 y ves
//     "GPIO 4 paso a LOW", esa soldadura esta bien. Si no
//     aparece nada al tocar un pin, esa soldadura puede
//     tener un problema: proba tocar de nuevo asegurandote
//     buen contacto, y si sigue sin aparecer, revisa esa
//     pata con lupa (puede ser un puente frio o falta de
//     estaño)
//
// IMPORTANTE: usa siempre el pin GND para este test, nunca
// el pin de 5V, porque los pines GPIO del ESP32 solo
// soportan hasta 3.3 volts.
// ============================================

// Lista de los pines que vamos a probar. Fijate en las
// letras impresas en tu placa (serigrafia) y si algun
// numero no coincide con lo que ves ahi, ajusta esta lista.
const int pines[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 21};
const int cantidadPines = sizeof(pines) / sizeof(pines[0]);

// Aca guardamos el ultimo estado leido de cada pin, para
// darnos cuenta solo cuando CAMBIA
int estadoAnterior[cantidadPines];

void setup() {
  Serial.begin(115200);
  delay(2000); // le da tiempo a la compu a abrir el puerto

  for (int i = 0; i < cantidadPines; i++) {
    pinMode(pines[i], INPUT_PULLUP);
    estadoAnterior[i] = digitalRead(pines[i]);
  }

  Serial.println("Listo. Toca cada pin con el jumper conectado a GND.");
}

void loop() {
  for (int i = 0; i < cantidadPines; i++) {
    int estadoActual = digitalRead(pines[i]);

    if (estadoActual != estadoAnterior[i]) {
      Serial.print("GPIO ");
      Serial.print(pines[i]);
      Serial.print(" paso a ");
      Serial.println(estadoActual == LOW ? "LOW (tocado con GND)" : "HIGH (soltado)");
      estadoAnterior[i] = estadoActual;
    }
  }
  delay(20);
}

// Nota sobre pines 2, 8 y 9: son pines "de arranque"
// (strapping pins), usados internamente en el momento de
// encender o resetear la placa. Una vez que el programa ya
// esta corriendo (como en este test), tocarlos con el
// jumper no tiene ningun riesgo.
