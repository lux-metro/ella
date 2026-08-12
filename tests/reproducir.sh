#!/bin/bash
#
# reproducir.sh
#
# Reproduce en bucle infinito los sonidos de ~/ruidosa/clips/, cambiando
# el volumen y la velocidad de forma aleatoria en cada clip.
#
# NOVEDAD: ahora además lee el archivo /tmp/intensidad.txt (que escribe
# escucha_radar.py) para que el sonido suene más presente cuando hay
# alguien cerca del tapiz, y más apagado cuando no hay nadie.
#
# OJO: esta es una versión nueva armada a partir de cómo me contaste
# que funcionaba tu script. Si ya tenías cosas específicas en tu
# reproducir.sh original (nombres de carpetas distintos, efectos de
# sox particulares, etc.), pasámelo y lo fusiono en vez de reemplazarlo.

# ===================== CONFIGURACIÓN =====================

CARPETA_CLIPS="$HOME/ruidosa/clips"
ARCHIVO_INTENSIDAD="/tmp/intensidad.txt"

# Dirección MAC del parlante Bluetooth.
# Revisá que sea la MAC real de tu parlante (no la de ejemplo).
MAC_PARLANTE="AA:BB:CC:DD:EE:FF"

# Volumen base (0.0 a 1.0) cuando NO hay nadie cerca
VOLUMEN_BASE_MIN=0.15
VOLUMEN_BASE_MAX=0.35

# Volumen extra que se suma según la intensidad de movimiento (0.0 a 1.0)
VOLUMEN_EXTRA_MAX=0.6

# Pausa entre clips, en segundos, cuando NO hay nadie cerca
PAUSA_MIN=3
PAUSA_MAX=10

# ============================================================


conectar_parlante() {
    echo "Intentando conectar el parlante Bluetooth ($MAC_PARLANTE)..."
    bluetoothctl connect "$MAC_PARLANTE"
}

leer_intensidad() {
    if [ -f "$ARCHIVO_INTENSIDAD" ]; then
        cat "$ARCHIVO_INTENSIDAD"
    else
        # Si todavía no existe el archivo (por ejemplo, escucha_radar.py
        # no arrancó), asumimos que no hay nadie cerca.
        echo "0.0"
    fi
}

# Nos aseguramos de que el parlante esté conectado antes de arrancar
conectar_parlante

while true; do

    # Si el parlante se desconectó en algún momento, probamos reconectar
    if ! bluetoothctl info "$MAC_PARLANTE" | grep -q "Connected: yes"; then
        conectar_parlante
        sleep 2
    fi

    INTENSIDAD=$(leer_intensidad)

    # Elegimos un clip al azar de la carpeta
    CLIP=$(find "$CARPETA_CLIPS" -name "*.wav" | shuf -n 1)

    if [ -z "$CLIP" ]; then
        echo "No se encontraron archivos .wav en $CARPETA_CLIPS"
        sleep 5
        continue
    fi

    # Volumen base al azar dentro del rango configurado
    VOLUMEN_BASE=$(awk -v min="$VOLUMEN_BASE_MIN" -v max="$VOLUMEN_BASE_MAX" \
        'BEGIN{srand(); print min+rand()*(max-min)}')

    # Le sumamos la parte que depende de la intensidad (movimiento cerca)
    VOLUMEN=$(awk -v base="$VOLUMEN_BASE" -v intensidad="$INTENSIDAD" -v extra="$VOLUMEN_EXTRA_MAX" \
        'BEGIN{print base + (intensidad*extra)}')

    # Velocidad al azar, entre 0.9 y 1.15
    VELOCIDAD=$(awk 'BEGIN{srand(); print 0.9+rand()*0.25}')

    echo "Reproduciendo: $(basename "$CLIP") | volumen=$VOLUMEN | velocidad=$VELOCIDAD | intensidad=$INTENSIDAD"

    play -q "$CLIP" vol "$VOLUMEN" speed "$VELOCIDAD" 2>/dev/null

    # La pausa entre clips se achica cuando hay más intensidad (más movimiento)
    PAUSA=$(awk -v min="$PAUSA_MIN" -v max="$PAUSA_MAX" -v intensidad="$INTENSIDAD" \
        'BEGIN{srand(); rango=max-min; pausa=max-(intensidad*rango); print pausa*(0.7+rand()*0.6)}')

    sleep "$PAUSA"

done
