# ella

> *Una alfombra de lana, arcilla, hongos y sonido.*  
> Instalación sonora de arte. Sonido emitido desde adentro de la alfombra usando transductores de vibración (exciters). El crecimiento biológico influye sobre el comportamiento del audio.

---

## ¿Qué hace este repositorio?

Este repositorio contiene todo el software, firmware y documentación para montar la instalación *ella*: dos Raspberry Pi que generan audio evolutivo, un Arduino que lee sensores ambientales (humedad de la arcilla, temperatura, luz), y transductores de vibración que convierten la alfombra en el parlante.

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
curl -sSL https://raw.githubusercontent.com/TU_USUARIO/ella/main/deploy/provision.sh | VOICE=a bash

# Eso es todo. La Pi queda autónoma y arranca sola.
```

> ⚠️ Reemplazá `TU_USUARIO` con tu usuario de GitHub antes de usar este comando.

---

## Arquitectura del sistema

```
                    ┌─────────────────────────────────┐
                    │         ALFOMBRA (ella)          │
                    │  [exciter] ←── amplificador ←── │
                    └─────────────────────────────────┘
                                                       ▲
                                                       │ audio 3.5mm
                    ┌───────────────────────────────────┐
                    │       Raspberry Pi 3 (Voz A)       │
                    │   audio_engine.py + sox/play        │
                    └──────────────┬────────────────────┘
                                   │ UART serie (cable)
                    ┌──────────────▼────────────────────┐
                    │           Arduino Uno              │
                    │  sensor humedad · temp · luz       │
                    └───────────────────────────────────┘
```

*(En la instalación final habrá dos Raspberry Pi, cada una manejando una voz independiente)*

---

## Estado del proyecto

- [x] Prototipo bash (sox/play + Bluetooth) — `prototype/bash/`
- [ ] Motor de audio Python + configuración por dispositivo
- [ ] Comunicación Arduino → Raspberry Pi por UART
- [ ] Deploy automatizado con Ansible
- [ ] Pruebas de larga duración (72 hs continuas)

---

## Hardware necesario

Listado completo con links en [docs/00-antes-de-empezar.md](docs/00-antes-de-empezar.md).

**Resumen:**
- 1× Raspberry Pi 3 Model B (ya tenés 2)
- 1× Arduino Uno (del Starter Kit)
- 1× Sensor de humedad de suelo (ej: resistivo analógico)
- 1× Sensor de temperatura (ej: LM35 o NTC)
- 1× Fotoresistor (LDR) para luz ambiental
- 2× Transductor de vibración / exciter (ej: Dayton Audio DAEX25)
- 1× Amplificador de audio (ej: PAM8403, 3W stereo)
- Cables Dupont macho-macho y macho-hembra
- SD cards (mínimo 8GB, clase 10)
- Fuente de alimentación 5V para cada Pi

---

## Licencia

[MIT](LICENSE) — libre para usar, modificar y compartir.
