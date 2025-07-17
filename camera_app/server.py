# server.py
import os
from flask import Flask, send_from_directory, render_template_string, abort

app = Flask(__name__)
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "photos")


HTML_TEMPLATE = """
<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8">
    <title>Foto anzeigen & herunterladen</title>
    <style>
        body {
            text-align: center;
            background: #f8f8f8;
            font-family: Arial, sans-serif;
        }
        img {
            max-width: 90vw;
            max-height: 70vh;
            border: 1px solid #ccc;
        }
        .download-btn {
            margin-top: 20px;
            padding: 12px 24px;
            font-size: 16px;
            background-color: #007acc;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .download-btn:hover {
            background-color: #005f99;
        }
    </style>
</head>
<body>
    <h2>Dein Foto</h2>
    <img src="/photos/{{filename}}" alt="Foto"><br>
    <a href="/photos/{{filename}}" download class="download-btn">📥 Bild herunterladen</a>
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