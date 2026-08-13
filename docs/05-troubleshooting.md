# Resolución de problemas

> Si algo no funciona como debería, esta guía tiene los diagnósticos más comunes. Empezá siempre por el primer síntoma que describe tu situación.

---

## El servicio de audio no arranca

**Síntoma:** `systemctl --user status reproducir` muestra `failed` o `inactive`

```bash
# Ver el error exacto:
journalctl --user -u reproducir -n 50 --no-pager

# Intentar reiniciar manualmente:
systemctl --user restart reproducir
systemctl --user status reproducir
```

**Causas comunes:**
- Error de Python en `main.py` — el log muestra el error exacto
- Archivo de audio no encontrado — verificar que haya archivos en `~/ella/audio/`
- Problema de permisos — ver sección de permisos más abajo

---

## No sale sonido

**Síntoma:** El servicio está corriendo pero no se escucha nada

```bash
# 1. Verificar que el parlante Bluetooth esté conectado
bluetoothctl info <MAC>
# Tiene que decir "Connected: yes". Si no, probá conectar:
bluetoothctl connect <MAC>

# 2. Verificar que PipeWire esté corriendo:
wpctl status

# 3. Verificar que el volumen del sink no esté en 0:
wpctl get-volume <ID_del_sink>

# Subir el volumen del sink (ej: 85%):
wpctl set-volume <ID_del_sink> 0.85

# 4. Probar audio manualmente:
play -n synth 3 sine 440
```

> El motor de audio intenta reconectar el parlante automáticamente antes de reproducir, **solo si** hay una MAC configurada: en `~/ella/bluetooth_mac.txt` (la escribe el Panel Web al conectar) o, como fallback, en `mac_parlante_bluetooth` de `pi/config.yaml`. El archivo runtime tiene prioridad.

---

## El parlante Bluetooth no se conecta solo

**Síntoma:** Tras un reinicio de la Pi, el audio no sale (el parlante quedó desconectado).

1. Verificá que el parlante esté encendido y cargado.
2. Desde el Panel Web → **"Bluetooth (Parlantes)"** → *Escanear* y *Conectar* para re-emparejarlo. Al conectar, el panel guarda la MAC en `~/ella/bluetooth_mac.txt` automáticamente.
3. Verificá que quedó configurado: en la card Bluetooth debe aparecer la sección **"Parlante configurado"** con tu dispositivo y su estado.
4. Reiniciá el servicio: `systemctl --user restart reproducir`

---

## "Conectar" falla con `br-connection-profile-unavailable`

**Síntoma:** Al pulsar *Conectar* en el Panel Web (o `bluetoothctl connect <MAC>`) sale `Failed to connect: org.bluez.Error.Failed br-connection-profile-unavailable`, y `wpctl status` no muestra ninguna tarjeta bluetooth.

**Causa:** En instalaciones **headless** (sin sesión gráfica, p. ej. solo por SSH), el monitor bluez de WirePlumber por defecto solo registra los perfiles de audio Bluetooth en el *seat activo* de logind. Sin seat activo, el perfil **A2DP nunca se registra** y la conexión falla con ese error.

**Solución:** desactivar el seat-monitoring de WirePlumber:

```bash
mkdir -p ~/.config/wireplumber/wireplumber.conf.d
cat > ~/.config/wireplumber/wireplumber.conf.d/51-disable-seat-monitoring.conf << 'EOF'
wireplumber.profiles = {
  main = {
    monitor.bluez.seat-monitoring = disabled
  }
}
EOF
systemctl --user restart wireplumber
```

Luego reintentá *Conectar* desde el Panel. Para verificar que quedó bien, `wpctl status` debería mostrar el parlante como dispositivo/sink bluez cuando esté conectado.

> `deploy/provision.sh` ya genera esta configuración en instalaciones nuevas.

---

## El escaneo de Bluetooth no encuentra dispositivos

**Síntoma:** En el Panel Web, *Escanear dispositivos* queda "Escaneando…" pero no aparece ningún dispositivo (o el estado muestra el error "Failed to start discovery: NotReady").

