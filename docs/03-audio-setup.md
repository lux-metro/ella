# Audio — Configuración de salida (parlante Bluetooth)

> Esta guía explica cómo hacer que el audio de *ella* salga por un parlante Bluetooth. La Raspberry Pi lo empareja una sola vez y después lo reconecta sola.

---

## El camino del audio en *ella*

```
Raspberry Pi
   │  sox/play (motor de audio)
   ↓
ALSA (dispositivo por defecto)
   ↓
PipeWire (sink A2DP)
   ↓
Parlante Bluetooth (emparejado)
   ↓
🎵 Suena la instalación
```

No hace falta conectar ningún cable de audio: el parlante es inalámbrico.

---

## Paso 1 — Emparejar el parlante Bluetooth

La forma más fácil es desde el **Panel Web** (sección **"Bluetooth (Parlantes)"**):

1. Pulsá *Escanear Dispositivos* — los dispositivos van apareciendo en vivo a medida que se descubren.
2. Asegurate de que el parlante esté en **modo emparejamiento** (pairing).
3. Apenas veas tu parlante, pulsá *Detener Escaneo* y después *Conectar* en ese dispositivo. El panel lo empareja, lo confía y lo conecta.

O por consola (SSH):

```bash
bluetoothctl
# Dentro de la consola interactiva:
scan on          # esperá unos segundos y buscá tu parlante
pair <MAC>       # ej: pair FC:58:FA:9E:3F:CD
trust <MAC>
connect <MAC>
exit
```

> ⚠️ Anotá la **MAC** de tu parlante: la vas a necesitar para el paso 3.

---

## Paso 2 — Verificar que el audio funciona

```bash
# Ver que el parlante esté conectado (debe decir "Connected: yes"):
bluetoothctl info <MAC>

# Ver que PipeWire esté corriendo y tenga el parlante como salida:
wpctl status

# Reproducir un tono de prueba (440 Hz, 3 segundos):
play -n synth 3 sine 440
```

Si escuchás el tono por el parlante Bluetooth, todo está bien. ✅

---

## Paso 3 — Configurar el parlante en *ella*

Para que el motor de audio reconecte el parlante automáticamente (por ejemplo tras un reinicio de la Pi), editá `pi/config.yaml` y completá:

```yaml
mac_parlante_bluetooth: "FC:58:FA:9E:3F:CD"
```

Reemplazá la MAC por la de tu parlante. Si la dejás vacía, el sistema usa el dispositivo de audio por defecto sin intentar reconectar.

---

## Paso 4 — Ajustar el volumen

El parlante tiene su propio volumen físico, pero también podés ajustarlo desde la Pi:

```bash
# Listar los sinks de PipeWire (anotá el ID del parlante, en la sección "Audio"):
wpctl status

# Subir/bajar el volumen de un sink (ej: 85%):
wpctl set-volume <ID_del_sink> 0.85

# O con la interfaz de ALSA:
alsamixer
# F6 para elegir tarjeta, flechas para subir/bajar, ESC para salir
```

---

## Paso 5 — Instalar sox (procesamiento de audio)

El motor de audio de *ella* usa `sox` para reproducir archivos y aplicar efectos en tiempo real (velocidad, volumen).

```bash
sudo apt install -y sox libsox-fmt-all
```

Verificar:
```bash
sox --version
# Debería mostrar algo como: sox v14.4.2
```

---

## Paso 6 — Probar reproducción con sox

```bash
# Copiar un archivo de audio de prueba al directorio correcto
# (reemplazá 'mi_audio.wav' por un archivo que tengas)
cp mi_audio.wav ~/ella/audio/

# Reproducir con sox (debería escucharse por el parlante Bluetooth)
play ~/ella/audio/mi_audio.wav

# Probar con efectos (80% de velocidad, 70% de volumen):
play ~/ella/audio/mi_audio.wav tempo 0.8 vol 0.7
```

---

## Verificación final

Correr el script de test de audio del proyecto:

```bash
cd ~/ella
python3 tests/test_audio.py
```

Este script verifica que:
- sox esté instalado
- Haya al menos un archivo de audio en la carpeta configurada
- La salida de audio funcione (reproduce un tono de prueba)

---

*← [02-arduino-setup.md](02-arduino-setup.md) | Siguiente: [04-wiring.md](04-wiring.md) →*
