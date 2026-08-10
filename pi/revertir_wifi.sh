#!/bin/bash
# revertir_wifi.sh
# Desactiva el Access Point y restaura la configuración normal de WiFi (DHCP)

set -e

echo "Desactivando Access Point y restaurando WiFi cliente..."

# 1. Detener y deshabilitar servicios del AP
sudo systemctl stop hostapd || true
sudo systemctl disable hostapd || true

sudo systemctl stop dnsmasq || true
sudo systemctl disable dnsmasq || true

# 2. Restaurar dhcpcd.conf
if [ -f /etc/dhcpcd.conf.backup ]; then
    sudo mv /etc/dhcpcd.conf.backup /etc/dhcpcd.conf
else
    # Si no hay backup, quitamos las líneas manualmente
    sudo sed -i '/interface wlan0/d' /etc/dhcpcd.conf
    sudo sed -i '/static ip_address=192.168.4.1\/24/d' /etc/dhcpcd.conf
    sudo sed -i '/nohook wpa_supplicant/d' /etc/dhcpcd.conf
fi

# 3. Restaurar dnsmasq.conf
if [ -f /etc/dnsmasq.conf.orig ]; then
    sudo mv /etc/dnsmasq.conf.orig /etc/dnsmasq.conf
fi

# 4. Reiniciar servicio de red
sudo systemctl restart dhcpcd

echo "====================================================="
echo "✅ Modo Access Point desactivado."
echo "La Raspberry Pi volverá a conectarse a tu red WiFi normal"
echo " (la que tenías configurada antes de correr provision.sh)."
echo "Es recomendable reiniciar con: sudo reboot"
echo "====================================================="