**Causa más común:** el adaptador Bluetooth quedó **bloqueado por software** (rfkill) y/o **apagado**. El scan es interactivo: corre hasta que lo detenés (o hasta el auto-stop de 60 s). Si pasan varios segundos sin que aparezca ningún `[NEW]`, el escaneo probablemente no arrancó.

```bash
# Verificar el estado del adaptador:
rfkill list                      # ¿Bluetooth "Soft blocked: yes"?
bluetoothctl show                # ¿Powered: yes?
systemctl status bluetooth       # ¿bluetoothd corriendo?
```

**Solución:** desbloquear y encender el adaptador:

```bash
sudo rfkill unblock bluetooth
bluetoothctl power on
```

Para que esto quede garantizado en cada arranque (operación desatendida), el deploy instala:

- **`ella-bluetooth.service`** — servicio systemd que desbloquea y enciende el adaptador en cada boot.
- **`99-bluetooth-unblock.rules`** — regla udev que fuerza el desbloqueo al aparecer el dispositivo rfkill.
- **`AutoEnable=true`** en `/etc/bluetooth/main.conf` — bluetoothd enciende el adaptador solo.

Verificar el servicio:

```bash
systemctl status ella-bluetooth.service
sudo journalctl -u ella-bluetooth.service
```

---

## No llegan datos del Arduino

**Síntoma:** El log muestra "Modo simulado activo" o errores de puerto serial

```bash
# Verificar que el Arduino está conectado:
ls /dev/ttyUSB* /dev/ttyACM*

# Ver qué está mandando el Arduino (si está conectado por USB):
cat /dev/ttyUSB0  # o el puerto que aparezca

# Verificar permisos del puerto:
ls -la /dev/ttyUSB0
# Debería mostrar "dialout" en el grupo
```

```bash
# Agregar usuario al grupo dialout (si no tiene acceso):
sudo usermod -a -G dialout pi
# Cerrar sesión y volver a entrar
```

---

## El ESP32 no se conecta al WiFi (escanea las redes pero falla)

**Síntoma:** El ESP32 escanea las redes con buen RSSI, pero la conexión siempre falla (el log del Arduino IDE muestra `Reason: 2 - AUTH_EXPIRE`), incluso contra redes abiertas sin contraseña.

**Causa:** Falla conocida del front-end RF de algunos módulos ESP32-C3 Super Mini: a máxima potencia, la señal TX se refleja y se auto-cancela, y el AP no llega a decodificar las tramas (el scan, que solo recibe, sí funciona).

**Solución:** en el sketch, inmediatamente después de `WiFi.begin(ssid, password)`:

```cpp
WiFi.setTxPower(WIFI_POWER_8_5dBm);
```

Y en `setup()`:

```cpp
WiFi.setSleep(false);
```

Si el módulo conecta y se comporta bien, se puede ir subiendo gradualmente la potencia para mejorar el alcance.

---

## La Pi no arranca o se queda trabada

**Síntoma:** La Pi no responde por SSH, LED de actividad no parpadea

Posibles causas:
1. **SD card corrupta** — ocurre si la Pi se apagó bruscamente mientras escribía
   - Solución: volver a grabar la SD card con Raspberry Pi Imager
   - Prevención: usar un UPS o asegurarse de apagar con `sudo shutdown -h now` antes de cortar la luz
   
2. **Fuente de alimentación insuficiente** — la Pi 3 necesita mínimo 2.5A
   - Síntoma adicional: ícono de rayo en el monitor (si tiene monitor conectado)
   
3. **Falla del watchdog** — si el watchdog detecta que el sistema está colgado, reinicia la Pi automáticamente. Si esto pasa muchas veces, hay un problema más profundo.

---

## El servicio se reinicia constantemente (crash loop)

**Síntoma:** `systemctl --user status reproducir` muestra que reinició muchas veces

```bash
# Ver los últimos errores con timestamps:
journalctl --user -u reproducir --since "1 hour ago" --no-pager

# Correr el script manualmente para ver el error completo:
cd ~/ella/repo
.venv/bin/python pi/shared/main.py
```

El error va a aparecer en la terminal y vas a poder entender qué falló.

---

## El panel web no está disponible

