#!/bin/bash
# ==============================================================================
# provision.sh — Script de instalación automatizada para Raspberry Pi
# ==============================================================================
# Este script configura una Raspberry Pi OS (Lite) desde cero para que corra
# la instalación "ella" de forma autónoma.
#
# Uso:
#   VOICE=a bash provision.sh
# ==============================================================================

set -e # Detener script si algún comando falla

# ------------------------------------------------------------------------------
# 1. Validaciones iniciales
# ------------------------------------------------------------------------------
echo "=== Iniciando instalación de 'ella' ==="

if [ -z "$VOICE" ]; then
    echo "ERROR: Tenés que especificar si esta Pi es la Voz A o la Voz B."
    echo "Uso correcto: VOICE=a bash provision.sh"
    exit 1
fi

if [[ "$VOICE" != "a" && "$VOICE" != "b" ]]; then
    echo "ERROR: VOICE debe ser 'a' o 'b'."
    exit 1
fi

if [ "$EUID" -eq 0 ]; then
    echo "ERROR: Por favor NO corras este script como root (con sudo)."
    echo "Corrélo como el usuario 'pi' normal."
    exit 1
fi

REPO_URL="https://github.com/TU_USUARIO/ella.git"
INSTALL_DIR="/home/$(whoami)/ella"

# ------------------------------------------------------------------------------
# 2. Actualización de sistema y dependencias
# ------------------------------------------------------------------------------
echo "--- Actualizando sistema (esto puede tardar) ---"
sudo apt-get update
sudo apt-get upgrade -y

echo "--- Instalando dependencias ---"
# python3-venv: para crear entornos virtuales
# sox, libsox-fmt-all: para el motor de audio
# git: para bajar el código
sudo apt-get install -y python3-venv sox libsox-fmt-all git alsa-utils curl

# ------------------------------------------------------------------------------
# 3. Clonar repositorio
# ------------------------------------------------------------------------------
echo "--- Configurando el repositorio ---"
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Clonando repositorio en $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
else
    echo "El directorio $INSTALL_DIR ya existe. Actualizando código..."
    cd "$INSTALL_DIR"
    git pull
fi

cd "$INSTALL_DIR"

# ------------------------------------------------------------------------------
# 4. Entorno de Python
# ------------------------------------------------------------------------------
echo "--- Configurando entorno de Python ---"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r pi/shared/requirements.txt

# ------------------------------------------------------------------------------
# 5. Configuración específica de la voz
# ------------------------------------------------------------------------------
echo "--- Configurando Voz $VOICE ---"
if [ "$VOICE" = "a" ]; then
    # Crear un symlink para que config_loader lo encuentre
    ln -sf "$INSTALL_DIR/pi/voice_a/config.yaml" "$INSTALL_DIR/pi/shared/config.yaml"
elif [ "$VOICE" = "b" ]; then
    ln -sf "$INSTALL_DIR/pi/voice_b/config.yaml" "$INSTALL_DIR/pi/shared/config.yaml"
fi

# Crear directorio de audio si no existe
mkdir -p "$INSTALL_DIR/audio"

# ------------------------------------------------------------------------------
# 6. Configuración de Audio (ALSA)
# ------------------------------------------------------------------------------
echo "--- Configurando salida de audio 3.5mm ---"
# Forzar salida por el jack 3.5mm
sudo raspi-config nonint do_audio 1

# Crear configuración de ALSA por defecto
cat << 'EOF' > /home/$(whoami)/.asoundrc
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

# Subir volumen al 85% por defecto
amixer set PCM 85% || true
sudo alsactl store || true

# ------------------------------------------------------------------------------
# 7. Configuración UART (para Arduino)
# ------------------------------------------------------------------------------
echo "--- Habilitando puerto serial UART ---"
# Deshabilitar la consola por serial (que interfiere) pero mantener el hardware port
sudo raspi-config nonint do_serial 2

# Asegurar que el usuario tiene permisos para leer el puerto
sudo usermod -a -G dialout $(whoami)

# ------------------------------------------------------------------------------
# 8. Habilitar Watchdog de Hardware
# ------------------------------------------------------------------------------
echo "--- Habilitando Watchdog (protección contra cuelgues) ---"
if ! grep -q "dtparam=watchdog=on" /boot/config.txt; then
    echo "dtparam=watchdog=on" | sudo tee -a /boot/config.txt
fi
sudo apt-get install -y watchdog
sudo systemctl enable watchdog

# ------------------------------------------------------------------------------
# 9. Instalar servicio systemd
# ------------------------------------------------------------------------------
echo "--- Registrando servicio systemd ---"
bash "$INSTALL_DIR/deploy/install-service.sh"

echo "========================================================================"
echo "✅ Instalación completada exitosamente."
echo "La Raspberry Pi se va a reiniciar en 10 segundos para aplicar los cambios."
echo "(Especialmente permisos de grupos y configuraciones de boot)."
echo ""
echo "Cuando vuelva a arrancar, el audio va a empezar a sonar automáticamente."
echo "Para ver si hay errores, conectate y corré: journalctl -u ella-voice -f"
echo "========================================================================"

sleep 10
sudo reboot
