#!/bin/bash
# ==============================================================================
# provision.sh — Script de instalación automatizada para Instalación Ella
# ==============================================================================
# Este script configura una Raspberry Pi OS desde cero para que corra
# la instalación "Ella" de forma autónoma (incluyendo el Panel Web, 
# el Access Point y el motor de Audio).
#
# Uso:
#   bash provision.sh
# ==============================================================================

set -e # Detener script si algún comando falla

echo "=== Iniciando instalación de Instalación 'Ella' ==="

if [ "$EUID" -eq 0 ]; then
    echo "ERROR: Por favor NO corras este script como root (con sudo)."
    echo "Corrélo como tu usuario normal (ej. pi). El script pedirá sudo cuando haga falta."
    exit 1
fi

PI_USER=$(whoami)
BASE_DIR="$HOME/ella"
REPO_URL="https://github.com/TU_USUARIO/ella.git"

# ------------------------------------------------------------------------------
# 1. Actualización de sistema y dependencias
# ------------------------------------------------------------------------------
echo "--- Actualizando sistema y paquetes (esto puede tardar) ---"
sudo apt-get update
sudo apt-get upgrade -y

echo "--- Instalando dependencias ---"
# sox, libsox-fmt-all: para el motor de audio
# hostapd, dnsmasq: para el access point
# python3-venv, pip, git: para el entorno
sudo apt-get install -y python3-venv python3-pip git sox libsox-fmt-all alsa-utils curl hostapd dnsmasq

# Asegurar pertenencia a grupos (dialout para UART, audio para sonido)
sudo usermod -a -G dialout,audio "$PI_USER"

# ------------------------------------------------------------------------------
# 2. Configuración de Directorios y Clonado
# ------------------------------------------------------------------------------
echo "--- Configurando estructura de directorios ---"
mkdir -p "$BASE_DIR/audio"

# Crear un clip de prueba para que no falle sox al arrancar
if [ ! -f "$BASE_DIR/audio/silencio.wav" ]; then
    echo "Generando archivo de audio de inicialización..."
    sox -n -r 44100 -c 2 "$BASE_DIR/audio/silencio.wav" trim 0.0 1.0
fi

if [ ! -d "$BASE_DIR/repo" ]; then
    echo "Clonando repositorio en $BASE_DIR/repo..."
    # Asumimos que si estamos corriendo este script, ya estamos dentro del repo.
    # Pero si lo bajaron con curl, lo clonamos.
    if [ -d "$(dirname "$0")/../.git" ]; then
        # El script se está corriendo desde el repo clonado
        REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
        echo "Usando repositorio existente en $REPO_DIR"
    else
        git clone "$REPO_URL" "$BASE_DIR/repo"
        REPO_DIR="$BASE_DIR/repo"
    fi
else
    echo "El repositorio ya existe. Actualizando código..."
    cd "$BASE_DIR/repo"
    git pull
    REPO_DIR="$BASE_DIR/repo"
fi

cd "$REPO_DIR"

# ------------------------------------------------------------------------------
# 3. Configuraciones Base e Interacción de Credenciales
# ------------------------------------------------------------------------------
echo "--- Configurando variables de entorno y contraseñas ---"
if [ ! -f "$BASE_DIR/config.env" ]; then
    cp "$REPO_DIR/pi/config.env.example" "$BASE_DIR/config.env"
    echo "✅ Creado $BASE_DIR/config.env"
fi

