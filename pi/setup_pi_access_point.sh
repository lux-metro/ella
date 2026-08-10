#!/bin/bash
# setup_pi_access_point.sh
# Convierte la Raspberry Pi en su propio punto de acceso WiFi ("InstalacionElla").
# La IP fija de la Pi será 192.168.4.1

set -e

# Leer contraseña de credenciales_wifi.txt
WIFI_CRED_FILE="$(dirname "$0")/../credenciales_wifi.txt"
if [ ! -f "$WIFI_CRED_FILE" ]; then
    echo "Error: No se encontró el archivo $WIFI_CRED_FILE"
    echo "Por favor, crea el archivo con la contraseña del WiFi (ej: echo 'MiClaveSecreta' > credenciales_wifi.txt)"
    exit 1
fi

WIFI_PASSWORD=$(cat "$WIFI_CRED_FILE")

echo "Configurando la Raspberry Pi como Access Point (InstalacionElla)..."

# Instalar dependencias necesarias (hostapd y dnsmasq)
sudo apt-get update
sudo apt-get install -y hostapd dnsmasq

# Detener los servicios mientras los configuramos
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

# Configurar IP estática en dhcpcd
sudo cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup
if ! grep -q "interface wlan0" /etc/dhcpcd.conf; then
    sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOF
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF
fi

# Reiniciar dhcpcd
sudo systemctl restart dhcpcd

# Configurar hostapd (Access Point)
sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan0
driver=nl80211
ssid=InstalacionElla
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$WIFI_PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Apuntar hostapd al archivo de configuración
sudo sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|g' /etc/default/hostapd

# Configurar dnsmasq (DHCP Server)
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Iniciar y habilitar servicios
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd

sudo systemctl enable dnsmasq
sudo systemctl start dnsmasq

echo "============================================="
echo "Access Point configurado con éxito."
echo "Red: InstalacionElla"
echo "IP de la Raspberry Pi: 192.168.4.1"
echo "============================================="
