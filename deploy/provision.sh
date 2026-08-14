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

# rpi-connect (Raspberry Pi Connect) se congela: su postinst reinicia el
# servicio y puede cortar la sesión a mitad de la instalación. Reversible
# con: sudo apt-mark unhold rpi-connect rpi-connect-lite
sudo apt-mark hold rpi-connect rpi-connect-lite 2>/dev/null || true
sudo apt-get update

echo "--- Instalando dependencias ---"
# sox, libsox-fmt-all: para el motor de audio
# network-manager: gestión de red (el Access Point se arma con nmcli)
# pipewire-pulse, wireplumber, libspa-0.2-bluetooth: salida por parlante
#   Bluetooth (compatible PulseAudio, sin dependencias X11)
# bluez: emparejamiento Bluetooth (bluetoothctl)
# python3-venv, pip, git: para el entorno
sudo apt-get install -y python3-venv python3-pip git sox libsox-fmt-all alsa-utils curl network-manager bluez pipewire-pulse wireplumber libspa-0.2-bluetooth

# Asegurar pertenencia al grupo audio (para sonido)
sudo usermod -a -G audio "$PI_USER"

# ------------------------------------------------------------------------------
# 1.4 PipeWire headless (A2DP Bluetooth sin sesión gráfica)
# ------------------------------------------------------------------------------
# El monitor bluez de WirePlumber por defecto solo expone los dispositivos
# Bluetooth en el "seat activo" de logind. En esta instalación headless
# (SSH, sin sesión gráfica) no hay seat activo, así que el perfil A2DP nunca
# se registra y 'bluetoothctl connect' falla con
# "br-connection-profile-unavailable" (y wpctl status no muestra la tarjeta).
# Desactivamos el seat-monitoring para que el A2DP esté siempre disponible.
WIREPLUMBER_CONF_DIR="$HOME/.config/wireplumber/wireplumber.conf.d"
mkdir -p "$WIREPLUMBER_CONF_DIR"
if ! grep -q "seat-monitoring" "$WIREPLUMBER_CONF_DIR/51-disable-seat-monitoring.conf" 2>/dev/null; then
    cat > "$WIREPLUMBER_CONF_DIR/51-disable-seat-monitoring.conf" <<'EOF'
wireplumber.profiles = {
  main = {
    monitor.bluez.seat-monitoring = disabled
  }
}
EOF
fi
# Aplicar ya si WirePlumber está corriendo (si no, aplica tras el reboot).
systemctl --user restart wireplumber 2>/dev/null || true

# ------------------------------------------------------------------------------
# 1.5 Bluetooth (operación desatendida)
# ------------------------------------------------------------------------------
echo "--- Configurando Bluetooth (desbloqueo automático) ---"
# El adaptador Bluetooth puede quedar bloqueado por rfkill tras un arranque
# ("Soft blocked: yes"), lo que hace fallar el escaneo y la reconexión del
# parlante. Aseguramos el desbloqueo en cada boot:
#   - Regla udev que fuerza soft=0 al aparecer el dispositivo rfkill
# NOTA: NO hay servicio ni AutoEnable que enciendan el adaptador en el boot.
# Mandar 'power on' o que bluetoothd inicie el adaptador apenas se registra
# hci0 interfiere con el handshake de firmware del controlador por UART y lo
# deja atorado ('command 0x0c14 tx timeout'). El motor de audio espera a que
# hci0 esté registrado y recién entonces enciende y conecta el parlante.
sudo systemctl enable --now bluetooth || true

# Desbloquear y encender YA (sin esperar el próximo boot)
sudo rfkill unblock bluetooth
sudo bluetoothctl power on >/dev/null 2>&1 || true

# ------------------------------------------------------------------------------
# 2. Configuración de Directorios y Clonado
# ------------------------------------------------------------------------------
echo "--- Configurando estructura de directorios ---"
# Los clips de audio viven en el repo (audio/), commiteados. No hace falta
# crear directorios de audio fuera del repositorio.

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
# 3. Configuraciones Base y Credenciales
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
    echo "--- Generando credenciales del Panel Web ---"
    PANEL_USER="ella"
    PANEL_PASS=$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 12)
    cat <<EOF > "$REPO_DIR/pi/panel/.env"
PANEL_USER=$PANEL_USER
PANEL_PASS=$PANEL_PASS
EOF
    CREDS_FILE="$BASE_DIR/panel_credenciales.txt"
    printf 'PANEL_USER=%s\nPANEL_PASS=%s\n' "$PANEL_USER" "$PANEL_PASS" > "$CREDS_FILE"
    chmod 600 "$CREDS_FILE"
    echo "✅ Credenciales del panel web generadas."
    echo "   Usuario:     $PANEL_USER"
    echo "   Contraseña:  $PANEL_PASS"
    echo "   📄 Guardadas en: $CREDS_FILE (por si las olvidás)"
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

# Regla udev: desbloquear por software el adaptador al aparecer rfkill
sudo cp "$REPO_DIR/deploy/99-bluetooth-unblock.rules" /etc/udev/rules.d/99-bluetooth-unblock.rules
sudo chown root:root /etc/udev/rules.d/99-bluetooth-unblock.rules
sudo chmod 0644 /etc/udev/rules.d/99-bluetooth-unblock.rules

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

echo ""
echo "🔐 Credenciales del Panel Web:"
PANEL_USER=$(grep '^PANEL_USER=' "$REPO_DIR/pi/panel/.env" | cut -d= -f2- || true)
PANEL_PASS=$(grep '^PANEL_PASS=' "$REPO_DIR/pi/panel/.env" | cut -d= -f2- || true)
echo "   Usuario:     $PANEL_USER"
echo "   Contraseña:  $PANEL_PASS"
echo "   📄 Si las olvidás, están en: $BASE_DIR/panel_credenciales.txt"
echo ""

sleep 10
sudo reboot