if [ ! -f "$REPO_DIR/credenciales_wifi.txt" ]; then
    echo ""
    echo "=========================================================="
    echo "🔑 SETUP DE RED WIFI (Access Point)"
    echo "=========================================================="
    read -p "Ingresá la contraseña para la red WiFi 'InstalacionElla' (min 8 caracteres): " WIFI_PASS
    while [ ${#WIFI_PASS} -lt 8 ]; do
        echo "La contraseña debe tener al menos 8 caracteres."
        read -p "Ingresá la contraseña para el WiFi: " WIFI_PASS
    done
    echo "$WIFI_PASS" > "$REPO_DIR/credenciales_wifi.txt"
    echo "✅ Contraseña WiFi guardada."
fi

if [ ! -f "$REPO_DIR/pi/panel/.env" ]; then
    echo ""
    echo "=========================================================="
    echo "🔐 SETUP DEL PANEL DE CONTROL WEB"
    echo "=========================================================="
    read -p "Ingresá el NOMBRE DE USUARIO para acceder al panel: " PANEL_USER
    read -sp "Ingresá la CONTRASEÑA para acceder al panel: " PANEL_PASS
    echo ""
    
    cat <<EOF > "$REPO_DIR/pi/panel/.env"
PANEL_USER=$PANEL_USER
PANEL_PASS=$PANEL_PASS
EOF
    echo "✅ Credenciales del panel web guardadas."
fi

# ------------------------------------------------------------------------------
# 4. Entorno de Python y Panel
# ------------------------------------------------------------------------------
echo "--- Configurando entorno Python para el Panel Web ---"
cd "$REPO_DIR/pi/panel"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd "$REPO_DIR"

# Modificar el ExecStart en panel.service para usar el venv
sed -i "s|ExecStart=/usr/bin/env python3 app.py|ExecStart=$REPO_DIR/pi/panel/venv/bin/python3 app.py|g" "$REPO_DIR/pi/services/panel.service"

# ------------------------------------------------------------------------------
# 5. Permisos Sudoers (Hora)
# ------------------------------------------------------------------------------
echo "--- Configurando permisos Sudoers para la hora ---"
SUDOERS_FILE="/tmp/panel-time"
echo "$PI_USER ALL=(ALL) NOPASSWD: /bin/date" > "$SUDOERS_FILE"
sudo chown root:root "$SUDOERS_FILE"
sudo chmod 0440 "$SUDOERS_FILE"
sudo mv "$SUDOERS_FILE" /etc/sudoers.d/panel-time
echo "✅ Permisos sudoers para comando date configurados."

# ------------------------------------------------------------------------------
# 6. Servicios Systemd
# ------------------------------------------------------------------------------
echo "--- Instalando y Habilitando Servicios Systemd de Usuario ---"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

cp "$REPO_DIR/pi/services/panel.service" "$SYSTEMD_USER_DIR/"
cp "$REPO_DIR/pi/services/sentir-presencia.service" "$SYSTEMD_USER_DIR/"
cp "$REPO_DIR/pi/services/reproducir.service" "$SYSTEMD_USER_DIR/"

systemctl --user daemon-reload
systemctl --user enable panel.service
systemctl --user enable sentir-presencia.service
systemctl --user enable reproducir.service

# Asegurar que systemd de usuario inicie en el boot sin requerir login
sudo loginctl enable-linger $PI_USER

# ------------------------------------------------------------------------------
# 7. Punto de Acceso WiFi
# ------------------------------------------------------------------------------
echo "--- Configurando Punto de Acceso WiFi ---"
chmod +x "$REPO_DIR/pi/setup_pi_access_point.sh"
bash "$REPO_DIR/pi/setup_pi_access_point.sh"

# ------------------------------------------------------------------------------
# 8. Watchdog (Opcional pero recomendado para instalaciones)
# ------------------------------------------------------------------------------
echo "--- Habilitando Watchdog (protección contra cuelgues) ---"
if ! grep -q "dtparam=watchdog=on" /boot/config.txt; then
    echo "dtparam=watchdog=on" | sudo tee -a /boot/config.txt
fi
sudo apt-get install -y watchdog
sudo systemctl enable watchdog

# ------------------------------------------------------------------------------
echo "========================================================================"
echo "✅ Instalación completada exitosamente."
echo "La Raspberry Pi se va a reiniciar en 10 segundos para aplicar los cambios."
echo ""
echo "Al arrancar:"
echo " 1. Se levantará la red WiFi 'InstalacionElla'."
echo " 2. Podrás acceder al panel en http://192.168.4.1:5000"
echo " 3. Desde allí podrás vincular el parlante Bluetooth y gestionar el audio."
echo "========================================================================"

sleep 10
sudo reboot
