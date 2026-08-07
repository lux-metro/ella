# Scripts de Instalación (Deploy)

> Esta carpeta contiene las herramientas para instalar y configurar la Raspberry Pi de forma automática.

---

## Opciones de instalación

Tenés dos formas de instalar *ella*. Elegí la que te parezca más cómoda.

### Opción 1: Provisioning Script (`provision.sh`) — Recomendado para empezar
Es un solo comando que corrés **adentro** de la Raspberry Pi. Hace todo por vos: instala dependencias, configura el audio, habilita puertos y deja el servicio corriendo.

*Ideal para cuando tenés una sola Pi o es la primera vez que armás la instalación.*

### Opción 2: Ansible (`ansible/`) — Más avanzado
Es un sistema que corrés en **tu computadora**, y que se conecta a la(s) Pi por red para configurarlas sin que tengas que tocarlas.

*Ideal para cuando tenés las dos Pi funcionando y querés actualizar el código en ambas al mismo tiempo con un solo comando.*

---

## Cómo usar el Provisioning Script (Opción 1)

1. Grabá la SD card, conectá la Pi a internet y entrá por SSH (ver `docs/01-raspberry-pi-setup.md`).
2. Una vez adentro de la Pi, corré este comando:

```bash
# Para instalar la Voz A:
curl -sSL https://raw.githubusercontent.com/TU_USUARIO/ella/main/deploy/provision.sh | VOICE=a bash
```

> **IMPORTANTE:** Cambiá `TU_USUARIO` por tu usuario de GitHub. Si el repositorio es privado, vas a tener que clonarlo manualmente primero.

**¿Qué hace el script exactamente?**
- Actualiza el sistema operativo (`apt update`).
- Instala Python, sox, git y herramientas necesarias.
- Clona este repositorio en `/home/pi/ella`.
- Crea el entorno virtual de Python e instala dependencias (`requirements.txt`).
- Configura ALSA para forzar la salida de audio por el conector 3.5mm.
- Habilita el puerto UART por hardware (para hablar con el Arduino).
- Configura el *hardware watchdog* (reinicia la Pi si se cuelga por completo).
- Instala el servicio systemd (`ella-voice.service`) para que el audio arranque solo al encender la Pi.

---

## Qué pasa después de instalar

Si todo salió bien, la Pi se va a reiniciar sola. Cuando vuelva a arrancar (tarda ~1 minuto), el motor de audio va a estar funcionando en modo simulado (porque asume que todavía no subiste archivos de audio reales ni conectaste el Arduino).

Para verificar que está funcionando, volvé a entrar por SSH y corré:
```bash
systemctl status ella-voice
```

Siguientes pasos lógicos:
1. Subir archivos de audio reales a `~/ella/audio/`
2. Conectar el Arduino y los exciters
3. Ajustar el volumen (ver `docs/03-audio-setup.md`)
