"""
Example: Using ClearBG Python API
"""

from PIL import Image, ImageDraw
from bg_remover import (
    remove_background,
    replace_background_color,
    replace_background_image,
    auto_crop,
    apply_feather,
)


def main():
    # 1. Create a sample image (or open your own with Image.open("photo.jpg"))
    img = Image.new("RGB", (300, 300), color=(0, 255, 0))  # Green background
    draw = ImageDraw.Draw(img)
    draw.ellipse([80, 80, 220, 220], fill=(240, 50, 50))  # Red sphere
    img.save("sample_subject.png")
    print("Saved sample_subject.png")

    # 2. Remove background to transparent PNG
    print("1. Removing background with Chroma/Color-key...")
    transparent_result = remove_background(
        "sample_subject.png",
        method="colorkey",
        key_color="green",
    )
    transparent_result.save("output_transparent.png")
    print("-> Saved output_transparent.png")

    # 3. Replace background with clean solid white (eCommerce ready)
    print("2. Replacing background with solid white...")
    white_bg_result = replace_background_color(transparent_result, color="#FFFFFF")
    white_bg_result.save("output_white.jpg", quality=95)
    print("-> Saved output_white.jpg")

    # 4. Composite subject onto another background image
    print("3. Compositing onto background...")
    bg_canvas = Image.new("RGB", (400, 400), color=(30, 40, 70))
    composited = replace_background_image(transparent_result, background=bg_canvas, fit="cover")
    composited.save("output_composited.jpg")
    print("-> Saved output_composited.jpg")

    # 5. Auto crop to remove empty space around the subject
    print("4. Auto-cropping transparent margins...")
    cropped = auto_crop(transparent_result, padding=10)
    cropped.save("output_cropped.png")
    print(f"-> Saved output_cropped.png (Original: {transparent_result.size}, Cropped: {cropped.size})")


if __name__ == "__main__":
    main()
