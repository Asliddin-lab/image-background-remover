"""
Core background removal engine supporting AI models, Chroma/Color-keying, and FFmpeg.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
from typing import Optional, Tuple, Union

import numpy as np
from PIL import Image

try:
    import rembg
    _REMBG_AVAILABLE = True
except ImportError:
    _REMBG_AVAILABLE = False

# Cache sessions by model name for high performance in batch / web requests
_SESSIONS: dict[str, any] = {}


def _get_rembg_session(model_name: str = "u2net"):
    """Get or create cached rembg ONNX session."""
    if not _REMBG_AVAILABLE:
        raise ImportError(
            "rembg is not installed. Run 'pip install rembg[cpu]' or 'pip install onnxruntime rembg'."
        )
    if model_name not in _SESSIONS:
        _SESSIONS[model_name] = rembg.new_session(model_name)
    return _SESSIONS[model_name]


def _parse_color(color: Union[str, Tuple[int, int, int]]) -> Tuple[int, int, int]:
    """Parse color string (hex or rgb name) or tuple into (R, G, B)."""
    if isinstance(color, (tuple, list)):
        return int(color[0]), int(color[1]), int(color[2])
    
    color = color.strip()
    if color.startswith("#"):
        color = color.lstrip("#")
        if len(color) == 3:
            color = "".join(c * 2 for c in color)
        if len(color) == 6:
            return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        raise ValueError(f"Invalid hex color format: #{color}")

    named = {
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "red": (255, 0, 0),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
        "yellow": (255, 255, 0),
    }
    if color.lower() in named:
        return named[color.lower()]

    raise ValueError(f"Unknown color: {color}. Use hex format like '#00FF00' or (R, G, B).")


def remove_background_ai(
    image: Image.Image,
    model_name: str = "u2net",
    alpha_matting: bool = False,
    alpha_matting_foreground_threshold: int = 240,
    alpha_matting_background_threshold: int = 10,
    alpha_matting_erode_size: int = 10,
    post_process_mask: bool = False,
) -> Image.Image:
    """
    Remove background using deep learning ONNX models via rembg.
    
    Supported models:
        - 'u2net': General high accuracy default
        - 'u2netp': Lightweight faster version of u2net
        - 'u2net_human_seg': Specifically tuned for portraits and human bodies
        - 'isnet-general-use': High-definition edge boundary precision
        - 'silueta': Compact, tiny footprint model
    """
    if not _REMBG_AVAILABLE:
        raise RuntimeError("rembg is required for AI background removal.")

    session = _get_rembg_session(model_name)
    output = rembg.remove(
        image,
        session=session,
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
        alpha_matting_background_threshold=alpha_matting_background_threshold,
        alpha_matting_erode_size=alpha_matting_erode_size,
        post_process_mask=post_process_mask,
    )
    if output.mode != "RGBA":
        output = output.convert("RGBA")
    return output


def remove_background_colorkey(
    image: Image.Image,
    key_color: Optional[Union[str, Tuple[int, int, int]]] = None,
    tolerance: float = 0.25,
    softness: float = 0.1,
) -> Image.Image:
    """
    Remove solid background color (e.g. green screen, blue screen, pure white/black backdrop)
    using smooth Euclidean distance color-keying.

    If key_color is None, it samples the corners of the image to auto-detect the background color.
    tolerance: float between 0.0 and 1.0 (relative color distance)
    softness: float between 0.0 and 1.0 (smooth alpha transition border)
    """
    rgb_img = image.convert("RGB")
    arr = np.array(rgb_img, dtype=np.float32)

    if key_color is None:
        # Sample 4 corners
        h, w, _ = arr.shape
        corners = [
            arr[0, 0],
            arr[0, w - 1],
            arr[h - 1, 0],
            arr[h - 1, w - 1],
        ]
        key_rgb = np.mean(corners, axis=0)
    else:
        key_rgb = np.array(_parse_color(key_color), dtype=np.float32)

    # Normalize max distance in RGB space: sqrt(255^2 * 3) ~ 441.67
    max_dist = 441.6729559300637
    dist = np.linalg.norm(arr - key_rgb, axis=-1) / max_dist

    tol = max(0.001, min(1.0, float(tolerance)))
    soft = max(0.001, min(1.0, float(softness)))

    # Compute alpha mask: 0 (transparent) when dist <= tol, 1 (opaque) when dist >= tol + soft
    alpha = np.clip((dist - tol) / soft, 0.0, 1.0)
    alpha = (alpha * 255.0).astype(np.uint8)

    # Reconstruct RGBA
    r, g, b = rgb_img.split()
    a = Image.fromarray(alpha, mode="L")
    return Image.merge("RGBA", (r, g, b, a))


def remove_background_ffmpeg(
    image: Image.Image,
    key_color: Union[str, Tuple[int, int, int]] = "0x00FF00",
    similarity: float = 0.3,
    blend: float = 0.1,
) -> Image.Image:
    """
    Remove background using FFmpeg's colorkey filter.
    Requires `ffmpeg` installed on the system PATH.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg executable not found on system PATH.")

    # Convert key_color to hex format for ffmpeg: 0xRRGGBB
    if isinstance(key_color, (tuple, list)):
        r, g, b = key_color
        hex_color = f"0x{r:02X}{g:02X}{b:02X}"
    elif isinstance(key_color, str):
        if key_color.startswith("0x"):
            hex_color = key_color
        elif key_color.startswith("#"):
            rgb = _parse_color(key_color)
            hex_color = f"0x{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
        else:
            rgb = _parse_color(key_color)
            hex_color = f"0x{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    else:
        hex_color = "0x00FF00"

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "in.png")
        output_path = os.path.join(tmpdir, "out.png")
        image.save(input_path, format="PNG")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-filter_complex", f"[0:v]colorkey={hex_color}:{similarity}:{blend}[out]",
            "-map", "[out]",
            output_path,
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg colorkey failed: {res.stderr.decode('utf-8', errors='ignore')}")

        result = Image.open(output_path)
        result.load()
        return result.convert("RGBA")


