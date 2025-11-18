import os
import sys
import cv2
import time
import shutil
import base64
import requests
import random
import io
import qrcode
import RPi.GPIO as GPIO
from dotenv import load_dotenv
from PIL import Image
from picamera2 import Picamera2
from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy,
    QStackedLayout, QToolButton, QGridLayout
)
from PyQt5.QtCore import (
    Qt, QSize, QRect, QTimer, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QObject
)
from PyQt5.QtGui import QImage, QPixmap, QIcon, QTransform, QMovie
from openai import OpenAI
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from functools import partial

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PHOTOS_DIR = os.path.join(BASE_DIR, "photos")
STYLE_DIR = os.path.join(ASSETS_DIR, "styles")

# Ensure directories exist
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(STYLE_DIR, exist_ok=True)

# Icons
ICON_PATHS = {
    "gallery": os.path.join(ASSETS_DIR, "icons", "gallery.png"),
    "arrow": os.path.join(ASSETS_DIR, "icons", "arrow.png"),
    "qr": os.path.join(ASSETS_DIR, "icons", "qr_code.png"),
    "wand": os.path.join(ASSETS_DIR, "icons", "magic_wand.png"),
    "trash": os.path.join(ASSETS_DIR, "icons", "trash_can.png"),
}

# OpenAI setup
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

