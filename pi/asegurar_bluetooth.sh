#!/bin/bash
# ==============================================================================
# asegurar_bluetooth.sh — Desbloquea y enciende el adaptador Bluetooth
# ==============================================================================
# Se ejecuta en cada boot (servicio systemd ella-bluetooth.service) para
# garantizar operación desatendida: el adaptador puede quedar bloqueado por
# rfkill (Soft blocked: yes) y, sin esto, el scan del panel y la reconexión
# del parlante fallan con "Failed to start discovery: NotReady".
#
# Tiene reintentos: bluetoothd puede tardar unos segundos en estar listo.
# ==============================================================================

set -u

LOG_TAG="ella-bluetooth"

echo "$LOG_TAG: Desbloqueando Bluetooth (rfkill)..."
rfkill unblock bluetooth

for INTENTO in $(seq 1 15); do
    if bluetoothctl show | grep -q "Powered: yes"; then
        echo "$LOG_TAG: Adaptador Bluetooth encendido."
        exit 0
    fi
    echo "$LOG_TAG: Intento $INTENTO/15: encendiendo adaptador..."
    bluetoothctl power on >/dev/null 2>&1
    sleep 2
done

echo "$LOG_TAG: ERROR: no se pudo encender el adaptador Bluetooth." >&2
exit 1
