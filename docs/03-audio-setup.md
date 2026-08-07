# Audio — Configuración de salida

> Esta guía explica cómo configurar la Raspberry Pi para que el audio salga por el conector de 3.5mm (el que conecta al amplificador y de ahí a los exciters). Si estás en fase de prototipo con Bluetooth, igual leé la sección de verificación básica.

---

## El camino del audio en *ella*

```
Raspberry Pi 3
   │  (salida 3.5mm)
   ↓
Cable de audio
   ↓
Amplificador (PAM8403 u otro)
   ↓
Cables a los exciters
   ↓
Exciters pegados a la alfombra
   ↓
🎵 Alfombra vibra como parlante
```

---

## Paso 1 — Forzar salida por 3.5mm

Por defecto, la Raspberry Pi puede intentar mandar audio por HDMI o por el chip de audio. Necesitamos asegurarnos de que siempre use el conector de 3.5mm.

Conectate a la Pi por SSH y escribí:

```bash
# Ver qué dispositivos de audio tiene la Pi
aplay -l
```

Deberías ver algo como:
```
card 0: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]
```

El `card 0, device 0` es la salida de 3.5mm de la Pi. 

Ahora configurá ALSA para que siempre use ese dispositivo:

```bash
# Crear o editar el archivo de configuración de ALSA
cat > ~/.asoundrc << 'EOF'
pcm.!default {
    type hw
    card 0
    device 0
}
ctl.!default {
    type hw
    card 0
}
EOF
```

```bash
# También forzar salida analógica desde la configuración del sistema
sudo raspi-config nonint do_audio 1
```

---

## Paso 2 — Verificar que el audio funciona

```bash
# Instalar archivos de audio de prueba
sudo apt install -y sox alsa-utils

# Reproducir un tono de prueba (440 Hz, 3 segundos)
play -n synth 3 sine 440

# Si no escuchás nada, probar también:
aplay /usr/share/sounds/alsa/Front_Left.wav
```

Si escuchás sonido por el conector de 3.5mm (con auriculares o parlante de prueba conectado), todo está bien. ✅

---

## Paso 3 — Ajustar el volumen

```bash
# Abrir el control de volumen de ALSA
alsamixer
```

En la interfaz:
- Usá las flechas arriba/abajo para subir/bajar volumen
- `F6` para seleccionar la tarjeta de audio si hay más de una
- `ESC` para salir

```bash
# O ajustar directamente desde comando (0-100):
amixer set PCM 85%

# Guardar la configuración de volumen para que persista al reiniciar:
sudo alsactl store
```

---

## Paso 4 — Instalar sox (procesamiento de audio)

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

## Paso 5 — Probar reproducción con sox

```bash
# Copiar un archivo de audio de prueba al directorio correcto
# (reemplazá 'mi_audio.wav' por un archivo que tengas)
cp mi_audio.wav ~/ella/audio/

# Reproducir con sox (debería escucharse por el 3.5mm)
play ~/ella/audio/mi_audio.wav

# Probar con efectos (80% de velocidad, 70% de volumen):
play ~/ella/audio/mi_audio.wav tempo 0.8 vol 0.7
```

---

## Configuración para la instalación final

Una vez que tengas el amplificador y los exciters:

1. Conectar cable de audio 3.5mm: **Pi → entrada del amplificador**
2. Conectar cables de los exciters: **salida del amplificador → exciters**
3. Los exciters se fijan a la base rígida debajo de la alfombra con epoxy o tornillos

> Para más detalles sobre las conexiones físicas, ver [04-wiring.md](04-wiring.md)

---

## Verificación final

Correr el script de test de audio del proyecto:

```bash
cd ~/ella
python3 tests/test_audio.py
```

Este script verifica que:
- La salida de audio esté configurada en el dispositivo correcto
- sox esté instalado
- Haya al menos un archivo de audio en la carpeta configurada

---

*← [02-arduino-setup.md](02-arduino-setup.md) | Siguiente: [04-wiring.md](04-wiring.md) →*
