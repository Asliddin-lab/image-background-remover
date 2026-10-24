"""
Flask Web Application & REST API for Image Background Remover.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image

from .core import remove_background
from .postprocess import (
    auto_crop,
    apply_feather,
    replace_background_color,
    replace_background_image,
)

BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

# Limit uploads to 50MB
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "Image Background Remover"})


@app.route("/api/remove", methods=["POST"])
def api_remove():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided in 'image' field"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        input_image = Image.open(file.stream)
    except Exception as e:
        return jsonify({"error": f"Invalid image format: {e}"}), 400

    # Parse options
    method = request.form.get("method", "ai")
    model_name = request.form.get("model", "u2net")
    alpha_matting = request.form.get("alpha_matting", "false").lower() in ("true", "1", "yes")
    crop = request.form.get("crop", "false").lower() in ("true", "1", "yes")
    feather = int(request.form.get("feather", 0))
    bg_color = request.form.get("color", "").strip() or None
    bg_fit = request.form.get("bg_fit", "cover")

    key_color = request.form.get("key_color", "").strip() or None
    tolerance = float(request.form.get("tolerance", 0.25))
    softness = float(request.form.get("softness", 0.1))

    try:
        # Step 1: Remove background
        result = remove_background(
            image=input_image,
            method=method,
            model_name=model_name,
            key_color=key_color,
            tolerance=tolerance,
            softness=softness,
            alpha_matting=alpha_matting,
        )

        # Step 2: Feather edges
        if feather > 0:
            result = apply_feather(result, radius=feather)

        # Step 3: Auto crop
        if crop:
            result = auto_crop(result, padding=10)

        # Step 4: Background replacement
        if "bg_image" in request.files and request.files["bg_image"].filename:
            bg_file = request.files["bg_image"]
            bg_img = Image.open(bg_file.stream)
            result = replace_background_image(result, background=bg_img, fit=bg_fit)
        elif bg_color and bg_color.lower() != "transparent":
            result = replace_background_color(result, color=bg_color)

        # Return PNG stream
        buf = io.BytesIO()
        result.save(buf, format="PNG")
        buf.seek(0)

        return send_file(
            buf,
            mimetype="image/png",
            as_attachment=False,
            download_name="nobg.png",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def start_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    start_server(debug=True)
