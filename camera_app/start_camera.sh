#!/bin/bash

# Virtuelle Umgebung aktivieren
source ~/venv/bin/activate

# Korrektes Display setzen
export DISPLAY=:0

# Warten bis wlan0 verfügbar ist
echo "Warte auf wlan0..."
while ! ip link show wlan0 | grep -q "state UP"; do
    sleep 1
done
echo "wlan0 ist aktiv."

# IP-Adresse manuell beziehen (vorher, damit Dienste sie nutzen können)
echo "Fordere IP-Adresse an..."
sudo dhclient wlan0

# Hotspotdienste starten (ggf. vorher stoppen, um sauber zu starten)
echo "Starte dnsmasq und hostapd..."
sudo systemctl stop dnsmasq
sudo systemctl stop hostapd
sudo systemctl start dnsmasq
sudo systemctl start hostapd

# Nochmalige IP-Anforderung, falls nötig
sleep 2
sudo dhclient wlan0

# Python-Skripte starten
echo "Starte camera.py..."
python3 ~/camera_app/camera.py &

echo "Starte server.py..."
python3 ~/camera_app/server.py
