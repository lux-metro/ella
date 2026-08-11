#!/bin/bash
# ==============================================================================
# provision.sh — Script de instalación automatizada para Instalación Ella
# ==============================================================================
# Este script configura una Raspberry Pi OS desde cero para que corra
# la instalación "Ella" de forma autónoma (Panel Web, servicios y motor
# de Audio). El modo Access Point NO se activa acá: queda a pedido del
# operador, desde el Panel Web o con pi/setup_pi_access_point.sh.
#
# Uso (una sola línea, hace todo: instala git, clona el repo y configura):
#   curl -sSL https://raw.githubusercontent.com/lux-metro/ella/main/deploy/provision.sh | bash
#
# También podés clonar manualmente y correrlo:
#   git clone https://github.com/lux-metro/ella.git ~/ella/repo
#   cd ~/ella/repo
#   bash deploy/provision.sh
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
REPO_URL="https://github.com/lux-metro/ella.git"

# ------------------------------------------------------------------------------
# 1. Actualización de sistema y dependencias
# ------------------------------------------------------------------------------
echo "--- Actualizando sistema y paquetes (esto puede tardar) ---"
# Si una corrida anterior quedó interrumpida, dpkg puede estar a medio
# configurar y bloquear apt. Lo dejamos consistente antes de seguir.
sudo DEBIAN_FRONTEND=noninteractive dpkg --configure -a
sudo apt-get update
sudo apt-get upgrade -y

echo "--- Instalando dependencias ---"
# sox, libsox-fmt-all: para el motor de audio
# network-manager: gestión de red (el Access Point se arma con nmcli)
# pulseaudio, pulseaudio-module-bluetooth: para la salida por parlante Bluetooth
# python3-venv, pip, git: para el entorno
sudo apt-get install -y python3-venv python3-pip git sox libsox-fmt-all alsa-utils curl network-manager pulseaudio pulseaudio-module-bluetooth

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

# Detectar el repositorio. El script puede correrse de dos formas:
#   a) Con curl | bash (git ya se instaló en el paso 1): clonamos a ~/ella/repo.
#   b) Desde un clon manual: usamos esa ubicación.
# Se detecta con el marcador pi/services/panel.service (no con .git, porque
# en el flujo curl|bash $0 es 'bash' y el chequeo de .git puede fallar).
if [ -d "$BASE_DIR/repo/.git" ]; then
    echo "El repositorio ya existe. Actualizando código..."
    cd "$BASE_DIR/repo"
    git pull
    REPO_DIR="$BASE_DIR/repo"
elif [ -f "$(dirname "$0")/../pi/services/panel.service" ]; then
    REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
    echo "Usando repositorio existente en $REPO_DIR"
else
    echo "Clonando repositorio en $BASE_DIR/repo..."
    git clone "$REPO_URL" "$BASE_DIR/repo"
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

# Nota: la contraseña de la red WiFi 'InstalacionElla' NO se pide acá.
# Se define cuando se activa el Access Point (desde el Panel Web o por CLI),
# y se guarda en ~/ella/credenciales_wifi.txt.

if [ ! -f "$REPO_DIR/pi/panel/.env" ]; then
    # Si vinimos por 'curl | bash', el stdin es la tubería y 'read' no lee del
    # teclado. Redirigimos stdin a la terminal cuando no es una tty.
    if [ ! -t 0 ]; then
        exec < /dev/tty 2>/dev/null || true
    fi
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
echo "--- Configurando entorno Python (venv unificado) ---"
cd "$REPO_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r pi/panel/requirements.txt
pip install -r pi/shared/requirements.txt
deactivate
cd "$REPO_DIR"

# ------------------------------------------------------------------------------
# 5. Permisos Sudoers (NOPASSWD)
# ------------------------------------------------------------------------------
echo "--- Configurando permisos Sudoers (NOPASSWD) ---"
# El panel web ejecuta comandos de sistema (red, hora, reinicio) desde un
# servicio systemd sin terminal. NOPASSWD: ALL habilita esto en esta máquina
# dedicada y aislada de la instalación.
SUDOERS_FILE="/tmp/ella-sudoers"
echo "$PI_USER ALL=(ALL) NOPASSWD: ALL" > "$SUDOERS_FILE"
sudo chown root:root "$SUDOERS_FILE"
sudo chmod 0440 "$SUDOERS_FILE"
sudo mv "$SUDOERS_FILE" /etc/sudoers.d/ella
echo "✅ Permisos sudoers (NOPASSWD: ALL) configurados."

# ------------------------------------------------------------------------------
# 6. Servicios Systemd
# ------------------------------------------------------------------------------
echo "--- Instalando y Habilitando Servicios Systemd de Usuario ---"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

# Copiar los servicios reemplazando el path canónico %h/ella/repo por la
# ubicación real del repositorio (soporta el clon en ~/ella/repo o en otra ruta).
for svc in panel reproducir sentir-presencia; do
    sed -e "s|%h/ella/repo|$REPO_DIR|g" "$REPO_DIR/pi/services/$svc.service" > "$SYSTEMD_USER_DIR/$svc.service"
done

systemctl --user daemon-reload
systemctl --user enable panel.service
systemctl --user enable sentir-presencia.service
systemctl --user enable reproducir.service

# Asegurar que systemd de usuario inicie en el boot sin requerir login
sudo loginctl enable-linger $PI_USER

# ------------------------------------------------------------------------------
# 7. Access Point (OPCIONAL — no se activa acá)
# ------------------------------------------------------------------------------
echo "--- Access Point (opcional, no se activa automáticamente) ---"
chmod +x "$REPO_DIR/pi/setup_pi_access_point.sh"
chmod +x "$REPO_DIR/pi/revertir_wifi.sh"
echo "El modo Access Point NO se activa durante la instalación."
echo "Para activarlo cuando la instalación esté montada:"
echo "  - Desde el Panel Web: sección 'Access Point'."
echo "  - Por CLI: bash $REPO_DIR/pi/setup_pi_access_point.sh"

# ------------------------------------------------------------------------------
# 8. Watchdog (Opcional pero recomendado para instalaciones)
# ------------------------------------------------------------------------------
echo "--- Habilitando Watchdog (protección contra cuelgues) ---"
# El path de config.txt cambió en Raspberry Pi OS moderno (Bookworm+)
BOOT_CFG="/boot/config.txt"
[ -f /boot/firmware/config.txt ] && BOOT_CFG="/boot/firmware/config.txt"
if ! grep -q "dtparam=watchdog=on" "$BOOT_CFG"; then
    echo "dtparam=watchdog=on" | sudo tee -a "$BOOT_CFG"
fi
sudo apt-get install -y watchdog
sudo systemctl enable watchdog

# ------------------------------------------------------------------------------
echo "========================================================================"
echo "✅ Instalación completada exitosamente."
echo "La Raspberry Pi se va a reiniciar en 10 segundos para aplicar los cambios."
echo ""
echo "Al arrancar:"
echo " 1. La Pi se conectará a tu red WiFi local (el Access Point NO está activado)."
echo " 2. Panel web: http://<IP_DE_LA_PI>:5000 (buscá la IP con: hostname -I)"
echo " 3. Para activar el Access Point 'InstalacionElla': Panel Web → 'Access Point'"
echo "    o por CLI: bash $REPO_DIR/pi/setup_pi_access_point.sh"
echo " 4. Desde el panel podrás gestionar audio, Bluetooth y la hora."
echo "========================================================================"

sleep 10
sudo reboot
