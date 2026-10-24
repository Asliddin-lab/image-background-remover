# ✨ ClearBG — Image Background Remover

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![GitHub Stars](https://img.shields.io/github/stars/Asliddin-lab/image-background-remover?style=social)](https://github.com/Asliddin-lab/image-background-remover)

A high-performance, modular image background remover powered by **State-of-the-Art Deep Learning (U2Net / IS-Net)**, **Chroma/Color-Key algorithms**, and **FFmpeg**. 

Features an intuitive **CLI**, a flexible **Python Library API**, and a modern **Interactive Web UI** with a live before/after comparison slider!

---

## 🚀 Key Features

- **🧠 State-of-the-Art AI Segmentation**:
  - Powered by ONNX Runtime (`u2net`, `u2netp`, `u2net_human_seg`, `isnet-general-use`, `silueta`).
  - Seamlessly separates complex natural backgrounds (people, pets, hair, products, cars).
- **🎨 Chroma & Color-Key Engine**:
  - Instant background removal for green screens, blue screens, or studio backdrops without needing GPU or heavy models.
  - Auto-detects backdrop color by sampling image corners.
- **🎬 FFmpeg Integration**:
  - High-speed colorkey filtering using system FFmpeg.
- **🖼️ Background Replacement**:
  - Swap transparent areas with **solid colors** (eCommerce white `#FFFFFF`, dark obsidian, or custom HEX/RGB).
  - Composite subjects onto **custom background photos** with `cover`, `contain`, `fill`, or `center` aspect-ratio modes.
- **✂️ Auto-Crop & Alpha Matting**:
  - Automatically trim empty transparent margins tightly around the subject.
  - Edge feathering and alpha matting for soft hair and fur details.
- **📁 Batch Processing**:
  - Process entire folders with parallel multi-threading and interactive progress bars (`tqdm`).
- **🌐 Interactive Web Interface**:
  - Beautiful drag-and-drop web UI with an **interactive before/after split slider**, live color palette picker, and 1-click downloads.
- **⚡ REST API**:
  - Ready-to-use HTTP endpoint (`/api/remove`) for integration into external workflows and apps.

---

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Asliddin-lab/image-background-remover.git
cd image-background-remover
```

### 2. Set Up a Virtual Environment
```bash
python3 -m venv .venv

# On macOS/Linux:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

> **Note on FFmpeg (Optional):**  
> If you wish to use the `--method ffmpeg` engine, ensure `ffmpeg` is installed:  
> - **macOS**: `brew install ffmpeg`  
> - **Ubuntu/Debian**: `sudo apt install ffmpeg`  
> - **Windows**: `winget install Gyan.FFmpeg` or `choco install ffmpeg`

---

## 🖥️ Usage

### 1. Command-Line Interface (CLI)

#### 🔹 Basic Background Removal (Transparent PNG)
```bash
bg-remover input.jpg -o output.png
```

#### 🔹 Batch Process an Entire Directory
```bash
bg-remover ./input_photos/ -o ./output_nobg/
```

#### 🔹 Replace Background with Solid Color (eCommerce White)
```bash
bg-remover product.jpg -o product_white.png --color white
# or custom hex code:
bg-remover product.jpg -o product_custom.png --color "#F4F4F6"
```

#### 🔹 Composite Subject onto Another Image
```bash
bg-remover model.jpg --bg-image landscape.jpg --bg-fit cover -o composited.png
```

#### 🔹 Chroma-Key / Green Screen Removal
```bash
bg-remover actor.png --method colorkey --key-color green -o keyed.png
```

#### 🔹 Auto-Crop Tight Around Subject
```bash
bg-remover logo.png -o cropped.png --crop --padding 10
```

#### 🔹 Edge Feathering & Alpha Matting for Hair/Fur
```bash
bg-remover portrait.jpg -o refined.png --alpha-matting --feather 2
```

---

### 2. CLI Options Reference

| Flag | Description | Default |
|---|---|---|
| `input` | Input image file or directory | *(Required)* |
| `-o, --output` | Destination file or directory | `<name>_nobg.png` |
| `-m, --method` | Removal method (`ai`, `colorkey`, `ffmpeg`) | `ai` |
| `--model` | AI model (`u2net`, `u2netp`, `u2net_human_seg`, `isnet-general-use`, `silueta`) | `u2net` |
| `--color` | Replace background with solid color (e.g. `white`, `#FFFFFF`) | `None` (transparent) |
| `--bg-image` | Composite onto a background photo file | `None` |
| `--bg-fit` | Fit mode for background image (`cover`, `contain`, `fill`, `center`) | `cover` |
| `--crop` | Automatically crop transparent borders around the subject | `False` |
| `--padding` | Pixel padding for auto-crop | `10` |
| `--feather` | Radius for smoothing alpha cutout edges | `0` (off) |
| `--alpha-matting` | Fine edge matting for intricate hair/fur | `False` |
| `--key-color` | Color to remove for colorkey/ffmpeg (e.g. `green`, `#00FF00`) | Auto-detect |
| `--tolerance` | Color distance tolerance for colorkey (0.0 - 1.0) | `0.25` |
| `--web` | Launch the interactive Web UI in your browser | `False` |
| `--port` | Port for the Web UI | `5000` |

---

### 3. Interactive Web UI

Launch the built-in browser UI with a single command:

```bash
bg-remover --web
```
Or:
```bash
python -m bg_remover --web
```

Open your browser at **`http://localhost:5000`**:
- **Drag & Drop** any image.
- **Split Comparison Slider**: Slide back and forth to inspect edges before downloading.
- **Instant Background Swapping**: Switch between transparent, preset colors, or custom palettes.
- **Download**: 1-click PNG export.

---

### 4. Python API Usage

You can easily integrate ClearBG into your Python scripts or web servers:

```python
from PIL import Image
from bg_remover import (
    remove_background,
    replace_background_color,
    replace_background_image,
    auto_crop,
)

# 1. Remove background (transparent RGBA)
img = Image.open("subject.jpg")
result = remove_background(img, method="ai", model_name="u2net")
result.save("subject_transparent.png")

# 2. Replace background with solid white
white_bg = replace_background_color(result, color="#FFFFFF")
white_bg.save("subject_white.jpg")

# 3. Composite onto a background image
bg_photo = Image.open("beach.jpg")
composited = replace_background_image(result, background=bg_photo, fit="cover")
composited.save("subject_on_beach.jpg")

# 4. Auto-crop empty margins
tight_crop = auto_crop(result, padding=15)
tight_crop.save("subject_cropped.png")
```

---

### 5. REST API

ClearBG includes a lightweight REST API endpoint:

```bash
curl -X POST http://localhost:5000/api/remove \
  -F "image=@photo.jpg" \
  -F "method=ai" \
  -F "color=#FFFFFF" \
  --output result.png
```

---

## 🧪 Running Tests

Run the test suite with `pytest`:

```bash
pytest tests/ -v
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

Give a star ⭐ if you liked it!
