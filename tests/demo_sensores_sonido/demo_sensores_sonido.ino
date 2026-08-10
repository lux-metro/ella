/*
  Demo interactiva: sensores modulando sonido (v2 - fix de crosstalk ADC)
  ------------------------------------------------------------------------
  El conversor analógico del Arduino (ADC) necesita un instante para
  "olvidarse" del voltaje del pin anterior antes de medir uno nuevo.
  Si el pin nuevo tiene mucha resistencia (como el piezo, con su
  resistencia de 1MΩ), ese olvido es incompleto y un poco de la
  lectura anterior se filtra en la nueva - eso causaba el "eco" de
  la luz en TempC y Vibracion.

  El arreglo: antes de cada lectura real, hacemos una lectura
  descartada del mismo pin. Esa primera lectura le da tiempo al ADC
  para acomodarse, y la segunda (la que realmente usamos) sale limpia.

  Sensores:
    - Luz (fotoresistencia) en A0
    - Piezo en A1 - sensor de golpe y parlante
    - Inclinación en el pin digital 2
    - Temperatura (TMP36) en A2
*/

const int pinLuz = A0;
const int pinPiezo = A1;
const int pinInclinacion = 2;
const int pinTemp = A2;

const int UMBRAL_GOLPE = 10; // ajustá según lo que veas en el Serial Plotter

void setup() {
  Serial.begin(9600);
  pinMode(pinInclinacion, INPUT_PULLUP);
  pinMode(pinPiezo, INPUT); // arranca en modo "sensor"
}

void loop() {
  int valorLuz = leerAnalogEstable(pinLuz);
  int valorInclinacion = digitalRead(pinInclinacion);
  float tempC = leerTemperatura();
  int valorPiezo = leerAnalogEstable(pinPiezo);

  Serial.print("Luz:"); Serial.print(valorLuz);
  Serial.print("\tInclinacion:"); Serial.print(valorInclinacion * 500);
  Serial.print("\tTempC:"); Serial.print(tempC);
  Serial.print("\tVibracion:"); Serial.println(valorPiezo);

  if (valorPiezo > UMBRAL_GOLPE) {
    reproducirSonido(tempC, valorLuz);
  }

  delay(50);
}

// Lee un pin analógico de forma "limpia": descarta la primera lectura
// para darle tiempo al ADC de acomodarse a este pin, y devuelve la
// segunda lectura, que ya no tiene rastros del pin anterior.
int leerAnalogEstable(int pin) {
  analogRead(pin); // lectura descartada
  delayMicroseconds(100);
  return analogRead(pin); // lectura real
}

float leerTemperatura() {
  int lectura = leerAnalogEstable(pinTemp);
  float voltaje = lectura * (5.0 / 1023.0);
  float tempC = (voltaje - 0.5) * 100.0; // fórmula estándar del TMP36
  return tempC;
}

void reproducirSonido(float tempC, int valorLuz) {
  int tempInt = (int)tempC;
  int frecuencia = map(tempInt, 15, 35, 200, 1000);
  frecuencia = constrain(frecuencia, 200, 2000);

  int duracion = map(valorLuz, 0, 1023, 100, 500);

  pinMode(pinPiezo, OUTPUT);
  tone(pinPiezo, frecuencia, duracion);
  delay(duracion + 20);

  pinMode(pinPiezo, INPUT); // vuelve a modo sensor
  delay(300); // pausa para que no se dispare solo con el eco de su sonido
}
