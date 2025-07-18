# Yumiko – Smart AI Camera for Raspberry Pi
Yumiko is an AI-powered camera app for the Raspberry Pi, combining live camera, style transfer, gallery with navigation, QR code export (tbd), and a fullscreen GUI for touchscreens. Designed for the Pi 4 with Raspberry Pi Camera v3 and a 3.5" LCD touchscreen.

Inspiration:
  - [pi-camera](https://github.com/geerlingguy/pi-camera) by [Jeff Geerling](https://github.com/geerlingguy/)
  - [PIKON Camera](https://www.kevsrobots.com/blog/pikon-camera.html) by [Kevin McAleer](https://www.kevsrobots.com)

### Features
- 📷 Live preview via picamera2
- 🎨 AI Style transfer
- 📁 Gallery mode with touch navigation
- 🧙 Magic wand style overlay with GIF loading animation
- 🔳 QR code for image download
- ⏹️ GPIO button control
- 🖼️ Fullscreen GUI on touchscreen

### Instruction Manual
(tbd)

### Directory Structure
```
yumiko/
├── camera_app/
│   ├── camera.py             ← Main application
│   ├── start_camera.sh       ← Start script (for autostart)
│   ├── server.py             ← Start script (for flask-server)
│   ├── assets/
│   │   ├── icons/            ← Gallery, QR, magic wand icons, GIFs, etc.
│   │   ├── styles/           ← Style image buttons
│   │   └── test/             ← Test images or debug material
│   └── photos/               ← Photos + stylized images
├── requirements.txt          ← Python dependencies
├── .gitignore                ← Ignored files/folders
├── README.md                 ← This file
```

## Requirements
- Verified OpenAI account with sufficient funds available and a valid API key
- Raspberry Pi 4 model B (2 GB RAM or better)
- Raspberry Pi Camera v3 (other camera modules should work too)
- 3.5 inch GPIO LCD touchscreen (Joy-IT model here)
- Raspberry Pi OS (Debian Bookworm 64-bit)
- microSD card
- 12mm push button
- 2x4 2.54 mm female headers
- USB-C powerbank and USB-C cable to power the Pi
- Screws and nuts:
    - M2.5 x 12 mm, 4 pcs, each with nut (for Pi)
    - M2.5 x 4 mm screws, 4 pcs (for front camera attachment)
    - M2 x 5 mm screws, 2 pcs (for bottom plate)
- 3D printed case (STL files in the corresponding directory)
- Wireless USB Adapter (D-Link DWA-131 N300)

## Assembly
(tbd)

## Installation:
### Raspberry Pi OS Installation
Write Raspberry Pi OS 64-bit (Bookworm) to microSD card using Raspberry Pi Imager.

Important: Enable SSH and set username (e.g. "admin") during flashing.

### First login and basic configuration
Connect via SSH:
```
ssh admin@<IP-address>
```

### Set up WiFi (if desired):
sudo raspi-config → System Options → Wireless LAN → enter WiFi credentials

### Enable desktop autologin and configure display:
```
sudo raspi-config
```
→ System Options → Auto Login → Desktop Autologin
→ Display Options → Screen Blanking → No (disable screensaver)
```
sudo reboot
```

### System updates
```
sudo apt update
```
IMPORTANT: Do NOT run apt full-upgrade!
This currently causes issues with the LCD driver and display errors.

### Install and configure display driver
```
sudo rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show
```
### Install display driver:
```
sudo ./LCD35-show
```
This will reboot the pi.
### If needed, rotate display:
```
cd LCD-show
./rotate.sh 180  # or 90 / 270 depending on your preference
```
This will also reboot the pi.

### Enable VNC:
```
sudo raspi-config 
```
→ Interface Options → VNC → Enable

Set screen size in VNC GUI 
(Preferences → Appearance Settings → Defaults → Small recommended)

### Calibrate touchscreen:
```
sudo apt install xinput-calibrator
```
```
sudo nano /etc/X11/xorg.conf.d/99-calibration.conf
```
Insert or adjust following content:
```
Section "InputClass"
    Identifier      "calibration"
    MatchProduct    "ADS7846 Touchscreen"
    Option  "Calibration"   "220 3942 3888 200"
    Option  "SwapAxes"      "1"
    Option  "TransformationMatrix" "0 -1 1 -1 0 1 0 0 1"
EndSection
```
Content may vary depending on your screen and orientation
reboot after adjusting touchscreen
```
sudo reboot
```

### Connect camera
Connect camera according to manufacturer instructions.

### Test command via SSH (with GUI output):
```
export DISPLAY=:0
libcamera-hello -t 0 --autofocus-mode continuous --qt-preview
```

### Python environment and dependencies
Install system packages:
```
sudo apt update
sudo apt install -y python3-pyqt5 python3-opencv libqt5gui5 libqt5widgets5 libqt5core5a libqt5network5 libjpeg-dev libatlas-base-dev
```

### Install Yumiko app
Download source code (e.g. via git clone or scp):
```
git clone https://github.com/Marsbitware/yumiko.git
cd yumiko/camera_app
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Add OpenAI API key to .env:
```
nano ~/camera_app/.env
OPENAI_API_KEY=<your_api_key>
```

### Make script executable:
```
chmod +x ~/camera_app/camera.py
chmod +x ~/camera_app/server.py
chmod +x ~/camera_app/start_camera.sh
```
### Create systemd service:
```
sudo nano /etc/systemd/system/start_camera.service
```
Add content:
```
[Unit]
Description=Start Camera App on boot
After=multi-user.target lgpiod.service
Requires=lgpiod.service

[Service]
ExecStart=/home/admin/camera_app/start_camera.sh
Restart=always
User=admin
Environment=DISPLAY=:0
WorkingDirectory=/home/admin/camera_app

[Install]
WantedBy=multi-user.target
Enable service and reboot:
```
```
sudo systemctl enable start_camera.service
sudo reboot
```

### Killing the Process if necessary
```
pkill -f camera.py
pkill -f server.py
```

### Creating the Hotspot
1. Drivers
1.1 Downloading
```
sudo apt update
sudo apt install git dkms build-essential raspberrypi-kernel-headers
```

```
cd ~
git clone https://github.com/clnhub/rtl8192eu-linux.git
cd rtl8192eu-linux
```

1.2 Editing Makefile
This is how it should look before:
```
CONFIG_PLATFORM_I386_PC = y
CONFIG_PLATFORM_ARM_RPI = n
```

change it to this:
```
CONFIG_PLATFORM_I386_PC = n
CONFIG_PLATFORM_ARM_RPI = y
```
1.3
```
make clean
make
sudo make install
```

2. Configure Hotspot
2.1
```
sudo apt update
sudo apt install hostapd dnsmasq
```

2.2 dedicate IP
go to
```
sudo nano /etc/systemd/network/wlan1.network
```

and put in

```
[Match]
Name=wlan1

[Network]
Address=192.168.50.1/24
#DHCPServer=yes
```

(IP is of course variable, 192.168.50.1/24 is just the one we used)

2.4 activating and starting
```
sudo systemctl enable systemd-networkd
sudo systemctl restart systemd-networkd
```

2.5 überprüfen:
```
sudo systemctl status systemd-networkd
ip a show wlan1
```

following should display:
```
inet 192.168.50.1/24
```

3. Creating the AccessPoint
3.1
go to/create:
```
sudo nano /etc/hostapd/hostapd.conf
```

fill it with :
```
interface=wlan1
driver=nl80211
ssid=YumikoCam
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=yumiko123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
```

3.2 Path to config
```
sudo nano /etc/default/hostapd
```

insert/change 
```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```


3.3 enable service
```
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
```

3.4 Check
```
sudo systemctl status hostapd
```

following should display:
```
Active: active (running)
wlan1: AP-ENABLED
```

4. DHCP with dnsmasq
4.1 create config
```
sudo nano /etc/dnsmasq.conf
```

and insert: 
```
interface=wlan1
dhcp-range=192.168.50.10,192.168.50.100,12h
```
(Again, IP/IP range are variable)

4.2 activating and staring service
```
sudo systemctl enable dnsmasq
sudo systemctl start dnsmasq
```

4.3 Check
```
sudo systemctl status dnsmasq
```

(optional) beides neustartenrstarting both:
```
sudo systemctl restart hostapd
```

and 
```
sudo systemctl restart dnsmasq
```

5. Test if you can see the WLAN on your phone and try connecting to it


additional commands that could be helpful:
stopping the services:
```
sudo systemctl stop hostapd
```

and 
```
sudo systemctl stop dnsmasq
```

starting the services:
```
sudo systemctl start hostapd
```

and
```
sudo systemctl start dnsmasq
```

### Additional: Creating QR Code for easy access to the WLAN


### Additional notes
Gallery and style assets are located in ~/camera_app/assets/
Photos and stylized images are saved in ~/camera_app/photos/

### Third-Party Assets
Icons used in this project are mostly licensed under the MIT License.  
Source and attribution details:
- [Icon: Arrow](https://www.iconfinder.com/icons/211607/right_arrow_icon)
- [Icon: Magic Wand](https://www.iconfinder.com/icons/9025834/magic_wand_icon)
- [Icon: QR Code](https://www.iconfinder.com/icons/4243314/ux_code_app_qr_icon)
- [Icon: Galery](https://www.iconfinder.com/icons/4706692/camera_equipment_gallery_photography_picture_icon)
- [Icon: Trashcan](https://www.iconfinder.com/icons/8664938/trash_can_delete_remove_icon)

