# Resolución de problemas

> Si algo no funciona como debería, esta guía tiene los diagnósticos más comunes. Empezá siempre por el primer síntoma que describe tu situación.

---

## El servicio de audio no arranca

**Síntoma:** `systemctl status ella-voice` muestra `failed` o `inactive`

```bash
# Ver el error exacto:
journalctl -u ella-voice -n 50 --no-pager

# Intentar reiniciar manualmente:
systemctl restart ella-voice
systemctl status ella-voice
```

**Causas comunes:**
- Error de Python en `main.py` — el log muestra el error exacto
- Archivo de audio no encontrado — verificar que haya archivos en `~/ella/audio/`
- Problema de permisos — ver sección de permisos más abajo

---

## No sale sonido

**Síntoma:** El servicio está corriendo pero no se escucha nada

```bash
# Verificar que el volumen no esté en 0:
amixer get PCM

# Subir el volumen:
amixer set PCM 85%

# Probar audio manualmente:
play -n synth 3 sine 440

# Ver qué dispositivo de audio está usando sox:
play -n synth 1 sine 440 -V
```

**Verificar que el dispositivo correcto esté configurado:**
```bash
cat ~/.asoundrc
# Debería mostrar hw:0,0 para salida 3.5mm
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

**Síntoma:** `systemctl status` muestra que reinició muchas veces

```bash
# Ver los últimos errores con timestamps:
journalctl -u ella-voice --since "1 hour ago" --no-pager

# Correr el script manualmente para ver el error completo:
cd ~/ella
python3 pi/main.py
```

El error va a aparecer en la terminal y vas a poder entender qué falló.

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
systemctl status ella-voice

# Reiniciar el servicio:
systemctl restart ella-voice

# Detener el servicio:
systemctl stop ella-voice

# Ver logs en tiempo real:
journalctl -u ella-voice -f

# Ver últimas 100 líneas de log:
journalctl -u ella-voice -n 100 --no-pager

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
