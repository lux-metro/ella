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

*Ideal para cuando tenés la Pi funcionando y querés actualizar el código con un solo comando.*

---

## Cómo usar el Provisioning Script (Opción 1)

1. Grabá la SD card, conectá la Pi a internet y entrá por SSH (ver `docs/01-raspberry-pi-setup.md`).
2. Una vez adentro de la Pi, corré este comando:

```bash
# Instalación de la Raspberry Pi:
curl -sSL https://raw.githubusercontent.com/lux-metro/ella/main/deploy/provision.sh | bash
```

**¿Qué hace el script exactamente?**
- Actualiza el sistema operativo (`apt update`).
- Instala Python, sox, git y herramientas necesarias.
- Clona este repositorio en `~/ella/repo`.
- Crea un entorno virtual de Python único (`~/ella/repo/.venv`) e instala las dependencias del panel web y del motor de audio.
- Pide las credenciales del Panel Web (usuario/contraseña) y las guarda en `pi/panel/.env`.
- Da al usuario permisos sudo sin contraseña (`NOPASSWD: ALL`), necesarios para que el Panel Web pueda administrar la red, la hora y reiniciar el sistema.
- Instala los servicios systemd de usuario: `panel.service` (panel web), `reproducir.service` (motor de audio Python) y `sentir-presencia.service` (radar ESP32).
- Configura el *hardware watchdog* (reinicia la Pi si se cuelga por completo).
- **NO activa el Access Point** — eso es una decisión del operador (ver abajo).

---

## Access Point (opcional, bajo demanda)

El modo Access Point (red WiFi propia `InstalacionElla`, IP `192.168.4.1`) **no se activa durante la instalación**, sino que se activa cuando lo necesites:

* **Desde el Panel Web:** sección **"Access Point"** → definís la contraseña y pulsás *Activar Access Point*.
* **Por CLI:** `bash ~/ella/repo/pi/setup_pi_access_point.sh`

Para desactivarlo: **Zona de Peligro** del Panel Web (reinicia la Pi) o `bash ~/ella/repo/pi/revertir_wifi.sh`. Ambos usan NetworkManager (nmcli).

---

## Qué pasa después de instalar

Si todo salió bien, la Pi se va a reiniciar sola. Cuando vuelva a arrancar (tarda ~1 minuto), se conectará a tu WiFi local y el motor de audio va a estar funcionando en modo simulado (porque asume que todavía no subiste archivos de audio reales ni conectaste el Arduino).

Para verificar que está funcionando, volvé a entrar por SSH y corré:
```bash
systemctl --user status reproducir
# Para el panel web: systemctl --user status panel
```

El Panel Web queda en `http://<IP_DE_LA_PI>:5000` (buscá la IP con `hostname -I`).

Siguientes pasos lógicos:
1. Subir archivos de audio reales a `~/ella/audio/`
2. Emparejar el parlante Bluetooth (ver `docs/03-audio-setup.md`)
3. Conectar el Arduino y los sensores
4. Ajustar el volumen (ver `docs/03-audio-setup.md`)
5. Cuando la instalación esté montada, activar el Access Point desde el Panel Web