**Síntoma:** no podés entrar a `http://<IP>:5000`

Posibles causas y soluciones:

1. **No sabés cuál es la IP de la Pi.** Desde la consola (SSH), buscá la IP local:
   ```bash
   hostname -I
   ```
   Si el Access Point está activo, la IP es fija: `192.168.4.1`.

2. **El servicio del panel no está corriendo.**
   ```bash
   systemctl --user status panel
   journalctl --user -u panel -n 50 --no-pager
   ```

3. **El Access Point está activo pero te conectaste a otra red.** Cuando el AP está activo, el panel solo se ve desde la red `InstalacionElla` (a menos que uses ethernet).

4. **Cambiaste de modo (AP ↔ WiFi local) y no reconectaste.** Al activar o desactivar el AP, el navegador tiene que conectarse a la red correspondiente:
   - AP activo → red `InstalacionElla`, panel en `192.168.4.1:5000`
   - AP inactivo → tu WiFi local, panel en `http://<IP_DE_LA_PI>:5000`

---

## Activar / desactivar el Access Point

**Activar** (modo aislado, para la sala de exposición):

* Desde el Panel Web → sección **"Access Point"** → contraseña + *Activar Access Point*.
* O por CLI: `bash ~/ella/repo/pi/setup_pi_access_point.sh`
  (la contraseña se guarda en `~/ella/credenciales_wifi.txt`, mínimo 8 caracteres).

**Desactivar** (volver a tu WiFi local):

* Desde el Panel Web → **Reset de access point (CUIDADO)** (reinicia la Pi).
* O por CLI: `bash ~/ella/repo/pi/revertir_wifi.sh`

> El Access Point usa **NetworkManager** (nmcli). Para ver su estado:
> ```bash
> nmcli con show --active
> ```
> La red `InstalacionElla` debe figurar como activa cuando el AP está encendido.

---

## Errores de Python

**Síntoma:** El log muestra texto con "Traceback" o "Error"

Los errores más comunes:

| Error | Causa | Solución |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'serial'` | Falta instalar dependencias | `pip3 install -r pi/shared/requirements.txt` |
| `FileNotFoundError: audio/` | No hay archivos de audio | Copiar archivos a `~/ella/audio/` |
| `PermissionError: /dev/ttyS0` | Sin permisos para el puerto serial | `sudo usermod -a -G dialout pi` |
| `OSError: [Errno 2] No such file or directory: 'play'` | sox no está instalado | `sudo apt install sox` |

---

## Verificar el estado general del sistema

```bash
# Temperatura de la CPU (no debería superar 80°C):
vcgencmd measure_temp

# Uso de CPU y memoria:
top -bn1 | head -20

# Espacio en disco:
df -h

# Uptime (cuánto tiempo lleva encendida):
uptime

# Últimos reinicios del sistema:
last reboot | head -5
```

---

## Comandos útiles de referencia rápida

```bash
# Ver estado del servicio:
systemctl --user status reproducir

# Reiniciar el servicio:
systemctl --user restart reproducir

# Detener el servicio:
systemctl --user stop reproducir

# Ver logs en tiempo real:
journalctl --user -u reproducir -f

# Ver últimas 100 líneas de log:
journalctl --user -u reproducir -n 100 --no-pager

# Reiniciar la Pi de forma segura:
sudo shutdown -r now

# Apagar la Pi de forma segura:
sudo shutdown -h now
```

---

## Si nada de esto funciona

1. Corré los scripts de test:
   ```bash
   cd ~/ella
   python3 tests/test_audio.py
   python3 tests/test_serial.py
   python3 tests/test_sensors.py
   ```
   
2. Revisá los logs completos del día:
   ```bash
   journalctl --since "today" --no-pager > ~/logs-hoy.txt
   ```
   Ese archivo tiene todo el historial de actividad del sistema.

3. Como último recurso, el script bash del prototipo siempre está disponible:
   ```bash
   bash ~/ella/prototype/bash/play_random.sh ~/ella/audio/
   ```
   Esto reproduce audio sin depender de ningún servicio del sistema.

---

*← [04-wiring.md](04-wiring.md) | [README principal](../README.md) →*
