# server.py
import os
from flask import Flask, send_from_directory, render_template_string, abort

app = Flask(__name__)
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "photos")


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Bild-Download</title>
  <style>
    body {
      margin: 0;
      font-family: 'Segoe UI', sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      background: linear-gradient(135deg, #6a11cb, #2575fc); /* Initialer Verlauf */
      color: white;
      transition: background 1s ease;
    }

    .container {
      text-align: center;
      padding: 20px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 15px;
      box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }

    img {
      max-width: 100%;
      height: auto;
      border-radius: 10px;
      margin-bottom: 20px;
    }

    .download-btn {
      background-color: #ffffff;
      color: #2575fc;
      border: none;
      padding: 12px 24px;
      font-size: 16px;
      border-radius: 8px;
      cursor: pointer;
      transition: background-color 0.3s ease;
      text-decoration: none;
    }

    .download-btn:hover {
      background-color: #e0e0e0;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Dein Bild</h1>
    <img src="beispielbild.jpg" alt="Beispielbild" id="mainImage" crossorigin="anonymous" />
    <br />
    <a href="beispielbild.jpg" download="beispielbild.jpg" class="download-btn">📥 Bild herunterladen</a>
  </div>

  <!-- Color Thief Library -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/color-thief/2.3.2/color-thief.umd.js"></script>

  <!-- Eingebettetes JavaScript -->
  <script>
    window.onload = function () {
      const img = document.getElementById('mainImage');
      const colorThief = new ColorThief();

      if (img.complete) {
        applyGradient();
      } else {
        img.addEventListener('load', applyGradient);
      }

      function applyGradient() {
        try {
          const dominantColor = colorThief.getColor(img);
          const gradient = `linear-gradient(135deg, rgb(${dominantColor.join(',')}), #ffffff)`;
          document.body.style.background = gradient;
        } catch (error) {
          console.error('Fehler beim Farbextrahieren:', error);
        }
      }
    };
  </script>
</body>
</html>
"""


@app.route("/view/<path:filename>")
def view(filename):
    if '..' in filename or filename.startswith("/"):
        abort(404)
    filepath = os.path.join(PHOTOS_DIR, filename)
    if not os.path.isfile(filepath):
        abort(404)
    return render_template_string(HTML_TEMPLATE, filename=filename)

@app.route("/photos/<path:filename>")
def photos(filename):
    return send_from_directory(PHOTOS_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)