# ella

> *Ella 

Instalación textil de Sandra Pauli y Rosario Oliva

Ella propone al textil como un territorio donde memoria, cuerpo e historia se entrelazan. Una antigua alfombra persa es abierta y reparada mediante la sutura con vellón, transformando la herida en un gesto de repetición que alivia. El tejido activa relatos íntimos y memorias heredadas que encuentran eco en los diarios de la abuela de Sandra Pauli, escritos entre 1943 y 1982. La obra convierte el acto de entrelazar en una forma de hacer visible lo oculto y entiende la reparación y el tejido como una práctica de transmisión, resistencia y transformación.*  

> Este código da soporte a una instalación aumentada con sonido emitidos desde el interior de la alfombra. Las condiciones del entorno influyen sobre el comportamiento del audio.

---

## ¿Qué hace este repositorio?

Este repositorio contiene todo el software, firmware y documentación para montar la instalación *ella*: una Raspberry Pi que genera audio evolutivo, un Arduino que lee sensores ambientales (temperatura, luz), un radar de presencia que detecta a los visitantes, y un parlante Bluetooth por el que sale el sonido. La presencia de gente acelera el tempo de la pieza.

**Si estás arrancando desde cero**, empezá por: [docs/00-antes-de-empezar.md](docs/00-antes-de-empezar.md)

---

## Estructura del repositorio

```
ella/
├── docs/           → Guías paso a paso (empezá acá)
├── hardware/       → Firmware del Arduino (código de sensores)
├── pi/             → Software de las Raspberry Pi (motor de audio)
├── deploy/         → Scripts de instalación automatizada
├── prototype/      → Scripts de prototipo y experimentos (no son producción)
├── audio/          → Archivos de audio de la instalación
└── tests/          → Scripts para verificar que todo funciona
```

---

## Guías de setup (en orden)

| Paso | Guía | Descripción |
|------|------|-------------|
| 0 | [00-antes-de-empezar.md](docs/00-antes-de-empezar.md) | Qué es cada cosa, lista de hardware |
| 1 | [01-raspberry-pi-setup.md](docs/01-raspberry-pi-setup.md) | Grabar SD card y primer arranque |
| 2 | [02-arduino-setup.md](docs/02-arduino-setup.md) | Subir firmware al Arduino |
| 3 | [03-audio-setup.md](docs/03-audio-setup.md) | Configurar salida de audio |
| 4 | [04-wiring.md](docs/04-wiring.md) | Conexiones físicas de cables |
| 5 | [05-troubleshooting.md](docs/05-troubleshooting.md) | Qué hacer si algo no funciona |

---

## Setup rápido (si ya sabés lo que hacés)

```bash
# En la Raspberry Pi, después del primer arranque:
curl -sSL https://raw.githubusercontent.com/TU_USUARIO/ella/main/deploy/provision.sh | bash

# Eso es todo. La Pi queda autónoma y arranca sola.
```

> ⚠️ Reemplazá `TU_USUARIO` con tu usuario de GitHub antes de usar este comando.

---

## 🛜 Conectividad y Red (Importante)

Después de ejecutar `provision.sh`, la Pi **se queda conectada a tu WiFi de la casa**. El modo Access Point **no se activa automáticamente**: es una opción que se activa a pedido (ideal para aislar la máquina cuando la instalación está montada en la sala de exposición).

El Access Point se hace con **NetworkManager** (nmcli) y se activa de dos formas:

* **Desde el Panel Web:** sección **"Access Point"** → definís la contraseña y pulsás *Activar Access Point*. La Pi crea la red `InstalacionElla` y se desconecta de tu WiFi local.
* **Por CLI (consola SSH):** `bash ~/ella/repo/pi/setup_pi_access_point.sh`

Cuando el AP está activo:
1. Conectá tu celular o computadora a la red WiFi `InstalacionElla`.
2. Ingresá a `http://192.168.4.1:5000` en tu navegador para ver el **Panel de Control**.
3. La Pi queda aislada (sin Internet). Para la consola: `ssh tu_usuario@192.168.4.1`.

**¿Qué hago si necesito que la Pi vuelva a tener internet (ej: para hacer un update o un git pull)?**
Tienes dos opciones:
* **Fácil (Hardware):** Enchufarle un cable Ethernet directo al router. La Pi mantendrá el Access Point por WiFi pero obtendrá internet por el cable.
* **Software:** Desde el Panel Web, abajo de todo está la "Zona de Peligro". Allí puedes ordenar que se desactive el Access Point. La máquina se reiniciará y volverá a conectarse automáticamente a tu WiFi de la casa. También podés hacerlo por CLI: `bash ~/ella/repo/pi/revertir_wifi.sh`.

---

## Arquitectura del sistema

```
                    ┌─────────────────────────────────┐
                    │        ALFOMBRA (ella)         │
                    │       🎵 parlante Bluetooth     │
                    └─────────────────────────────────┘
                                   ▲
                                   │ A2DP (PulseAudio)
                    ┌───────────────────────────────────┐
                    │        Raspberry Pi 3 (una)       │
                    │   audio_engine.py + sox/play      │
                    └──────┬───────────────────┬────────┘
                           │ UART serie        │ UDP (red)
                    ┌──────▼───────┐    ┌──────▼──────────┐
                    │  Arduino Uno │    │  ESP32-C3       │
                    │  temp · luz  │    │  radar presencia│
                    └──────────────┘    └─────────────────┘
```

*La instalación usa una sola Raspberry Pi: una única voz que evoluciona según los sensores y la presencia de visitantes.*

---

## Estado del proyecto

- [x] Prototipo bash (sox/play + Bluetooth) — `prototype/bash/`
- [x] Motor de audio Python + configuración por dispositivo — `pi/shared/` (corre como servicio `reproducir.service`)
- [x] Comunicación Arduino → Raspberry Pi por UART — `serial_reader.py` + firmware `hardware/sensor_hub/`
- [x] Deploy automatizado — `deploy/provision.sh` (y Ansible como flujo alternativo)
- [x] Panel de control web + Access Point bajo demanda — `pi/panel/`
- [ ] Pruebas de larga duración (72 hs continuas)

---

## Hardware necesario

Listado completo con links en [docs/00-antes-de-empezar.md](docs/00-antes-de-empezar.md).

**Resumen:**
- 1× Raspberry Pi 3 Model B (ya tenés)
- 1× Arduino Uno (del Starter Kit)
- 1× Sensor de temperatura (ej: LM35 o NTC)
- 1× Fotoresistor (LDR) para luz ambiental
- 1× Módulo radar de presencia (ESP32-C3 + RCWL-0516)
- 1× Parlante Bluetooth
- Cables Dupont macho-macho y macho-hembra
- SD card (mínimo 8GB, clase 10)
- Fuente de alimentación 5V para la Pi

---

## Licencia

[MIT](LICENSE) — libre para usar, modificar y compartir.
