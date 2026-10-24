"""
Image Background Remover - High quality AI and Chroma-Key background removal tool.
"""

from .core import (
    remove_background,
    remove_background_ai,
    remove_background_colorkey,
    remove_background_ffmpeg,
)
from .postprocess import (
    auto_crop,
    apply_feather,
    replace_background_color,
    replace_background_image,
)

__version__ = "1.0.0"

__all__ = [
    "remove_background",
    "remove_background_ai",
    "remove_background_colorkey",
    "remove_background_ffmpeg",
    "replace_background_color",
    "replace_background_image",
    "auto_crop",
    "apply_feather",
]
