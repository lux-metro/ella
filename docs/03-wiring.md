# Conexiones físicas — Cableado y montaje

> Esta guía describe las conexiones físicas de la instalación. La buena noticia: **no hay cables entre los componentes** — el parlante se conecta por Bluetooth y el radar de presencia por WiFi. Solo hay que alimentar cada placa.

---

## ¿Qué se conecta con cables?

| Componente | Conexión | Tipo |
|------------|----------|------|
| Raspberry Pi | Fuente 5V (USB) | Cable de alimentación |
| Parlante Bluetooth | → Raspberry Pi | Sin cables (Bluetooth A2DP) |
| ESP32-C3 (radar) | → Raspberry Pi | Sin cables (WiFi, red del Access Point) |
| Radars RCWL-0516 | → ESP32-C3 | 2 cables de señal (pines 4 y 5) |

---

## Radar RCWL-0516 → ESP32-C3

Cada radar tiene una salida (OUT) que se conecta a un pin digital de la ESP32:

| Radar | Señal OUT | Pin ESP32 |
|-------|-----------|-----------|
| Radar 1 (una cara del tapiz) | `OUT` → | GPIO 4 |
| Radar 2 (otra cara del tapiz) | `OUT` → | GPIO 5 |
| Alimentación de ambos | `VCC`/`GND` → | 3.3V / GND |

> Los pines están definidos en `hardware/radar_esp32/config.h` (`PIN_RADAR_1` y `PIN_RADAR_2`). Si tu placa usa otros números, cambiálos ahí.

> **Ojo:** la serigrafía del ESP32-C3 Super Mini puede variar entre fabricantes — verificá que el "4" y el "5" impresos en la placa correspondan a los pines que vas a usar.

---

## Montaje

1. **Parlante Bluetooth:** dentro o junto a la alfombra, apuntando hacia afuera. Sin cables: solo necesita energía (su batería o cargador).
2. **Radar:** uno a cada lado del tapiz, apuntando a la zona por donde pasa el público. No lo pegues sobre metal (interfiere con la microonda).
3. **ESP32-C3:** junto al tapiz, alimentado por cualquier USB (cargador de 5V o una powerbank).
4. **Raspberry Pi:** oculta cerca del tapiz, con su fuente 5V/3A.

---

## Checklist antes de encender

- [ ] Parlante Bluetooth emparejado y conectado (ver [02-audio-setup.md](02-audio-setup.md))
- [ ] Radars conectados a los pines 4 y 5 de la ESP32
- [ ] ESP32 alimentada y con el firmware grabado (`hardware/radar_esp32/`)
- [ ] Raspberry Pi con la fuente conectada

---

*← [02-audio-setup.md](02-audio-setup.md) | Siguiente: [04-troubleshooting.md](04-troubleshooting.md) →*
