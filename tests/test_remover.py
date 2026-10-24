"""
Comprehensive unit and integration tests for Image Background Remover.
"""

import io
import shutil
from pathlib import Path
from PIL import Image, ImageDraw
import pytest

from bg_remover.core import (
    remove_background,
    remove_background_ai,
    remove_background_colorkey,
    remove_background_ffmpeg,
)
from bg_remover.postprocess import (
    auto_crop,
    apply_feather,
    replace_background_color,
    replace_background_image,
)
from bg_remover.web import app


@pytest.fixture
def sample_green_screen_image():
    """Create a 100x100 green screen image with a red centered circle."""
    img = Image.new("RGB", (100, 100), color=(0, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([30, 30, 70, 70], fill=(255, 0, 0))
    return img


@pytest.fixture
def sample_transparent_image():
    """Create a 100x100 RGBA image with transparent margins and opaque red center."""
    img = Image.new("RGBA", (100, 100), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([25, 25, 75, 75], fill=(255, 0, 0, 255))
    return img


def test_colorkey_removal(sample_green_screen_image):
    result = remove_background_colorkey(
        sample_green_screen_image,
        key_color=(0, 255, 0),
        tolerance=0.2,
        softness=0.05,
    )
    assert result.mode == "RGBA"
    # Corner (green background) should be transparent (alpha 0)
    assert result.getpixel((0, 0))[3] == 0
    # Center (red circle) should be opaque (alpha 255)
    assert result.getpixel((50, 50))[3] == 255
    assert result.getpixel((50, 50))[:3] == (255, 0, 0)


def test_ffmpeg_colorkey(sample_green_screen_image):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not installed")

    result = remove_background_ffmpeg(
        sample_green_screen_image,
        key_color="0x00FF00",
        similarity=0.3,
        blend=0.1,
    )
    assert result.mode == "RGBA"
    # Corner should be transparent
    assert result.getpixel((0, 0))[3] == 0
    # Center should remain red
    assert result.getpixel((50, 50))[3] == 255


def test_replace_background_color(sample_transparent_image):
    result = replace_background_color(sample_transparent_image, color="#0000FF")
    assert result.mode == "RGB"
    # Corner should now be blue
    assert result.getpixel((0, 0)) == (0, 0, 255)
    # Center should still be red
    assert result.getpixel((50, 50)) == (255, 0, 0)


def test_replace_background_image(sample_transparent_image):
    bg = Image.new("RGB", (100, 100), color=(255, 255, 0))  # yellow
    result = replace_background_image(sample_transparent_image, background=bg, fit="cover")
    assert result.mode == "RGB"
    # Corner should have background yellow color
    assert result.getpixel((0, 0)) == (255, 255, 0)
    # Center should have foreground red color
    assert result.getpixel((50, 50)) == (255, 0, 0)


def test_auto_crop(sample_transparent_image):
    cropped = auto_crop(sample_transparent_image, padding=0)
    # Original is 100x100, subject rectangle is [25, 25, 75, 75]
    # Cropped size should be approx 51x51
    w, h = cropped.size
    assert 48 <= w <= 52
    assert 48 <= h <= 52


def test_apply_feather(sample_transparent_image):
    feathered = apply_feather(sample_transparent_image, radius=3)
    assert feathered.mode == "RGBA"
    # Border pixels between 20-30 should have blurred alpha values between 0 and 255
    alpha_edge = feathered.getpixel((24, 25))[3]
    assert 0 < alpha_edge < 255


def test_ai_removal():
    # Test rembg AI model inference with lightweight model u2netp
    img = Image.new("RGB", (128, 128), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    draw.ellipse([32, 32, 96, 96], fill=(240, 240, 240))

    result = remove_background(img, method="ai", model_name="u2netp")
    assert result.mode == "RGBA"
    assert result.size == (128, 128)


def test_web_api_remove(sample_green_screen_image):
    client = app.test_client()

    img_bytes = io.BytesIO()
    sample_green_screen_image.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    response = client.post(
        "/api/remove",
        data={
            "image": (img_bytes, "test.png"),
            "method": "colorkey",
            "key_color": "#00FF00",
            "tolerance": "0.2",
            "softness": "0.05",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.mimetype == "image/png"
    out_img = Image.open(io.BytesIO(response.data))
    assert out_img.mode == "RGBA"
    assert out_img.getpixel((0, 0))[3] == 0


def test_cli_execution(tmp_path, sample_green_screen_image):
    input_file = tmp_path / "sample.png"
    output_file = tmp_path / "result.png"
    sample_green_screen_image.save(input_file)

    import subprocess
    import sys

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "bg_remover.cli",
            str(input_file),
            "-o",
            str(output_file),
            "-m",
            "colorkey",
            "--key-color",
            "green",
            "--crop",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert res.returncode == 0
    assert output_file.exists()
    out_img = Image.open(output_file)
    assert out_img.mode == "RGBA"
    assert out_img.getpixel((0, 0))[3] == 0

