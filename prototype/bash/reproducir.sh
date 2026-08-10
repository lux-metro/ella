#!/bin/bash
CONFIG_FILE=~/ruidosa/config.env
CLIPS_DIR=~/ruidosa/clips

# Default values
VOL_MIN=0.3
VOL_MAX=1.0
SPEED_MIN=0.85
SPEED_MAX=1.35

if [ -f "$CONFIG_FILE" ]; then
  export $(grep -v '^#' "$CONFIG_FILE" | xargs)
fi
MAC="FC:58:FA:9E:3F:CD"
 
for i in $(seq 1 20); do
  bluetoothctl info "$MAC" | grep -q "Connected: yes" && break
  bluetoothctl connect "$MAC" > /dev/null 2>&1
  sleep 3
done

while true; do
  clip=$(ls "$CLIPS_DIR"/*.wav | shuf -n 1)
  vol=$(awk -v min="$VOL_MIN" -v max="$VOL_MAX" 'BEGIN{srand(); print min+rand()*(max-min)}')
  speed=$(awk -v min="$SPEED_MIN" -v max="$SPEED_MAX" 'BEGIN{srand(); print min+rand()*(max-min)}')
  play "$clip" vol "$vol" speed "$speed"
  sleep $(( (RANDOM % 4) + 2 ))
done