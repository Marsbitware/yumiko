#!/bin/bash

source ~/venv/bin/activate

export DISPLAY=:0

echo "waiting for wlan0..."
while ! ip link show wlan0 | grep -q "state UP"; do
    sleep 1
done
echo "wlan0 ist active."

echo "requesting IP..."
sudo dhclient wlan0

echo "starting dnsmasq und hostapd..."
sudo systemctl stop dnsmasq
sudo systemctl stop hostapd
sudo systemctl start dnsmasq
sudo systemctl start hostapd

sleep 2
sudo dhclient wlan0

echo "starting camera.py..."
python3 ~/camera_app/camera.py &

echo "starting server.py..."
python3 ~/camera_app/server.py
