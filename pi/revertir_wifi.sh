#!/bin/bash
# ==============================================================================
# revertir_wifi.sh — Desactiva el modo Access Point y restaura la WiFi cliente
# ==============================================================================
# Elimina el perfil "InstalacionElla" de NetworkManager. Al reiniciar, la Pi
# volverá a conectarse automáticamente a tu red WiFi local (o por ethernet).
#
# Uso:
#   bash revertir_wifi.sh
# ==============================================================================

set -e

CONN_NAME="InstalacionElla"

echo "Desactivando Access Point y restaurando WiFi cliente..."

# 1. Bajar y eliminar el perfil del AP
nmcli con down "$CONN_NAME" 2>/dev/null || true
nmcli con delete "$CONN_NAME" 2>/dev/null || true

# 2. Asegurar que la radio WiFi esté encendida (para volver a conectar)
nmcli radio wifi on

echo "============================================="
echo "✅ Modo Access Point desactivado."
echo "La Raspberry Pi volverá a conectarse a tu red WiFi normal"
echo " (la que tenías configurada antes de activar el AP)."
echo "Es recomendable reiniciar con: sudo reboot"
echo "============================================="
