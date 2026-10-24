"""
Post-processing utilities: solid color background, background image replacement,
auto-crop / trim margins, and edge feathering.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple, Union
from PIL import Image, ImageFilter

from .core import _parse_color


def replace_background_color(
    image: Image.Image,
    color: Union[str, Tuple[int, int, int]] = "#FFFFFF",
) -> Image.Image:
    """
    Replace transparent areas of an RGBA image with a solid color.
    Returns RGB image (or RGBA if color has alpha).
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    rgb = _parse_color(color)
    bg = Image.new("RGBA", image.size, (*rgb, 255))
    composite = Image.alpha_composite(bg, image)
    return composite.convert("RGB")


def replace_background_image(
    foreground: Image.Image,
    background: Union[str, Image.Image],
    fit: str = "cover",
) -> Image.Image:
    """
    Composite foreground subject with transparent background over a background image.

    fit options:
        - 'cover': Scale background to cover foreground, cropping excess.
        - 'contain': Scale foreground to fit inside background.
        - 'fill': Resize background directly to match foreground dimensions.
        - 'center': Center foreground directly onto background without scaling either.
    """
    if foreground.mode != "RGBA":
        foreground = foreground.convert("RGBA")

    if isinstance(background, (str, os.PathLike)):
        bg = Image.open(background).convert("RGBA")
    else:
        bg = background.convert("RGBA")

    fw, fh = foreground.size
    bw, bh = bg.size

    fit = fit.lower().strip()

    if fit == "fill":
        bg_resized = bg.resize((fw, fh), Image.Resampling.LANCZOS)
        return Image.alpha_composite(bg_resized, foreground).convert("RGB")

    elif fit == "cover":
        # Scale bg so it completely covers the foreground
        scale = max(fw / bw, fh / bh)
        new_bw = int(bw * scale)
        new_bh = int(bh * scale)
        bg_scaled = bg.resize((new_bw, new_bh), Image.Resampling.LANCZOS)
        # Crop to (fw, fh) centered
        left = (new_bw - fw) // 2
        top = (new_bh - fh) // 2
        bg_cropped = bg_scaled.crop((left, top, left + fw, top + fh))
        return Image.alpha_composite(bg_cropped, foreground).convert("RGB")

    elif fit == "contain":
        # Scale foreground to fit nicely inside the background image
        scale = min(bw / fw, bh / fh)
        new_fw = int(fw * scale)
        new_fh = int(fh * scale)
        fg_scaled = foreground.resize((new_fw, new_fh), Image.Resampling.LANCZOS)
        pos_x = (bw - new_fw) // 2
        pos_y = (bh - new_fh) // 2
        canvas = bg.copy()
        canvas.paste(fg_scaled, (pos_x, pos_y), fg_scaled)
        return canvas.convert("RGB")

    else:  # default 'center'
        # If dimensions differ, center foreground on bg canvas
        if (bw, bh) == (fw, fh):
            return Image.alpha_composite(bg, foreground).convert("RGB")
        canvas = bg.copy()
        pos_x = (bw - fw) // 2
        pos_y = (bh - fh) // 2
        canvas.paste(foreground, (pos_x, pos_y), foreground)
        return canvas.convert("RGB")


def auto_crop(
    image: Image.Image,
    padding: int = 10,
) -> Image.Image:
    """
    Automatically detect subject bounding box and crop out excess transparent space.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Get alpha bounding box
    alpha = image.split()[-1]
    bbox = alpha.getbbox()
    if not bbox:
        # Image is entirely transparent or empty
        return image

    w, h = image.size
    left, upper, right, lower = bbox

    # Apply padding
    left = max(0, left - padding)
    upper = max(0, upper - padding)
    right = min(w, right + padding)
    lower = min(h, lower + padding)

    return image.crop((left, upper, right, lower))


def apply_feather(
    image: Image.Image,
    radius: int = 2,
) -> Image.Image:
    """
    Feather the edges of the alpha channel to soften harsh pixel cutouts.
    """
    if image.mode != "RGBA" or radius <= 0:
        return image

    r, g, b, a = image.split()
    feathered_a = a.filter(ImageFilter.GaussianBlur(radius=radius))
    return Image.merge("RGBA", (r, g, b, feathered_a))