STYLE_PROMPTS = {
        "zombies": (
            "Transform this image into a post-apocalyptic zombie scene. Turn people into zombies or survivors with torn clothing, decayed skin, "
            "and place them in a ruined, post-apocaliptic world with destruction and lurking undead. Make it realistic but don't make the picture too dark"
        ),

        "lego": (
            "Transform this image so that all people, objects, and surroundings appear like the colorful, modular LEGO style. "
            "Use plastic textures, blocky shapes, and bright, toy-like colors typical of a LEGO world."
        ),

        "simpsons": (
            "Transform this image into a cartoon universe like that of The Simpsons. Use flat, saturated colors, thick black outlines, "
            "and exaggerated facial features. Convert characters into yellow-skinned, 2D cartoon figures."
        ),

        "studio_ghibli": (
            "Turn this photo into a Ghibli scene, preserving the original features but transforming the people and the landscape into "
            "classic Ghibli Style."
        ),

        "cyberpunk": (
            "Transform this image into a futuristic cyberpunk scene. Use neon lights, dark cityscapes, holograms, and high-tech fashion. "
            "Incorporate cybernetic enhancements and a gritty, dystopian atmosphere."
        ),

        "renaissance": (
            "Transform this image so that the people and their clothes, objects, and background are reimagined in the style of a Renaissance painting. "
            "Use soft light, realistic proportions, and detailed shading to mimic the classical atmosphere."
        ),

        "mafiosi": (
            "Transform this image into a 1920s–1940s mafia scene, keeping the people and composition intact. Dress everyone in period-accurate suits, "
            "fedoras, and overcoats, and add subtle noir tones and era-specific ambiance. Don't make the picture too dark though. "
        ),

        "oval_office": (
            "Place this scene in the Oval Office while preserving the people and their facial features. Add presidential elements, formal suits, U.S. flags, "
            ", and iconic White House / Oval Office styling."
        ),

        "roman_empire": (
            "Transform this image into the world of Ancient Rome. Dress people Roman military gear, while preserving facial features. "
            "Include things like marble columns, grand statues, or just classical Roman architecture in general. "
        ),

        "samurai": (
            "Transform this image into the world of feudal Japan. Dress people in traditional samurai armor while preserving original features like face or pose. "
            " Include things like katana swords, temples, or misty mountain landscapes with a historical Japanese aesthetic. Also add a little cherry blossom. "
        ),

        "manga_bw": (
            "Transform this image into a black-and-white manga drawing. Use clean ink lines, strong contrast, cross-hatching, while preserving original features, "
            "like face or pose of the people. Focus on dynamic composition and emotional intensity typical of Japanese manga art."
        ),

        "van_gogh": (
            "Transform this image so that people, objects, and the background resemble the style of Vincent van Gogh. Use thick brush strokes, "
            "vibrant contrasting colors, and swirling, expressive textures to mimic his iconic post-impressionist paintings."
        ),

        "medieval": (
            "Transform this image into a piece of naive medieval art. Preserve the original faces and poses, but depict everything in the style "
            "of medieval marginalia and early bestiary illustrations: flat perspective, awkward proportions, humorous misinterpretations of anatomy, "
            "and richly colored illuminated manuscript details with gold-leaf accents on parchment."
        ),

        "horror": (
            "Transform this photo into a dark, fear-inducing horror setting. Retain the recognizable subjects and arrangement, but surround them with eerie shadows, "
            "unsettling atmosphere, and a well-known horror villain. The people are supposed to look afraid but try to preserve facial features and of the people. "
            " Don't make it too dark though. It should still be recognizable. You are allowed to change the pose of the people to make them look scared though. "
        ),

        "formula_1": (
            "Transform this image into a Formula 1 racing theme. Dress people in professional racing suits and helmets, while keeping their facial features (-> open helmets or "
            " helmets being carried) and / or poses. Insert F-1 themed objects like F1-cars, a racetrack, checkered flags, while (more or less) keeping the original composition. "
        ),
    
        "steampunk": (
            "Recreate this image in a detailed steampunk universe. Maintain the people and composition, but dress them in Victorian-inspired outfits enhanced with for example gears, pipes, "
            " goggles, and steam-powered devices. Don't make the picture too dark. "
        ),

        "lord_of_the_rings": (
            "Recreate this image in a high-fantasy medieval world. Keep faces and poses recognizable, but restyle everyone as elegant forest beings, sturdy mountain folk, fierce warrior tribes, "
            " or noble ranger-like characters in detailed fantasy attire. Include a distinctive fantasy landmark—such as a towering fortress, a mystical valley city, or a distant volcanic "
            " stronghold—and surround them with bright, vibrant landscapes. "
        ),

        "minecraft": (
            "Transform this image into the pixelated, blocky world of Minecraft. Convert people, objects, and background into cubic shapes with simple textures. "
            "Use bright, low-resolution graphics and game-like environments with trees, mountains, or structures made from blocks."
        ),

        "donald_duck": (
            "Transform this image into a cartoon world like Donald Duck. Convert people into anthropomorphic, expressive characters with beak-like faces, "
            "cartoon eyes, and colorful, animated surroundings inspired by classic Disney comic and TV styles."
        ),

        "cavemen": (
            "Turn this image into a prehistoric cave tableau. Maintain the original people’s features and layout, dress them in fur or leather outfits, "
            " scatter stone-age tools around, and use a bright, atmospheric cave interior rather than dark shadows. "
        ),

        "star_wars": (
            "Convert this photo into a cinematic sci-fi fantasy scene. Preserve facial features and composition, style people with futuristic robes, armor, "
            " or alien traits, and include glowing energy blades, robotic assistants, starships, and epic galactic environments. "
        )
}


BUTTON_STYLE = """
    QPushButton, QToolButton {
        background-color: rgba(255, 255, 255, 40);
        border: 2px solid black;
        border-radius: 6px;
    }
    QPushButton:hover, QToolButton:hover {
        background-color: rgba(255, 255, 255, 60);
    }
    QPushButton:pressed, QToolButton:pressed {
        background-color: rgba(255, 255, 255, 100);
    }
"""

class WorkerSignals(QObject):
    finished = pyqtSignal(bytes, str, str)

