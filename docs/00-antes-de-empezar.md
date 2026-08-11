# Antes de empezar — Guía de orientación

> Si nunca antes usaste una Raspberry Pi, un Arduino, ni una terminal de Linux, esta guía es para vos. Explicamos qué es cada cosa antes de empezar a conectar cables.

---

## Índice

1. [¿Qué es cada componente?](#1-qué-es-cada-componente)
2. [Glosario de términos](#2-glosario-de-términos)
3. [Lista de hardware completa](#3-lista-de-hardware-completa)
4. [Lista de herramientas y materiales](#4-lista-de-herramientas-y-materiales)
5. [¿Por dónde empezar?](#5-por-dónde-empezar)

---

## 1. ¿Qué es cada componente?

### Raspberry Pi 3 Model B
Una computadora pequeña del tamaño de una tarjeta de crédito. Corre Linux (un sistema operativo), puede conectarse a internet, y puede mandar el sonido a un parlante Bluetooth. En esta instalación, es la que corre el software de audio y controla el sonido.

*Necesitás una SD card para que funcione — es su "disco duro".*

### Arduino Uno
Un microcontrolador: una pequeña placa electrónica diseñada para leer sensores y controlar cosas físicas. No corre un sistema operativo completo — corre un único programa que vos le cargás. En esta instalación, lee los sensores de temperatura y luz, y manda esos datos a la Raspberry Pi.

### Parlante Bluetooth
El sonido de la instalación sale por un parlante Bluetooth inalámbrico. La Raspberry Pi lo empareja una sola vez (desde el Panel Web o por consola) y después el sistema lo reconecta automáticamente cuando se enciende.

### Radar de presencia (ESP32-C3 + RCWL-0516)
Un módulo con un radar de microondas que detecta movimiento (a diferencia de los sensores del Arduino, no mide el ambiente sino la gente). Cuando alguien se acerca, la Raspberry Pi lo nota y acelera el tempo de la pieza: la instalación reacciona a los visitantes.

---

## 2. Glosario de términos

| Término | Qué significa en este proyecto |
|---------|-------------------------------|
| **Terminal / consola** | Pantalla de texto negro donde escribís comandos. No es peligroso: si escribís algo mal, el peor caso es que no pase nada. |
| **SSH** | Forma de conectarte a la Raspberry Pi desde tu computadora usando texto, sin necesitar monitor ni teclado conectados a la Pi. |
| **UART / serie** | Protocolo de comunicación: la forma en que el Arduino y la Raspberry Pi se hablan usando cables (no wifi). |
| **Access Point** | Modo en el que la Raspberry Pi crea su propia red WiFi (en este proyecto se llama `InstalacionElla`). Se usa para aislar la máquina en la sala de exposición y entrar al panel desde `192.168.4.1:5000`. Se activa a pedido (panel web o CLI), no automáticamente. |
| **NetworkManager** | El programa de Linux que gestiona las redes (WiFi, ethernet). En este proyecto se usa su herramienta `nmcli` para activar/desactivar el Access Point. |
| **systemd** | El programa de Linux que arranca otros programas cuando enciende el sistema. Úsalo para que el audio arranque solo. |
| **Ansible** | Herramienta que corre en tu computadora y configura la Raspberry Pi automáticamente por SSH. |
| **firmware** | El programa que corre en el Arduino. A diferencia de un archivo común, se "graba" directamente en el chip. |
| **pin** | Los conectores metálicos en los bordes del Arduino y la Raspberry Pi. Cada uno tiene un nombre o número. |
| **ALSA** | El sistema de audio de Linux. Lo usamos para enrutar el audio al parlante Bluetooth. |
| **sox / play** | Herramientas de audio de línea de comandos. `sox` procesa audio, `play` lo reproduce. Ya las usaste en el prototipo. |
| **Git** | Sistema de control de versiones. Guarda el historial de cambios del código. GitHub es el sitio web donde guardás el repositorio. |

---

## 3. Lista de hardware completa

### Ya tenés
- ✅ 1× Raspberry Pi 3 Model B
- ✅ Arduino Uno (del Starter Kit)
- ✅ Cable USB tipo A a tipo B (para conectar Arduino a computadora)
- ✅ Cables Dupont (vienen en el Starter Kit)
- ✅ Resistencias surtidas (vienen en el Starter Kit)

### Necesitás conseguir

| Componente | Para qué sirve | Dónde buscarlo |
|------------|---------------|----------------|
| SD card ×1 | "Disco duro" de la Pi. Mínimo 8GB, clase 10 o A1 | Ferretería, libre mercado |
| Sensor temperatura LM35 | Leer temperatura ambiente | MercadoLibre: "LM35 arduino" |
| Fotoresistor / LDR | Leer luz ambiental | MercadoLibre: "LDR 5mm arduino" |
| ESP32-C3 + radar RCWL-0516 | Detectar presencia de visitantes | MercadoLibre: "ESP32-C3" / "RCWL-0516" |
| Parlante Bluetooth | Salida de audio de la instalación | Cualquier tienda de audio o celulares |
| Fuente 5V 3A ×1 | Alimentar la Raspberry Pi | MercadoLibre: "fuente 5v 3a raspberry pi" |

> **Nota sobre el parlante Bluetooth:** Cualquier parlante inalámbrico sirve. Es importante que tenga modo Bluetooth (A2DP) y que se apague/recupere bien cuando pierde señal. Se empareja una sola vez desde el Panel Web.

### Opcional (mejora la confiabilidad)
- UPS / batería de respaldo para las Pi (evita apagados bruscos por cortes de luz)

---

## 4. Lista de herramientas y materiales

- Computadora con Linux (para correr Ansible y conectarte por SSH)
- Cable de red ethernet (recomendado para el primer setup de la Pi)
- Multímetro (para verificar conexiones, opcional pero útil)
- Cinta aisladora o termocontraíble

---

## 5. ¿Por dónde empezar?

Si es la primera vez que abrís este repositorio, el camino es:

```
Esta guía (00)
    ↓
Preparar la Raspberry Pi → docs/01-raspberry-pi-setup.md
    ↓
Subir firmware al Arduino → docs/02-arduino-setup.md
    ↓
Configurar audio → docs/03-audio-setup.md
    ↓
Conectar los cables → docs/04-wiring.md
    ↓
¿Algo no funciona? → docs/05-troubleshooting.md
```

No necesitás tener todo el hardware antes de empezar. Podés arrancar solo con la Raspberry Pi y probar el audio, y agregar el Arduino y los sensores después.

---

*← [README principal](../README.md) | Siguiente: [01-raspberry-pi-setup.md](01-raspberry-pi-setup.md) →*
