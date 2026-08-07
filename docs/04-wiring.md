# Conexiones físicas — Diagrama de cableado

> Esta guía describe cómo conectar todos los componentes físicamente. Incluye la conexión UART entre Arduino y Raspberry Pi (la "línea de comunicación" entre ellos), y la cadena de audio hasta los exciters.

---

## Conexión Arduino → Raspberry Pi por UART

UART es una forma de comunicación en serie: los dos dispositivos se hablan usando dos cables (uno para enviar, uno para recibir) más un cable de tierra común.

> ⚠️ **Importante sobre voltajes:** El Arduino Uno trabaja a 5V y la Raspberry Pi trabaja a 3.3V. Conectar un pin de 5V directamente a la Pi puede dañarla. Necesitás un divisor de voltaje o un módulo convertidor de nivel lógico (level shifter).

### Opción recomendada: divisor de voltaje simple

Un divisor de voltaje con dos resistencias baja la señal de 5V del Arduino a ~3.3V para la Pi. Solo se necesita en el cable TX del Arduino (el que envía datos).

```
Arduino TX (pin 1)  ──── R1 (1kΩ) ──┬──── Raspberry Pi RX (GPIO 15, pin 10)
                                      │
                                     R2 (2kΩ)
                                      │
Arduino GND ──────────────────────────┴──── Raspberry Pi GND (pin 6)
```

La fórmula del divisor: `Vout = Vin × R2 / (R1 + R2) = 5V × 2000 / 3000 ≈ 3.33V` ✅

### Tabla de conexiones

| Arduino | Cable | Raspberry Pi |
|---------|-------|-------------|
| Pin TX (1) | → R1(1kΩ) → R2(2kΩ) → | GPIO 15 / RXD / Pin físico 10 |
| Pin RX (0) | ← directo ← | GPIO 14 / TXD / Pin físico 8 |
| GND | — tierra común — | GND / Pin físico 6 |

> **Nota:** En el prototipo inicial, el Arduino se conecta por USB (no UART directo). La conexión UART directa es para la instalación final, cuando el Arduino no va a estar conectado a ninguna computadora.

---

## Diagrama de pines de la Raspberry Pi 3

```
                    ┌─────────────────────────────────┐
                    │  RASPBERRY PI 3 — PINES GPIO    │
                    │                                  │
 3.3V  [pin  1] ●  ○ [pin  2] 5V                      │
  SDA  [pin  3] ○  ○ [pin  4] 5V                      │
  SCL  [pin  5] ○  ○ [pin  6] GND  ◄── tierra común  │
       [pin  7] ○  ○ [pin  8] TXD  ◄── Arduino RX    │
   GND [pin  9] ○  ○ [pin 10] RXD  ◄── Arduino TX    │
       ...                                             │
                    └─────────────────────────────────┘
```

---

## Conexión cadena de audio

```
Raspberry Pi 3
│  Pin 3.5mm (conector verde/negro en la placa)
│
├── Cable de audio 3.5mm (macho-macho)
│
▼
Amplificador PAM8403
│  Entrada: 3.5mm o terminales L/R
│  Salida: terminales A+ A- B+ B-
│
├── Cable fino (estaño soldado)
│
▼
Exciter / transductor de vibración
│  (dos cables: + y -)
│
▼
🎵 Alfombra vibra
```

### Conexión del exciter al amplificador PAM8403

El PAM8403 tiene terminales de tornillo (o pads de soldadura). El exciter tiene dos cables.

| Amplificador | Cable | Exciter |
|-------------|-------|---------|
| Canal A+ (o L+) | → | Cable rojo (o el marcado +) |
| Canal A- (o L-) | → | Cable negro (o el marcado -) |

> Si tenés dos exciters, uno va al canal A (Left) y el otro al canal B (Right).

---

## Conexión sensores → Arduino

### Sensor de humedad de suelo

```
Módulo sensor (lado del módulo, no la sonda):
  VCC ──── Arduino 5V
  GND ──── Arduino GND
  AO  ──── Arduino A0   (salida analógica)
  DO  ──── (no conectar, no lo usamos)
```

### Sensor de temperatura LM35

```
LM35 (visto de frente, con el texto legible):
  Pin izquierdo  (+Vs) ──── Arduino 5V
  Pin central   (Vout) ──── Arduino A1
  Pin derecho    (GND) ──── Arduino GND
```

### Fotoresistor / LDR

```
                         Arduino 5V
                              │
                          LDR (cualquier orientación)
                              │
                    ┌─────────┤──── Arduino A2
                    │
                  10kΩ (resistencia de pull-down)
                    │
                 Arduino GND
```

---

## Checklist antes de encender

- [ ] Divisor de voltaje armado (R1 y R2 entre Arduino TX y Pi RX)
- [ ] Cable tierra común entre Arduino GND y Pi GND
- [ ] Cable de audio 3.5mm conectado Pi → amplificador
- [ ] Exciter(es) conectado(s) al amplificador
- [ ] Sensores conectados a los pines A0, A1, A2 del Arduino
- [ ] Amplificador alimentado (puede ser con la misma fuente de la Pi o una separada)

---

*← [03-audio-setup.md](03-audio-setup.md) | Siguiente: [05-troubleshooting.md](05-troubleshooting.md) →*