class StyleTransferTask(QRunnable):
    def __init__(self, image_path, style_name):
        super().__init__()
        self.image_path = image_path
        self.style_name = style_name
        self.signals = WorkerSignals()

    def run(self):
        try:
            with open(self.image_path, "rb") as image_file:
                full_prompt = f"Transform this image into the style of {STYLE_PROMPTS.get(self.style_name, '')}"
                response = client.images.edit(
                    model="gpt-image-1",
                    image=[image_file],
                    prompt=full_prompt,
                    n=1,
                    quality="high",
                    size="1024x1024",
                )
                data = response.data[0].b64_json
                if not data:
                    self.signals.finished.emit(None, "No image data received", self.style_name)
                    return
                self.signals.finished.emit(base64.b64decode(data), None, self.style_name)
        except Exception as e:
            self.signals.finished.emit(None, str(e), self.style_name)

FLASK_SERVER = "http://192.168.50.1:5000"

class CameraApp(QWidget):
    gpio_button_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.styles_per_page = 6
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(0, 0, 480, 320)
        self.setWindowTitle("Smart Camera")
        self.showFullScreen()
        
        self.loading_overlay = None
        self.current_mode = "camera"
        self.image_paths = []
        self.current_index = 0

        self.setup_ui()
        self.setup_camera()
        self.setup_gpio()

    def setup_ui(self):
        self.stack = QStackedLayout()
        self.camera_widget = QWidget()
        self.gallery_widget = QWidget()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setStyleSheet("background-color: black;")

        camera_layout = QVBoxLayout(self.camera_widget)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        camera_layout.addWidget(self.label)

        self.stack.addWidget(self.camera_widget)
        self.stack.addWidget(self.gallery_widget)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.stack)

        self.gallery_button = QPushButton()
        self.gallery_button.setIcon(QIcon(QPixmap(ICON_PATHS["gallery"]).transformed(QTransform().rotate(-90))))
        self.gallery_button.setIconSize(QSize(96, 96))
        self.gallery_button.setFixedSize(120, 120)
        self.gallery_button.setStyleSheet(BUTTON_STYLE)
        self.gallery_button.move(0, 200)
        self.gallery_button.setParent(self.camera_widget)
        self.gallery_button.clicked.connect(self.open_gallery)

        self.loading_label = QLabel(self, alignment=Qt.AlignCenter)
        self.loading_label.setGeometry(0, 0, 480, 320)
        self.loading_label.setStyleSheet("background-color: rgba(0, 0, 0, 180); color: white; font-size: 18px;")
        self.loading_label.setText("Applying style... Please wait.")
        self.loading_label.hide()

    def setup_camera(self):
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (480, 320)}))
        self.picam2.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_preview)
        self.timer.start(30)

    def setup_gpio(self):
        self.gpio_button_pressed.connect(self.handle_back_or_photo)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(21, GPIO.FALLING, callback=self.handle_gpio_press, bouncetime=300)

    def handle_gpio_press(self, channel):
        print("[BUTTON] GPIO 21 pressed")
        self.gpio_button_pressed.emit()

    def handle_back_or_photo(self):
        print(f"[BUTTON] Current mode: {self.current_mode}")
        if self.current_mode == "style_overlay":
            self.open_gallery()
        elif self.current_mode == "qr_overlay":
            if hasattr(self, "qr_overlay") and self.qr_overlay is not None:
                self.qr_overlay.deleteLater()
                self.qr_overlay = None
            self.open_gallery()
        elif self.current_mode == "gallery":
            self.return_to_camera()
        elif self.current_mode == "camera":
            self.take_photo()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("[KEY] ESC pressed")
            if self.current_mode in ["gallery", "qr_overlay", "style_overlay"]:
                self.return_to_camera()

    def update_preview(self):
        frame = self.picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape

        # Crop to 3:2 aspect ratio (480x320)
        target_aspect = 480 / 320
        frame_aspect = w / h

        if frame_aspect > target_aspect:
            # Image is too wide, crop left/right
            new_w = int(h * target_aspect)
            x1 = (w - new_w) // 2
            frame = frame[:, x1:x1+new_w]
            w = new_w
        else:
            # Image is too tall, crop top/bottom
            new_h = int(w / target_aspect)
            y1 = (h - new_h) // 2
            frame = frame[y1:y1+new_h, :]
            h = new_h

        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.label.setPixmap(pixmap.scaled(480, 320, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def open_gallery(self):
        print("[INFO] Opening gallery")
        files = [
            os.path.join(PHOTOS_DIR, f)
            for f in os.listdir(PHOTOS_DIR)
            if f.lower().endswith((".jpg", ".png"))
        ]
        self.image_paths = sorted(files, key=os.path.getmtime, reverse=True)
        if self.image_paths:
            self.current_index = 0
            self.show_current_image()
            self.stack.setCurrentWidget(self.gallery_widget)
        self.current_mode = "gallery"

    def return_to_camera(self):
        print("[INFO] Returning to camera mode")
        self.stack.setCurrentWidget(self.camera_widget)
        self.current_mode = "camera"

    def take_photo(self):
        print("[PHOTO] Taking photo")
        self.picam2.stop()
        still_config = self.picam2.create_still_configuration(main={"format": "RGB888", "size": (2028, 1520)})
        self.picam2.configure(still_config)
        self.picam2.start()
        frame = self.picam2.capture_array()

        preview_config = self.picam2.create_preview_configuration(main={"format": "RGB888", "size": (480, 320)})
        self.picam2.stop()
        self.picam2.configure(preview_config)
        self.picam2.start()

        h, w, _ = frame.shape
        crop_size = min(w, h)
        x1 = (w - crop_size) // 2
        y1 = (h - crop_size) // 2
        shift = int(0.10 * crop_size)
        x1 = max(0, x1 - shift)

        cropped = frame[y1:y1 + crop_size, x1:x1 + crop_size]

        filename = f"photo_{int(time.time())}.png"
        filepath = os.path.join(PHOTOS_DIR, filename)
        cv2.imwrite(filepath, cropped)
        print(f"[PHOTO] Saved to: {filepath}")
        self.flash_screen()

    def flash_screen(self):
        flash = QLabel(self.camera_widget)
        flash.setStyleSheet("background-color: white;")
        flash.setGeometry(0, 0, 480, 320)
        flash.show()
        flash.raise_()
        QTimer.singleShot(100, flash.deleteLater)

    def show_current_image(self):
        self.clear_gallery_widget()

        self.gallery_image_label = QLabel(self.gallery_widget)
        self.gallery_image_label.setAlignment(Qt.AlignCenter)
        self.gallery_image_label.setGeometry(0, 0, 480, 320)
        self.gallery_image_label.setStyleSheet("background-color: black;")

        current_path = self.image_paths[self.current_index]
        self.current_image_path = current_path

        pixmap = QPixmap(current_path)
        scaled = pixmap.scaled(480, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.gallery_image_label.setPixmap(scaled)
        self.gallery_image_label.show()

        self.create_overlay_buttons()

    def clear_gallery_widget(self):
        for child in self.gallery_widget.findChildren(QWidget):
            child.setParent(None)
            child.deleteLater()

        layout = self.gallery_widget.layout()
        if layout is not None:
            self.clear_nested_layout(layout)

    def clear_nested_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_nested_layout(item.layout())
        layout.deleteLater()

    def create_overlay_buttons(self):
        def make_button(icon, pos, callback):
            btn = QToolButton(self.gallery_widget)
            btn.setIcon(QIcon(icon))
            btn.setIconSize(QSize(64, 64))
            btn.setFixedSize(72, 72)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.move(*pos)
            btn.clicked.connect(callback)
            btn.raise_()
            btn.show()

        # ← Left arrow
        left_icon = QPixmap(ICON_PATHS["arrow"]).transformed(QTransform().scale(-1, 1))
        btn_left = QToolButton(self.gallery_widget)
        btn_left.setIcon(QIcon(left_icon))
        btn_left.setIconSize(QSize(96, 96))
        btn_left.setFixedSize(120, 120)
        btn_left.setStyleSheet(BUTTON_STYLE)
        btn_left.move(0, 100)
        btn_left.clicked.connect(self.show_previous_image)
        btn_left.raise_()
        btn_left.show()

        # → Right arrow
        btn_right = QToolButton(self.gallery_widget)
        btn_right.setIcon(QIcon(ICON_PATHS["arrow"]))
        btn_right.setIconSize(QSize(96, 96))
        btn_right.setFixedSize(120, 120)
        btn_right.setStyleSheet(BUTTON_STYLE)
        btn_right.move(480 - 120, 100)
        btn_right.clicked.connect(self.show_next_image)
        btn_right.raise_()
        btn_right.show()

        make_button(ICON_PATHS["qr"], (5, 5), self.show_qr_overlay)
        make_button(ICON_PATHS["wand"], (403, 5), self.show_style_overlay)
        make_button(ICON_PATHS["trash"], (403, 243), self.delete_current_image)

    def show_next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.show_current_image()

    def show_previous_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()

    def show_qr_overlay(self):
        if not hasattr(self, "current_image_path") or not self.current_image_path:
            print("[QR] No current image found.")
            return

        if hasattr(self, "qr_overlay") and self.qr_overlay is not None:
            self.qr_overlay.deleteLater()
            self.qr_overlay = None

        filename = os.path.basename(self.current_image_path)
        qr_url = f"{FLASK_SERVER}/view/{filename}"

        print(f"[QR] Generating QR for: {qr_url}")
        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qt_img = QImage.fromData(buf.getvalue())

        # Create Overlay
        overlay = QWidget(self)
        overlay.setGeometry(0, 0, self.width(), self.height())
        overlay.setStyleSheet("background-color: rgba(0,0,0,180);")
        overlay.setAttribute(Qt.WA_DeleteOnClose)
        overlay.raise_()

        # Show QR-Code
        qr_label = QLabel(overlay)
        qr_pixmap = QPixmap.fromImage(qt_img).scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        qr_label.setPixmap(qr_pixmap)
        qr_label.setGeometry((overlay.width() - 240) // 2, 60, 240, 240)
        qr_label.show()

        # Display Info
        txt = QLabel("📱 Scan the QR code\nto view & download the photo", overlay)
        txt.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        txt.setAlignment(Qt.AlignCenter)
        txt.setGeometry((overlay.width() - 300) // 2, 320, 300, 40)
        txt.show()

        overlay.show()

        self.qr_overlay = overlay 
        self.current_mode = "qr_overlay"

    def show_style_overlay(self):
        print("[AI] Showing style overlay")
        if self.current_mode != "style_overlay":
            self.current_style_page = 0

        if hasattr(self, "style_overlay") and self.style_overlay is not None:
            try:
                self.style_overlay.deleteLater()
            except RuntimeError:
                pass
            self.style_overlay = None

        self.clear_gallery_widget()

        overlay = QWidget()
        overlay.setParent(self.gallery_widget)
        overlay.setGeometry(0, 0, 480, 320)
        overlay.setStyleSheet("background-color: black;")
        overlay.raise_()

        all_styles = [
            ("random", "random"),
            ("zombies", "zombies"),
            ("lego", "lego"),
            ("simpsons", "simpsons"),
            ("studio_ghibli", "studio_ghibli"),
            ("cyberpunk", "cyberpunk"),
            ("renaissance", "renaissance"),
            ("mafiosi", "mafiosi"),
            ("oval_office", "oval_office"),
            ("roman_empire", "roman_empire"),
            ("samurai", "samurai"),
            ("manga_bw", "manga_bw"),
            ("van_gogh", "van_gogh"),
            ("medieval", "medieval"),
            ("horror", "horror"),
            ("formula_1", "formula_1"),
            ("steampunk", "steampunk"),
            ("lord_of_the_rings", "lord_of_the_rings"),
            ("minecraft", "minecraft"),
            ("donald_duck", "donald_duck"),
            ("cavemen", "cavemen"),
            ("star_wars", "star_wars"),
        ]

        available_styles = []
        for style_name, file_base in all_styles:
            for ext in [".jpg", ".png"]:
                path = os.path.join(STYLE_DIR, file_base + ext)
                if os.path.exists(path):
                    available_styles.append((style_name, file_base, path))
                    break

        self.style_overlay = overlay
        self.current_mode = "style_overlay"

        self.styles_per_page = 6
        start = self.current_style_page * self.styles_per_page
        end = start + self.styles_per_page
        styles = available_styles[start:end]

        positions = [
            (0, 0), (160, 0), (320, 0),
            (0, 160), (160, 160), (320, 160)
        ]

        for idx, (style, file_base, path) in enumerate(styles):
            btn = QPushButton(overlay)
            btn.setGeometry(positions[idx][0] + 1, positions[idx][1] + 1, 158, 158)
            btn.setIconSize(QSize(156, 156))
            btn.setStyleSheet(BUTTON_STYLE)

            pixmap = QPixmap(path)
            cropped = self.crop_and_scale_pixmap(pixmap, QSize(156, 156))
            btn.setIcon(QIcon(cropped))

            if style == "random":
                btn.clicked.connect(self.apply_random_style)
            else:
                btn.clicked.connect(partial(self.apply_style, style))
            btn.show()

        max_pages = (len(available_styles) - 1) // self.styles_per_page

        # ← Left arrow
        if self.current_style_page > 0:
            left_icon = QPixmap(ICON_PATHS["arrow"]).transformed(QTransform().scale(-1, 1))
            btn_prev = QToolButton(overlay)
            btn_prev.setIcon(QIcon(left_icon))
            btn_prev.setIconSize(QSize(96, 96))
            btn_prev.setFixedSize(120, 120)
            btn_prev.setStyleSheet(BUTTON_STYLE)
            btn_prev.move(0, 100)
            btn_prev.clicked.connect(self.prev_style_page)
            btn_prev.raise_()
            btn_prev.show()

        # → Right arrow
        if self.current_style_page < max_pages:
            right_icon = QPixmap(ICON_PATHS["arrow"])
            btn_next = QToolButton(overlay)
            btn_next.setIcon(QIcon(right_icon))
            btn_next.setIconSize(QSize(96, 96))
            btn_next.setFixedSize(120, 120)
            btn_next.setStyleSheet(BUTTON_STYLE)
            btn_next.move(480 - 120, 100)
            btn_next.clicked.connect(self.next_style_page)
            btn_next.raise_()
            btn_next.show()

        overlay.show()

    def apply_random_style(self):
        style_names = list(STYLE_PROMPTS.keys())
        random_style = random.choice(style_names)
        print(f"[STYLE] randomly chosen style: {random_style}")
        self.apply_style(random_style)

    def next_style_page(self):
        self.current_style_page += 1
        self.show_style_overlay()

    def prev_style_page(self):
        self.current_style_page -= 1
        self.show_style_overlay()

    def show_loading_overlay(self):
        if self.loading_overlay:
            self.loading_overlay.deleteLater()

        self.loading_overlay = QWidget(self)
        self.loading_overlay.setGeometry(0, 0, 480, 320)
        self.loading_overlay.setStyleSheet("background-color: white;")
        self.loading_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.loading_gif_label = QLabel(self.loading_overlay)
        self.loading_gif_label.setGeometry(0, 0, 480, 320)
        self.loading_gif_label.setAlignment(Qt.AlignCenter)

        gif_path = os.path.join(ASSETS_DIR, "icons", "sleeping.gif")
        self.loading_movie = QMovie(gif_path)
        self.loading_movie.setScaledSize(QSize(480, 320))
        self.loading_gif_label.setMovie(self.loading_movie)
        self.loading_movie.start()

        self.loading_text_label = QLabel("Yumiko is dreaming...", self.loading_overlay)
        self.loading_text_label.setAlignment(Qt.AlignCenter)

        self.loading_text_label.resize(320, 40)
        self.loading_text_label.move(80, 270)

        self.loading_text_label.setStyleSheet(
            "background-color: rgba(255, 255, 210, 200);"
            "color: black;"
            "font-size: 18px;"
            "border: 2px solid #444;"
            "border-radius: 12px;"
            "padding: 6px;"
        )

        self.loading_overlay.show()
        self.loading_overlay.raise_()

    def crop_and_scale_pixmap(self, pixmap, target_size):
        src_width, src_height = pixmap.width(), pixmap.height()
        target_width, target_height = target_size.width(), target_size.height()
        src_aspect = src_width / src_height
        target_aspect = target_width / target_height

        if src_aspect > target_aspect:
            new_width = int(src_height * target_aspect)
            x_offset = (src_width - new_width) // 2
            rect = QRect(x_offset, 0, new_width, src_height)
        else:
            new_height = int(src_width / target_aspect)
            y_offset = (src_height - new_height) // 2
            rect = QRect(0, y_offset, src_width, new_height)

        return pixmap.copy(rect).scaled(target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    def apply_style(self, style_name):
        self.show_loading_overlay()
        print(f"[STYLE] Selected style: {style_name}")
        if not hasattr(self, "current_image_path") or not os.path.exists(self.current_image_path):
            print("[ERROR] No current image available.")
            return

        task = StyleTransferTask(self.current_image_path, style_name)
        task.signals.finished.connect(self.handle_style_result)
        QThreadPool.globalInstance().start(task)

    def play_waking_up_and_close(self, on_finished_callback):
        if not self.loading_overlay or not hasattr(self, "loading_gif_label"):
            on_finished_callback()
            return

        gif_path = os.path.join(ASSETS_DIR, "icons", "waking_up.gif")

        self.waking_movie = QMovie(gif_path)
        self.waking_movie.setScaledSize(QSize(480, 320))
        self.loading_gif_label.setMovie(self.waking_movie)

        def on_frame_changed(frame_number):
            if frame_number == self.waking_movie.frameCount() - 1:
                print("[GIF] Waking up finished")
                self.waking_movie.stop()
                self.loading_overlay.hide()
                self.loading_overlay.deleteLater()
                self.loading_overlay = None
                on_finished_callback()

        self.waking_movie.frameChanged.connect(on_frame_changed)
        self.waking_movie.start()

    @pyqtSlot(bytes, str, str)
    def handle_style_result(self, image_bytes, error, style_name):
        if error:
            print(f"[ERROR] Style transfer failed: {error}")
            self.loading_label.setText("Style transfer failed")
            return

        filename = f"styled_{style_name}_{int(time.time())}.png"
        save_path = os.path.join(PHOTOS_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(image_bytes)

        print(f"[STYLE] Saved styled image to: {save_path}")
        self.current_image_path = save_path
        self.play_waking_up_and_close(lambda: self.open_gallery())

    def delete_current_image(self):
        if not self.image_paths:
            return

        path = self.image_paths[self.current_index]
        try:
            os.remove(path)
            print(f"[DELETE] Image deleted: {path}")
        except Exception as e:
            print(f"[ERROR] Failed to delete image: {e}")
            return

        self.image_paths = [p for p in self.image_paths if p != path]

        if not self.image_paths:
            print("[INFO] No more images — returning to camera")
            self.return_to_camera()
        else:
            self.current_index = min(self.current_index, len(self.image_paths) - 1)
            self.show_current_image()

    def closeEvent(self, event):
        self.picam2.close()
        GPIO.cleanup()
        event.accept()

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec_())