def remove_background(
    image: Union[str, bytes, io.BytesIO, Image.Image],
    method: str = "ai",
    model_name: str = "u2net",
    key_color: Optional[Union[str, Tuple[int, int, int]]] = None,
    tolerance: float = 0.25,
    softness: float = 0.1,
    alpha_matting: bool = False,
    alpha_matting_foreground_threshold: int = 240,
    alpha_matting_background_threshold: int = 10,
    alpha_matting_erode_size: int = 10,
) -> Image.Image:
    """
    Main entry point for removing an image background.

    Args:
        image: Path to image, raw image bytes, BytesIO stream, or PIL Image.
        method: 'ai' (neural net), 'colorkey'/'color' (chroma/color distance), or 'ffmpeg' (FFmpeg filter).
        model_name: Model used if method='ai' ('u2net', 'u2netp', 'u2net_human_seg', 'isnet-general-use', 'silueta').
        key_color: Target background color for 'colorkey' or 'ffmpeg'. If None, auto-detected from corners.
        tolerance: Color distance tolerance (0.0 to 1.0).
        softness: Alpha transition edge softness (0.0 to 1.0).
        alpha_matting: Refine hair, fur, and intricate boundaries (AI method only).

    Returns:
        PIL.Image.Image in RGBA mode with background removed.
    """
    if isinstance(image, (str, os.PathLike)):
        pil_img = Image.open(image)
    elif isinstance(image, bytes):
        pil_img = Image.open(io.BytesIO(image))
    elif isinstance(image, io.BytesIO):
        pil_img = Image.open(image)
    elif isinstance(image, Image.Image):
        pil_img = image
    else:
        raise TypeError(f"Unsupported image input type: {type(image)}")

    method = method.lower().strip()
    if method in ("ai", "u2net", "rembg"):
        return remove_background_ai(
            pil_img,
            model_name=model_name,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold,
            alpha_matting_erode_size=alpha_matting_erode_size,
        )
    elif method in ("colorkey", "color", "chroma"):
        return remove_background_colorkey(
            pil_img,
            key_color=key_color,
            tolerance=tolerance,
            softness=softness,
        )
    elif method == "ffmpeg":
        return remove_background_ffmpeg(
            pil_img,
            key_color=key_color or "0x00FF00",
            similarity=tolerance,
            blend=softness,
        )
    else:
        raise ValueError(f"Unknown background removal method: {method}. Choose 'ai', 'colorkey', or 'ffmpeg'.")
