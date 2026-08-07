#!/bin/bash
# ==============================================================================
# play_random.sh — Script de prototipo (Fallback)
# ==============================================================================
# Este es el script bash original que se usó para las pruebas iniciales.
# Selecciona audios al azar, les aplica variaciones ligeras de tempo/pitch,
# y los reproduce.
#
# Uso:
#   bash play_random.sh /ruta/a/archivos/de/audio
# ==============================================================================

if [ -z "$1" ]; then
    echo "Uso: $0 <directorio_audio>"
    exit 1
fi

AUDIO_DIR="$1"

if [ ! -d "$AUDIO_DIR" ]; then
    echo "Error: el directorio $AUDIO_DIR no existe."
    exit 1
fi

echo "Iniciando reproductor aleatorio..."
echo "Buscando en: $AUDIO_DIR"

while true; do
    # 1. Buscar todos los archivos de audio en el directorio
    # mapfile lee las líneas en un array. find busca archivos válidos.
    mapfile -t files < <(find "$AUDIO_DIR" -type f \( -iname "*.wav" -o -iname "*.mp3" -o -iname "*.flac" -o -iname "*.ogg" \))
    
    if [ ${#files[@]} -eq 0 ]; then
        echo "No se encontraron archivos de audio. Esperando..."
        sleep 10
        continue
    fi
    
    # 2. Elegir un archivo al azar
    RANDOM_INDEX=$((RANDOM % ${#files[@]}))
    CHOSEN_FILE="${files[$RANDOM_INDEX]}"
    
    # 3. Generar variaciones aleatorias para esta reproducción
    # awk es útil acá para hacer cuentas con decimales en bash.
    
    # Tempo entre 0.7 y 1.1
    TEMPO=$(awk -v min=0.7 -v max=1.1 'BEGIN{srand(); print min+rand()*(max-min)}')
    
    # Pitch entre -200 y +200 cents (±2 semitonos)
    PITCH_CENTS=$(( (RANDOM % 401) - 200 ))
    
    # Volumen entre 0.6 y 0.9
    VOL=$(awk -v min=0.6 -v max=0.9 'BEGIN{srand(); print min+rand()*(max-min)}')
    
    # Pausa entre 2 y 8 segundos
    PAUSA=$(( (RANDOM % 7) + 2 ))
    
    # 4. Reproducir
    FILENAME=$(basename "$CHOSEN_FILE")
    echo "------------------------------------------------"
    echo "Reproduciendo: $FILENAME"
    echo "  Vol: $VOL  |  Tempo: $TEMPO  |  Pitch: $PITCH_CENTS"
    
    play "$CHOSEN_FILE" vol "$VOL" tempo "$TEMPO" pitch "$PITCH_CENTS" 2>/dev/null
    
    # 5. Pausa
    echo "Pausa: $PAUSA segs..."
    sleep "$PAUSA"
done
