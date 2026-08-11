#!/bin/bash
# ==============================================================================
# setup_pi_access_point.sh — Activa el modo Access Point en la Raspberry Pi
# ==============================================================================
# Convierte la Raspberry Pi en su propia red WiFi "InstalacionElla" usando
# NetworkManager (nmcli), el gestor de red predeterminado en Raspberry Pi OS
# basado en Debian Trixie / Bookworm.
#
# La IP fija de la Pi será 192.168.4.1 y el panel web quedará en:
#   http://192.168.4.1:5000
#
# La contraseña de la red se lee de ~/ella/credenciales_wifi.txt
# (el Panel Web la crea al activar; también podés crearla a mano).
#
# Uso:
#   bash setup_pi_access_point.sh
# ==============================================================================

set -e

WIFI_CRED_FILE="$HOME/ella/credenciales_wifi.txt"
SSID="InstalacionElla"
CONN_NAME="InstalacionElla"

# ------------------------------------------------------------------------------
# Verificaciones previas
# ------------------------------------------------------------------------------
if [ ! -f "$WIFI_CRED_FILE" ]; then
    echo "Error: No se encontró $WIFI_CRED_FILE"
    echo "Creá el archivo con la contraseña del WiFi (mínimo 8 caracteres):"
    echo "  echo 'MiClaveSecreta' > $WIFI_CRED_FILE"
    exit 1
fi

WIFI_PASSWORD=$(cat "$WIFI_CRED_FILE")
if [ ${#WIFI_PASSWORD} -lt 8 ]; then
    echo "Error: la contraseña debe tener al menos 8 caracteres."
    exit 1
fi

if ! nmcli -t -f RUNNING general status | grep -q "running"; then
    echo "Error: NetworkManager no está corriendo. Verificá el sistema."
    exit 1
fi

echo "Activando Access Point '$SSID' con NetworkManager..."

# ------------------------------------------------------------------------------
# Crear (o recrear) el perfil del Access Point
# ------------------------------------------------------------------------------
nmcli con delete "$CONN_NAME" 2>/dev/null || true

nmcli con add type wifi ifname wlan0 con-name "$CONN_NAME" ssid "$SSID"
nmcli con modify "$CONN_NAME" 802-11-wireless.mode ap
nmcli con modify "$CONN_NAME" wifi-sec.key-mgmt wpa-psk
nmcli con modify "$CONN_NAME" wifi-sec.psk "$WIFI_PASSWORD"
nmcli con modify "$CONN_NAME" ipv4.method shared
nmcli con modify "$CONN_NAME" ipv4.addresses 192.168.4.1/24
nmcli con modify "$CONN_NAME" ipv4.gateway ""
nmcli con modify "$CONN_NAME" ipv6.method ignore

# Nota: dejamos autoconnect por defecto (activado) para que en la galería
# el AP vuelva solo tras un corte de luz. Si querés que la Pi siempre arranque
# conectada a tu WiFi local, desactivalo: nmcli con modify "$CONN_NAME" autoconnect no

nmcli con up "$CONN_NAME"

# ------------------------------------------------------------------------------
# Verificación
# ------------------------------------------------------------------------------
if nmcli -t -f NAME con show --active | grep -q "^$CONN_NAME$"; then
    echo "============================================="
    echo "✅ Access Point activado."
    echo "Red WiFi: $SSID"
    echo "IP de la Raspberry Pi: 192.168.4.1"
    echo "Panel web: http://192.168.4.1:5000"
    echo "============================================="
else
    echo "❌ El Access Point no quedó activo. Revisá:"
    echo "   nmcli con show $CONN_NAME"
    exit 1
fi
