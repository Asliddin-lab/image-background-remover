"""
Command-line interface for Image Background Remover.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List

from PIL import Image

from .core import remove_background
from .postprocess import (
    auto_crop,
    apply_feather,
    replace_background_color,
    replace_background_image,
)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def process_single_file(
    input_file: Path,
    output_file: Path,
    method: str = "ai",
    model_name: str = "u2net",
    key_color: str | None = None,
    tolerance: float = 0.25,
    softness: float = 0.1,
    alpha_matting: bool = False,
    color_bg: str | None = None,
    bg_image_path: str | None = None,
    bg_fit: str = "cover",
    crop: bool = False,
    crop_padding: int = 10,
    feather: int = 0,
) -> None:
    """Process a single image through the pipeline."""
    img = Image.open(input_file)

    # 1. Background removal
    result = remove_background(
        image=img,
        method=method,
        model_name=model_name,
        key_color=key_color,
        tolerance=tolerance,
        softness=softness,
        alpha_matting=alpha_matting,
    )

    # 2. Edge feathering
    if feather > 0:
        result = apply_feather(result, radius=feather)

    # 3. Auto crop
    if crop:
        result = auto_crop(result, padding=crop_padding)

    # 4. Background replacement
    if color_bg:
        result = replace_background_color(result, color=color_bg)
    elif bg_image_path:
        result = replace_background_image(result, background=bg_image_path, fit=bg_fit)

    # 5. Save output
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # If result is RGB (because background was replaced) or format allows, save accordingly
    ext = output_file.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        if result.mode == "RGBA":
            # Flatten onto white background if user specified .jpg
            result = replace_background_color(result, color="#FFFFFF")
        result.save(output_file, format="JPEG", quality=95)
    elif ext == ".webp":
        result.save(output_file, format="WEBP", quality=95)
    else:
        # Default PNG for lossless RGBA transparency
        result.save(output_file, format="PNG")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bg-remover",
        description="🚀 High-Performance Image Background Remover (AI, Chroma-Key & FFmpeg)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic removal to transparent PNG
  bg-remover photo.jpg -o transparent.png

  # Batch process a whole folder
  bg-remover ./input_folder/ -o ./output_folder/

  # Replace background with solid white (e.g. for eCommerce)
  bg-remover product.jpg -o product_white.png --color white

  # Composite subject onto another background image
  bg-remover model.jpg --bg-image beach.jpg -o composited.png

  # Chroma-key green screen removal
  bg-remover actor.png --method colorkey --key-color green -o keyed.png

  # Launch the interactive Web UI
  bg-remover --web
        """,
    )

    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Input image path or directory containing images",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output image path or output directory (default: <name>_nobg.png)",
    )
    parser.add_argument(
        "-m",
        "--method",
        choices=["ai", "colorkey", "ffmpeg"],
        default="ai",
        help="Removal method: 'ai' (neural net), 'colorkey' (chroma color), 'ffmpeg' (FFmpeg filter)",
    )
    parser.add_argument(
        "--model",
        default="u2net",
        help="AI Model name: u2net, u2netp, u2net_human_seg, isnet-general-use, silueta (default: u2net)",
    )
    parser.add_argument(
        "--alpha-matting",
        action="store_true",
        help="Enable alpha matting for finer edge detection (hair, fur)",
    )
    parser.add_argument(
        "--color",
        default=None,
        help="Replace background with solid color (e.g. white, black, '#F0F0F0')",
    )
    parser.add_argument(
        "--bg-image",
        default=None,
        help="Replace background with another image file",
    )
    parser.add_argument(
        "--bg-fit",
        choices=["cover", "contain", "fill", "center"],
        default="cover",
        help="Fit mode when using --bg-image (default: cover)",
    )
    parser.add_argument(
        "--crop",
        action="store_true",
        help="Automatically crop transparent borders around the subject",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=10,
        help="Padding in pixels when --crop is enabled (default: 10)",
    )
    parser.add_argument(
        "--feather",
        type=int,
        default=0,
        help="Feather radius to smooth cutout edges (default: 0)",
    )
    parser.add_argument(
        "--key-color",
        default=None,
        help="Color to remove when using colorkey/ffmpeg (e.g. '#00FF00', 'green'). Auto-detected if omitted.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.25,
        help="Tolerance threshold for colorkey (0.0 to 1.0, default: 0.25)",
    )
    parser.add_argument(
        "--softness",
        type=float,
        default=0.1,
        help="Softness edge transition for colorkey (0.0 to 1.0, default: 0.1)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch the interactive Web UI in your browser",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the Web UI (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind the Web UI (default: 5000)",
    )

    args = parser.parse_args()

    # Launch Web UI if requested or if no arguments provided
    if args.web or args.input is None:
        from .web import start_server
        print(f"\n✨ Starting Image Background Remover Web UI on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop.\n")
        start_server(host=args.host, port=args.port)
        return

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input path '{args.input}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Directory batch mode
    if input_path.is_dir():
        output_dir = Path(args.output) if args.output else input_path.parent / f"{input_path.name}_nobg"
        output_dir.mkdir(parents=True, exist_ok=True)

        files = [p for p in input_path.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS]
        if not files:
            print(f"⚠️  No supported images found in '{input_path}'.")
            sys.exit(0)

        print(f"🔄 Processing {len(files)} images from '{input_path}'...")
        try:
            from tqdm import tqdm
            iterator = tqdm(files, desc="Removing backgrounds")
        except ImportError:
            iterator = files

        success_count = 0
        for file in iterator:
            out_file = output_dir / f"{file.stem}.png"
            try:
                process_single_file(
                    input_file=file,
                    output_file=out_file,
                    method=args.method,
                    model_name=args.model,
                    key_color=args.key_color,
                    tolerance=args.tolerance,
                    softness=args.softness,
                    alpha_matting=args.alpha_matting,
                    color_bg=args.color,
                    bg_image_path=args.bg_image,
                    bg_fit=args.bg_fit,
                    crop=args.crop,
                    crop_padding=args.padding,
                    feather=args.feather,
                )
                success_count += 1
            except Exception as e:
                print(f"⚠️ Failed to process {file.name}: {e}", file=sys.stderr)

        print(f"✅ Finished! {success_count}/{len(files)} images saved to '{output_dir}'.")

    # Single file mode
    else:
        if args.output:
            output_file = Path(args.output)
        else:
            output_file = input_path.parent / f"{input_path.stem}_nobg.png"

        print(f"🔄 Removing background from '{input_path.name}'...")
        try:
            process_single_file(
                input_file=input_path,
                output_file=output_file,
                method=args.method,
                model_name=args.model,
                key_color=args.key_color,
                tolerance=args.tolerance,
                softness=args.softness,
                alpha_matting=args.alpha_matting,
                color_bg=args.color,
                bg_image_path=args.bg_image,
                bg_fit=args.bg_fit,
                crop=args.crop,
                crop_padding=args.padding,
                feather=args.feather,
            )
            print(f"✅ Success! Saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
