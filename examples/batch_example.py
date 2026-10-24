"""
Example: Batch Processing a folder of images
"""

from pathlib import Path
from PIL import Image, ImageDraw
from bg_remover.cli import process_single_file


def create_mock_images(folder: Path, count: int = 3):
    folder.mkdir(parents=True, exist_ok=True)
    colors = [(255, 0, 0), (0, 0, 255), (255, 165, 0)]
    for i in range(count):
        img = Image.new("RGB", (200, 200), color=(0, 255, 0))  # Green screen
        draw = ImageDraw.Draw(img)
        draw.rectangle([40, 40, 160, 160], fill=colors[i % len(colors)])
        img.save(folder / f"product_{i+1}.png")


def main():
    input_dir = Path("mock_input_products")
    output_dir = Path("mock_output_nobg")

    print(f"Creating sample images in '{input_dir}'...")
    create_mock_images(input_dir, count=3)

    print(f"Batch processing images to '{output_dir}'...")
    for file in input_dir.glob("*.png"):
        out_file = output_dir / f"{file.stem}.png"
        print(f"Processing {file.name} -> {out_file.name}")
        process_single_file(
            input_file=file,
            output_file=out_file,
            method="colorkey",
            key_color="green",
            crop=True,
            crop_padding=8,
        )

    print("Batch processing complete! Check:", output_dir)


if __name__ == "__main__":
    main()
