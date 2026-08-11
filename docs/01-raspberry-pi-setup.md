# Raspberry Pi — Setup inicial

> Esta guía cubre todo desde cero: cómo grabar la SD card, cómo arrancar la Pi por primera vez, y cómo dejarla lista para instalar el software de *ella*.

---

## Qué vas a necesitar para esta guía

- 1× Raspberry Pi 3 Model B
- 1× SD card (mínimo 8GB, clase 10)
- Tu computadora Linux
- Cable de red ethernet (recomendado, más confiable que wifi para el primer setup)
- Router con un puerto ethernet libre

---

## Paso 1 — Descargar Raspberry Pi Imager

Raspberry Pi Imager es un programa gráfico (con botones, no comandos) que graba el sistema operativo en la SD card.

1. En tu computadora Linux, abrí una terminal y escribí:
   ```bash
   sudo apt install rpi-imager
   ```
   Si te pide contraseña, es la contraseña de tu computadora (no se ve mientras escribís, es normal).

2. Abrí Raspberry Pi Imager desde el menú de aplicaciones, o escribí:
   ```bash
   rpi-imager
   ```

---

## Paso 2 — Grabar la SD card

Con Raspberry Pi Imager abierto:

1. **"Choose Device"** → Elegí **Raspberry Pi 3**

2. **"Choose OS"** → Elegí:
   - **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (64-bit)**
   
   > "Lite" significa sin interfaz gráfica — es lo que queremos. La Pi va a correr sin monitor.

3. **"Choose Storage"** → Elegí tu SD card
   
   > ⚠️ CUIDADO: todo lo que había en la SD card se va a borrar. Asegurate de elegir la SD card y no otro disco.

4. Hacé click en **"Next"**

5. Va a aparecer un diálogo que pregunta si querés personalizar la configuración. Hacé click en **"Edit Settings"** y configurá:

   **En la pestaña "General":**
   - ✅ Set hostname: `ella-voz-a`
   - ✅ Set username and password:
     - Username: `pi`
     - Password: elegí una que recuerdes, la vas a necesitar
   - ✅ Configure wireless LAN (opcional, solo si no usás cable ethernet)
   - ✅ Set locale settings: tu zona horaria y teclado

   **En la pestaña "Services":**
   - ✅ Enable SSH: **Use password authentication**

   Hacé click en **"Save"**, luego en **"Yes"** para aplicar la configuración.

6. Confirmá que querés grabar. El proceso tarda 5-10 minutos.

---

## Paso 3 — Primer arranque

1. Insertá la SD card en la Raspberry Pi (la ranura está en la parte de abajo de la placa)

2. Conectá el cable ethernet entre la Pi y tu router

3. Conectá la alimentación (cable micro-USB)

4. La Pi tarda aproximadamente 60 segundos en arrancar la primera vez

---

## Paso 4 — Conectarte por SSH

SSH te permite controlar la Pi desde tu computadora, sin necesitar conectarle monitor ni teclado.

1. Primero necesitás saber la IP de la Pi. Podés probar directamente con el hostname:
   ```bash
   ssh pi@ella-voz-a.local
   ```
   
   Si eso no funciona (algunos routers no soportan `.local`), buscá la IP en la interfaz de tu router, o usá:
   ```bash
   nmap -sn 192.168.1.0/24 | grep ella
   ```
   
   > Reemplazá `192.168.1.0/24` por el rango de tu red si es diferente (preguntale a ChatGPT cómo encontrarlo si no sabés).

2. La primera vez que te conectás, va a aparecer un mensaje de advertencia de seguridad. Escribí `yes` y Enter.

3. Te va a pedir la contraseña que elegiste en el paso 2. Escribila (no se ve, es normal) y Enter.

4. Si todo salió bien, deberías ver algo como:
   ```
   pi@ella-voz-a:~ $
   ```
   
   ¡Ya estás adentro de la Pi!

---

## Paso 5 — Instalar el software de ella

Ahora que estás conectado a la Pi, el siguiente paso es correr el script de instalación automática. Seguí los pasos en [deploy/README.md](../deploy/README.md).

**El camino rápido (si ya subiste el repositorio a GitHub):**

```bash
# En la terminal de la Pi, escribí:
curl -sSL https://raw.githubusercontent.com/TU_USUARIO/ella/main/deploy/provision.sh | bash
```

Reemplazá `TU_USUARIO` con tu usuario de GitHub.

Si preferís clonar el repositorio primero:
```bash
git clone https://github.com/TU_USUARIO/ella.git
cd ella
bash deploy/provision.sh
```

---

## Paso 6 — Verificar que todo funciona

```bash
# Ver el estado de los servicios (corren como servicios de usuario):
systemctl --user status reproducir
systemctl --user status panel
systemctl --user status sentir-presencia

# Ver los últimos logs del motor de audio:
journalctl --user -u reproducir -n 50

# Ver logs en tiempo real (salir con Ctrl+C):
journalctl --user -u reproducir -f
```

Si el servicio aparece como `active (running)`, todo está bien. El Panel Web queda en `http://<IP_DE_LA_PI>:5000` (buscá la IP con `hostname -I`).

---

## Notas para cuando tengás la segunda Pi

La segunda Pi se configura igual (con Raspberry Pi Imager, el hostname sería `ella-voz-b`):

```bash
curl -sSL https://raw.githubusercontent.com/TU_USUARIO/ella/main/deploy/provision.sh | bash
```

---

*← [00-antes-de-empezar.md](00-antes-de-empezar.md) | Siguiente: [02-arduino-setup.md](02-arduino-setup.md) →*
