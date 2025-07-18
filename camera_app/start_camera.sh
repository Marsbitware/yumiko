nano ~/camera_app/start_camera.sh


#!/bin/bash
# activate virtual environment
source ~/venv/bin/activate
#Hotspot Dienste aktivieren
echo "Starte Hotspot-Dienste..."
sudo systemctl start hostapd
sudo systemctl start dnsmasq
echo "Hotspot ist aktiv."

# ste the right display
export DISPLAY=:0
# execute Python-Script
python3 ~/camera_app/camera.py &
# start Pyhton Server 
python3 ~/camera_app/server.py
