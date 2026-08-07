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
Una computadora pequeña del tamaño de una tarjeta de crédito. Corre Linux (un sistema operativo), puede conectarse a internet, y tiene una salida de audio de 3.5mm igual a la de un celular. En esta instalación, es la que corre el software de audio y controla el sonido.

*Necesitás una SD card para que funcione — es su "disco duro".*

### Arduino Uno
Un microcontrolador: una pequeña placa electrónica diseñada para leer sensores y controlar cosas físicas. No corre un sistema operativo completo — corre un único programa que vos le cargás. En esta instalación, lee los sensores de humedad, temperatura y luz, y manda esos datos a la Raspberry Pi.

### Transductor de vibración / Exciter
Un dispositivo que convierte señales de audio en vibraciones mecánicas. Cuando lo pegás a una superficie (como la alfombra), esa superficie se convierte en el parlante. Es el corazón conceptual de la instalación: el sonido sale desde adentro de la alfombra misma.

### Amplificador de audio
El audio que sale de la Raspberry Pi es muy débil. El amplificador lo hace más fuerte antes de mandarlo al exciter. Sin amplificador, el exciter no va a vibrar lo suficiente.

### Sensor de humedad de suelo
Una sondita que medís la conductividad eléctrica de la arcilla. La arcilla húmeda conduce más electricidad que la seca. Con este sensor podemos saber qué tan húmeda está la arcilla en tiempo real, y que eso influya en el sonido.

---

## 2. Glosario de términos

| Término | Qué significa en este proyecto |
|---------|-------------------------------|
| **Terminal / consola** | Pantalla de texto negro donde escribís comandos. No es peligroso: si escribís algo mal, el peor caso es que no pase nada. |
| **SSH** | Forma de conectarte a la Raspberry Pi desde tu computadora usando texto, sin necesitar monitor ni teclado conectados a la Pi. |
| **UART / serie** | Protocolo de comunicación: la forma en que el Arduino y la Raspberry Pi se hablan usando cables (no wifi). |
| **systemd** | El programa de Linux que arranca otros programas cuando enciende el sistema. Úsalo para que el audio arranque solo. |
| **Ansible** | Herramienta que corre en tu computadora y configura la Raspberry Pi automáticamente por SSH. |
| **firmware** | El programa que corre en el Arduino. A diferencia de un archivo común, se "graba" directamente en el chip. |
| **pin** | Los conectores metálicos en los bordes del Arduino y la Raspberry Pi. Cada uno tiene un nombre o número. |
| **ALSA** | El sistema de audio de Linux. Lo vamos a usar para configurar la salida de 3.5mm. |
| **sox / play** | Herramientas de audio de línea de comandos. `sox` procesa audio, `play` lo reproduce. Ya las usaste en el prototipo. |
| **Git** | Sistema de control de versiones. Guarda el historial de cambios del código. GitHub es el sitio web donde guardás el repositorio. |

---

## 3. Lista de hardware completa

### Ya tenés
- ✅ 2× Raspberry Pi 3 Model B
- ✅ Arduino Uno (del Starter Kit)
- ✅ Cable USB tipo A a tipo B (para conectar Arduino a computadora)
- ✅ Cables Dupont (vienen en el Starter Kit)
- ✅ Resistencias surtidas (vienen en el Starter Kit)

### Necesitás conseguir

| Componente | Para qué sirve | Dónde buscarlo |
|------------|---------------|----------------|
| SD card ×2 | "Disco duro" de cada Pi. Mínimo 8GB, clase 10 o A1 | Ferretería, libre mercado |
| Sensor humedad suelo | Leer humedad de la arcilla | MercadoLibre: "sensor humedad suelo arduino" |
| Sensor temperatura LM35 | Leer temperatura ambiente | MercadoLibre: "LM35 arduino" |
| Fotoresistor / LDR | Leer luz ambiental | MercadoLibre: "LDR 5mm arduino" |
| Exciter / transductor ×2 | Convertir alfombra en parlante | MercadoLibre: "transductor exciter" / "shaker exciter audio" |
| Amplificador PAM8403 | Amplificar audio antes del exciter | MercadoLibre: "PAM8403 amplificador" |
| Fuente 5V 3A ×2 | Alimentar cada Raspberry Pi | MercadoLibre: "fuente 5v 3a raspberry pi" |
| Cable de audio 3.5mm | Pi → amplificador | Cualquier ferretería o electronica |

> **Nota sobre los exciters:** El Dayton Audio DAEX25 es el más recomendado para instalaciones de arte, pero puede ser difícil de conseguir localmente. Alternativas: cualquier transductor de vibración de 4-8 ohm, 10-25W. En duda, escribime.

### Opcional (mejora la confiabilidad)
- UPS / batería de respaldo para las Pi (evita apagados bruscos por cortes de luz)

---

## 4. Lista de herramientas y materiales

- Computadora con Linux (para correr Ansible y conectarte por SSH)
- Cable de red ethernet (recomendado para el primer setup de la Pi)
- Soldador y estaño (para conectar el exciter al amplificador)
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
