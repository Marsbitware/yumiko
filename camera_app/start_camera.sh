#Den nachfolgenden Code in die Datei start_camera.sh einfügen
nano ~/camera_app/start_camera.sh


#!/bin/bash
# Virtuelle Umgebung aktivieren
source ~/venv/bin/activate
# Korrektes Display setzen
export DISPLAY=:0
# Python-Skript ausführen
python3 ~/camera_app/camera.py