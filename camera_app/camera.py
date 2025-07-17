import os
import sys
import cv2
import time
import shutil
import base64
import requests
import io
import qrcode
import RPi.GPIO as GPIO
from dotenv import load_dotenv
from PIL import Image
from picamera2 import Picamera2
from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QSizePolicy,
    QStackedLayout, QToolButton, QGridLayout
)
from PyQt5.QtCore import (
    Qt, QSize, QRect, QTimer, QRunnable, QThreadPool, pyqtSlot, pyqtSignal, QObject
)
from PyQt5.QtGui import QImage, QPixmap, QIcon, QTransform, QMovie
from openai import OpenAI
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PHOTOS_DIR = os.path.join(BASE_DIR, "photos")
STYLE_DIR = os.path.join(ASSETS_DIR, "styles")

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
    "studio_ghibli": (
        "Transform this image so that the people, objects, and landscape appear in the charming and dreamy style "
        "of a Studio Ghibli animation. Use soft colors, painterly textures, and whimsical lighting typical of classic Ghibli scenes."
    ),
    "van_gogh": (
        "Transform this image so that the people and their clothes, objects, and landscape resemble a painting by Vincent van Gogh. "
        "Apply thick brush strokes, swirling textures, and vibrant, contrasting colors to evoke the energy and emotion of his style."
    ),
    "renaissance": (
        "Transform this image so that the people and their clothes, objects, and background are reimagined in the style of a Renaissance painting, "
        "as if painted by Leonardo da Vinci. Use soft light, realistic proportions, and detailed shading to mimic the classical atmosphere."
    ),
    "medieval": (
        "Transform this image so that the scene looks like a medieval piece of art. "
        "Depict the people and their clothes and objects with flat perspective, rich colors, ornate details, and gold-leaf embellishments on parchment."
    ),
    "cyberpunk": (
        "Transform this image into a futuristic cyberpunk scene. Reimagine the people and their clothes, objects, and environment with neon lights, "
        "high-tech elements, rain-soaked streets, glowing signs, and a gritty urban atmosphere."
    ),
    "fantasy": (
        "Transform this image into a dreamy fantasy world filled with surreal elements. Reimagine people and their clothes, creatures, and landscapes "
        "with soft lighting, floating objects, mythical creatures and a magical color palette."
    ),
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

FLASK_SERVER = "http://192.168.178.83:5000"  # ❗ Deine Pi-IP hier eintragen

class CameraApp(QWidget):
    gpio_button_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
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
        camera_layout = QVBoxLayout(self.camera_widget)
        camera_layout.setContentsMargins(0, 0, 0, 0)
        camera_layout.addWidget(self.label)
        QVBoxLayout(self.camera_widget).addWidget(self.label)

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
            self.open_gallery()
        elif self.current_mode == "gallery":
            self.return_to_camera()
        elif self.current_mode == "camera":
            self.take_photo()

    
    def handle_back_or_photo(self):
        print(f"[BUTTON] Current mode: {self.current_mode}")
        if self.current_mode == "style_overlay":
            self.open_gallery()
        elif self.current_mode == "qr_overlay":
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
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.label.setPixmap(pixmap.scaled(self.label.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

    def open_gallery(self):
        print("[INFO] Opening gallery")
        self.image_paths = [
            os.path.join(PHOTOS_DIR, f)
            for f in sorted(os.listdir(PHOTOS_DIR))
            if f.lower().endswith((".jpg", ".png"))
        ]
        if self.image_paths:
            self.current_index = len(self.image_paths) - 1
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
        cx, cy = w // 2, h // 2
        cropped = frame[cy - 512:cy + 512, cx - 512:cx + 512]
        if cropped.shape[0] != 1024 or cropped.shape[1] != 1024:
            cropped = cv2.resize(cropped, (1024, 1024), interpolation=cv2.INTER_AREA)

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
        # Sicherstellen, dass Bild vorhanden ist
        if not hasattr(self, "current_image_path") or not self.current_image_path:
            print("[QR] Kein aktuelles Bild gefunden.")
            return

        filename = os.path.basename(self.current_image_path)
        qr_url = f"{FLASK_SERVER}/view/{filename}"  # QR zeigt auf HTML-Seite mit Downloadbutton

        print(f"[QR] Generiere QR für: {qr_url}")
        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qt_img = QImage.fromData(buf.getvalue())

        # Overlay erstellen
        overlay = QWidget(self)
        overlay.setGeometry(0, 0, self.width(), self.height())
        overlay.setStyleSheet("background-color: rgba(0,0,0,180);")
        overlay.setAttribute(Qt.WA_DeleteOnClose)
        overlay.raise_()

        # QR-Code anzeigen
        qr_label = QLabel(overlay)
        qr_pixmap = QPixmap.fromImage(qt_img).scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        qr_label.setPixmap(qr_pixmap)
        qr_label.setGeometry((overlay.width() - 240) // 2, 60, 240, 240)
        qr_label.show()

        # Infotext darunter
        txt = QLabel("📱 Scan den QR-Code\num das Foto anzuzeigen & herunterzuladen", overlay)
        txt.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        txt.setAlignment(Qt.AlignCenter)
        txt.setGeometry((overlay.width() - 300) // 2, 320, 300, 40)
        txt.show()

        overlay.show()

        self.current_mode = "qr_overlay"

    def show_style_overlay(self):
        print("[AI] Showing style overlay")
        self.clear_gallery_widget()
        overlay = QWidget(self.gallery_widget)
        overlay.setGeometry(0, 0, 480, 320)
        overlay.setStyleSheet("background-color: black;")
        overlay.raise_()

        grid = QGridLayout(overlay)
        grid.setSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)

        styles = [
            ("studio_ghibli", "studio_ghibli"),
            ("van_gogh", "van_gogh"),
            ("renaissance", "mona_lisa"),
            ("medieval", "medieval"),
            ("cyberpunk", "cyberpunk"),
            ("fantasy", "fantasy"),
        ]

        row, col = 0, 0
        for style_name, file_base in styles:
            for ext in [".jpg", ".png"]:
                path = os.path.join(STYLE_DIR, file_base + ext)
                if os.path.exists(path):
                    break
            else:
                print(f"[WARNING] Style image not found for: {style_name}")
                continue

            btn = QPushButton()
            btn.setFixedSize(164, 164)
            btn.setIconSize(QSize(154, 154))
            btn.setStyleSheet(BUTTON_STYLE)

            pixmap = QPixmap(path)
            target_size = QSize(160, 160)
            cropped = self.crop_and_scale_pixmap(pixmap, target_size)
            btn.setIcon(QIcon(cropped))

            btn.clicked.connect(lambda _, name=style_name: self.apply_style(name))
            grid.addWidget(btn, row, col)
            col += 1
            if col == 3:
                col = 0
                row += 1

        self.style_overlay = overlay
        overlay.show()
        self.current_mode = "style_overlay"

    def show_loading_overlay(self):
        if self.loading_overlay:
            self.loading_overlay.deleteLater()

        self.loading_overlay = QWidget(self)
        self.loading_overlay.setGeometry(0, 0, 480, 320)
        self.loading_overlay.setStyleSheet("background-color: white;")
        self.loading_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

        # GIF fullscreen
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

        # Größe und Position
        self.loading_text_label.resize(320, 40)
        self.loading_text_label.move(80, 270)  # zentriert (480 - 320) / 2 = 80

        # Stil: abgerundet, leichter Rahmen, weiches Pastellgelb
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