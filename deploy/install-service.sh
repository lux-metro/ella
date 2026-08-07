#!/bin/bash
# ==============================================================================
# install-service.sh — Instala el servicio systemd para *ella*
# ==============================================================================
# Este script toma la plantilla ella-voice.service, la configura con las rutas
# correctas para el usuario actual, y la registra en el sistema.
#
# Se llama automáticamente desde provision.sh, pero podés correrlo a mano si
# necesitás reinstalar el servicio.
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_ROOT="$(dirname "$DIR")"
USER_NAME="$(whoami)"

SERVICE_FILE="$DIR/ella-voice.service"
SYSTEMD_DIR="/etc/systemd/system"
TARGET_SERVICE="$SYSTEMD_DIR/ella-voice.service"

echo "Instalando servicio systemd en $TARGET_SERVICE..."

# Crear un archivo temporal para el servicio con las rutas reemplazadas
TMP_SERVICE=$(mktemp)

# Leer la plantilla y reemplazar los placeholders
sed -e "s|{{ user_name }}|$USER_NAME|g" \
    -e "s|{{ install_dir }}|$PROJECT_ROOT|g" \
    "$SERVICE_FILE" > "$TMP_SERVICE"

# Mover el archivo final a la carpeta de systemd (requiere sudo)
sudo mv "$TMP_SERVICE" "$TARGET_SERVICE"
sudo chown root:root "$TARGET_SERVICE"
sudo chmod 644 "$TARGET_SERVICE"

# Recargar systemd y habilitar el servicio
sudo systemctl daemon-reload
sudo systemctl enable ella-voice.service

echo "Servicio instalado y habilitado para arrancar en el próximo reinicio."
echo "Para arrancarlo ahora, usá: sudo systemctl start ella-voice"
