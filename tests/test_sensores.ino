/*
  Test interactivo de sensores - Arduino Starter Kit
  ----------------------------------------------------
  Lee al mismo tiempo:
    - Sensor de luz (fotoresistencia) en A0
    - Piezo / sensor de vibración en A1
    - Sensor de inclinación en el pin digital 2

  Cómo verlo de forma interactiva:
    1. Subí este sketch al Arduino.
    2. Abrí Tools > Serial Plotter (NO Serial Monitor).
    3. Vas a ver tres líneas de colores. Movete: inclina el sensor
       de inclinación, tapá/destapá el sensor de luz con la mano,
       y dale un golpecito suave al piezo. Cada acción mueve una
       línea distinta en el gráfico, en tiempo real.
*/

const int pinLuz = A0;
const int pinPiezo = A1;
const int pinInclinacion = 2;

void setup() {
  Serial.begin(9600);

  // El sensor de inclinación es básicamente un interruptor que abre
  // o cierra según la posición. Usamos la resistencia interna del
  // Arduino (pull-up) para no tener que agregar una resistencia
  // externa solo para este sensor.
  pinMode(pinInclinacion, INPUT_PULLUP);
}

void loop() {
  int valorLuz = analogRead(pinLuz);            // rango: 0 (oscuro) a 1023 (muy iluminado)
  int valorPiezo = analogRead(pinPiezo);         // sube de golpe con un toque o vibración
  int valorInclinacion = digitalRead(pinInclinacion); // 0 o 1 según la posición

  // Formato "etiqueta:valor" separado por tabs: el Serial Plotter del
  // Arduino IDE lo reconoce automáticamente y dibuja una línea de
  // color distinta por cada etiqueta.
  Serial.print("Luz:");
  Serial.print(valorLuz);

  Serial.print("\tVibracion:");
  Serial.print(valorPiezo);

  // Multiplico por 500 solo para que la línea de inclinación (que es
  // 0 o 1) se vea en una escala parecida a las otras dos en el
  // gráfico. Para lógica real más adelante, usá el valor sin multiplicar.
  Serial.print("\tInclinacion:");
  Serial.println(valorInclinacion * 500);

  delay(50);
}
