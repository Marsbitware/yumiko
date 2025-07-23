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
  <style># server.py
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
  <style>
    :root {
      --black: #0d0d0d;
      --dark-purple: #2c003e;
      --deep-blue: #001f4d;
      --gray: #cccccc;
      --white: #ffffff;
      --button-gradient: linear-gradient(90deg, #ffffff, #dddddd);
    }

    body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #0d0d0d, #2c003e, #001f4d, #000000);
      background-size: 400% 400%;
      animation: gradientFlow 15s ease infinite;
      color: var(--white);
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
    }

    @keyframes gradientFlow {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }

    .container {
      background: rgba(255, 255, 255, 0.05);
      padding: 30px;
      border-radius: 20px;
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.8);
      max-width: 90%;
      width: 420px;
      text-align: center;
      backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    h1 {
      font-size: 28px;
      margin-bottom: 20px;
      background: linear-gradient(90deg, #bbbbbb, #ffffff);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    img {
      width: 100%;
      height: auto;
      border-radius: 12px;
      margin-bottom: 20px;
      box-shadow: 0 0 12px rgba(255, 255, 255, 0.1);
    }

    .download-btn {
      display: inline-block;
      background: var(--button-gradient);
      color: #111;
      font-weight: bold;
      padding: 12px 24px;
      border-radius: 10px;
      text-decoration: none;
      font-size: 16px;
      transition: all 0.3s ease;
    }

    .download-btn:hover {
      background: linear-gradient(90deg, #eeeeee, #cccccc);
      transform: scale(1.05);
    }

    .footer {
      margin-top: 15px;
      font-size: 13px;
      color: var(--gray);
      opacity: 0.6;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Dein Bild</h1>
    <img src="/photos/{{filename}}" alt="Foto"><br>
    <a href="/photos/{{filename}}" download class="download-btn">📥 Bild herunterladen</a>
  </div>
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