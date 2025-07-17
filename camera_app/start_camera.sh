nano ~/camera_app/start_camera.sh


#!/bin/bash
# activate virtual environment
source ~/venv/bin/activate
# ste the right display
export DISPLAY=:0
# execute Python-Script
python3 ~/camera_app/camera.py &
# start Pyhton Server 
python3 ~/camera_app/server.py
