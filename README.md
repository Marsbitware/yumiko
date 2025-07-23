# Yumiko – Smart AI Camera for Raspberry Pi

Yumiko is an AI-powered camera app for the Raspberry Pi, featuring live preview, AI style transfer, gallery navigation, QR code export, and a fullscreen GUI for touchscreens.  
Designed for Pi 4 with Raspberry Pi Camera v3 and a 3.5" LCD touchscreen.

---

## Features

- 📷 Live camera preview (picamera2)
- 🎨 AI style transfer (OpenAI API)
- 🖼️ Gallery mode with touch navigation
- 🧙 Style overlay with GIF loading animation
- 🔳 QR code for image download
- ⏹️ GPIO button control
- 🖥️ Fullscreen GUI for touchscreens

---

## Requirements

- Raspberry Pi 4 Model B (2GB RAM+)
- Raspberry Pi Camera v3 (other modules may work)
- 3.5" GPIO LCD touchscreen (in our case: Joy-IT)
- Raspberry Pi OS (Debian Bookworm 64-bit)
- OpenAI API key (with credits)
- microSD card, USB-C powerbank, push button, headers, screws, 3D-printed case
- Wireless USB Adapter (in our case: D-Link DWA-131 N300)

---

## Quick Installation

### 1. Flash Raspberry Pi OS

- Use Raspberry Pi Imager to write Raspberry Pi OS 64-bit (Bookworm) to your microSD card.
- Enable SSH and set a username (e.g. `admin`) during flashing.

### 2. First Boot & Basic Setup

```sh
# Connect via SSH
ssh admin@<IP-address>

# Update system and install dependencies
sudo apt update
sudo apt install -y python3-pyqt5 python3-opencv libqt5gui5 libqt5widgets5 libqt5core5a libqt5network5 \
    libjpeg-dev libatlas-base-dev git dkms build-essential raspberrypi-kernel-headers hostapd dnsmasq \
    xinput-calibrator

# (Optional) Enable VNC
sudo raspi-config  # Interface Options → VNC → Enable
```

### 3. Display Driver

```sh
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show
sudo ./LCD35-show
# (Reboots automatically)
```
- To rotate display: `./rotate.sh 180` (or 90/270)

### 4. Touchscreen Calibration

```sh
sudo nano /etc/X11/xorg.conf.d/99-calibration.conf
```
Insert:
```
Section "InputClass"
    Identifier      "calibration"
    MatchProduct    "ADS7846 Touchscreen"
    Option  "Calibration"   "220 3942 3888 200"
    Option  "SwapAxes"      "1"
    Option  "TransformationMatrix" "0 -1 1 -1 0 1 0 0 1"
EndSection
```
- Adjust values as needed, then reboot: `sudo reboot`

### 5. Camera Setup

- Connect the camera as per manufacturer instructions.
- Test with:
```sh
export DISPLAY=:0
libcamera-hello -t 0 --autofocus-mode continuous --qt-preview
```

### 6. Clone & Install Yumiko

```sh
git clone https://github.com/Marsbitware/yumiko.git
cd yumiko/camera_app
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Configure OpenAI API Key

```sh
nano ~/camera_app/.env
# Add:
OPENAI_API_KEY=<your_api_key>
```

### 8. Make Scripts Executable

```sh
chmod +x ~/camera_app/camera.py ~/camera_app/server.py ~/camera_app/start_camera.sh
```

### 9. Autostart with systemd

```sh
sudo nano /etc/systemd/system/start_camera.service
```
Insert:
```
[Unit]
Description=Start Camera App on boot
After=multi-user.target
[Service]
ExecStart=/home/admin/camera_app/start_camera.sh
Restart=always
User=admin
Environment=DISPLAY=:0
WorkingDirectory=/home/admin/camera_app
[Install]
WantedBy=multi-user.target
```
Then:
```sh
sudo systemctl enable start_camera.service
sudo reboot
```

---

## Hotspot Setup (Optional)

### 1. Install WiFi Driver

```sh
git clone https://github.com/clnhub/rtl8192eu-linux.git
cd rtl8192eu-linux
# Edit Makefile: set CONFIG_PLATFORM_ARM_RPI = y
make clean
make
sudo make install
```

### 2. Configure Network

```sh
sudo tee /etc/systemd/network/wlan1.network <<EOF
[Match]
Name=wlan1
[Network]
Address=192.168.50.1/24
EOF

sudo systemctl enable systemd-networkd
sudo systemctl restart systemd-networkd
```

### 3. Configure Access Point

```sh
sudo tee /etc/hostapd/hostapd.conf <<EOF
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
EOF

sudo sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
```

### 4. DHCP with dnsmasq

```sh
sudo tee /etc/dnsmasq.conf <<EOF
interface=wlan1
dhcp-range=192.168.50.10,192.168.50.100,12h
EOF

sudo systemctl enable dnsmasq
sudo systemctl start dnsmasq
```

### 5. WiFi Management

```sh
sudo systemctl enable wpa_supplicant@wlan0
sudo systemctl start wpa_supplicant@wlan0
sudo systemctl stop wpa_supplicant@wlan1
sudo systemctl disable wpa_supplicant@wlan1
```

```sh
sudo nano /etc/NetworkManager/conf.d/unmanaged.conf
```
and insert:
```
[keyfile]
unmanaged-devices=interface-name:wlan0
```

Add WiFi
```
sudo nano /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
```

and insert:
```
country=DE
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="SSID"
    psk="PWD..."
    key_mgmt=WPA-PSK
}
```

Restart everything
```
sudo systemctl restart NetworkManager
sudo systemctl enable --now wpa_supplicant@wlan0
sudo systemctl restart dnsmasq
sudo systemctl restart hostapd
```


### Additional: Creating QR Code for easy access to the WiFi


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
