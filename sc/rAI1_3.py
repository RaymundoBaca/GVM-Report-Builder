# rAI1_3.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from pathlib import Path
from PIL import Image
import pytesseract
import re
import time
import os
import sys

# ===== Configuración Tesseract portable =====
if getattr(sys, 'frozen', False):
    # Si está compilado con PyInstaller, la carpeta _MEIPASS contiene los binarios
    base_path = Path(sys._MEIPASS) / "tesseract"
else:
    # Ruta local durante desarrollo
    base_path = Path("tesseract")

if os.name == "nt":  # Windows
    pytesseract.pytesseract.tesseract_cmd = str(base_path / "tesseract.exe")
else:  # Linux
    pytesseract.pytesseract.tesseract_cmd = str(base_path / "tesseract")

RED_LOW = np.array([180, 0, 0], dtype=np.uint8)
RED_HIGH = np.array([220, 50, 50], dtype=np.uint8)

YELLOW_LOW = np.array([225, 135, 35], dtype=np.uint8)
YELLOW_HIGH = np.array([255, 180, 70], dtype=np.uint8)

BLUE_LOW = np.array([130, 190, 250], dtype=np.uint8)
BLUE_HIGH = np.array([140, 200, 255], dtype=np.uint8)

MIN_AREA = 50
DELAY = 0.2  # Delay in seconds

# =========================
# Functions
# =========================
def detect_color_regions(arr, low, high):
    mask = np.all((arr >= low) & (arr <= high), axis=2)
    if not mask.any():
        return []
    ys, xs = np.where(mask)
    x1, y1, x2, y2 = xs.min(), ys.min(), xs.max(), ys.max()
    if (x2 - x1) * (y2 - y1) >= MIN_AREA:
        return [(x1, y1, x2, y2)]
    return []

def generate_unique_name(text, counters):
    text = re.sub(r'(High|Medium)\s*\(CVSS:[^)]+\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'NVT:?', '', text, flags=re.IGNORECASE)

    words = text.split()
    if not words:
        words = ["vuln"]

    key = "_".join(words)
    key = re.sub(r'[^\w\-]', '', key)
    key = re.sub(r'_+', '_', key)
    key = key.strip('_')

    if key not in counters:
        counters[key] = 1
    else:
        counters[key] += 1

    return f"{key}{counters[key]}.png"

def base_number(stem):
    m = re.match(r'(\d+)', stem)
    return int(m.group(1)) if m else None

# =========================
# MAIN
# =========================
def main(pdf_path, txt_path, log, output_dir=None, progress_callback=None):
    """
    pdf_path, txt_path: compatibility only
    log: logging function
    output_dir: folder containing the images (tables_png)
    progress_callback: optional callback(float) to report progress (0.0 to 1.0)
    """
    if output_dir:
        results_dir = Path(output_dir) / "Results"
    else:
        results_dir = Path(pdf_path).parent / "Results"
    input_dir = results_dir / "tables_png"

    if not input_dir.exists():
        log(f"⛔ Folder not found: {input_dir}")
        return

    # input_dir now points exactly to the folder with images
    files = sorted(
        [f for f in input_dir.glob("*.png") if not re.match(r'hosts\d+(\.\d+)?', f.stem)],
        key=lambda f: [int(x) if x.isdigit() else float(x) for x in re.split(r'\D+', f.stem) if x]
    )

    if not files:
        log(f"⛔ No images in {input_dir}")
        return

    if progress_callback:
        progress_callback(0.0)

    renames = []
    processed = set()
    hosts_count = 0
    host_count = 0
    blue_count = 0
    vuln_counters = {}
    last_host_name = None
    last_vuln_name = None
    prev_color = None
    initial_blue_block = True
    last_base_num = None
    total_files = len(files)

    for idx, file in enumerate(files):
        if progress_callback and total_files > 0:
            progress_callback(0.8 * (idx + 1) / total_files)
        if file in processed:
            continue

        # ---- INITIAL BLUE BLOCK ----
        if initial_blue_block and file.stem.startswith("1"):
            hosts_count += 1
            new_name = f"hosts{hosts_count}.png"
            renames.append((file, input_dir / new_name))
            processed.add(file)
            log(f"ℹ️ {file.name} → {new_name}")
            continue
        else:
            initial_blue_block = False

        # Detect base number change
        curr_base_num = base_number(file.stem)
        if last_base_num is None:
            last_base_num = curr_base_num
        elif curr_base_num != last_base_num:
            vuln_counters = {}
            last_vuln_name = None
            last_base_num = curr_base_num

        # ---- DETECT COLOR ----
        img = Image.open(file).convert("RGB")
        arr = np.array(img)

        color = None
        if detect_color_regions(arr, BLUE_LOW, BLUE_HIGH):
            color = "Blue"
        elif detect_color_regions(arr, RED_LOW, RED_HIGH):
            color = "Red"
        elif detect_color_regions(arr, YELLOW_LOW, YELLOW_HIGH):
            color = "Yellow"

        # ---- BLUE ----
        if color == "Blue":
            if prev_color == "Blue" and last_host_name:
                blue_count += 1
                new_name = f"{last_host_name}.{blue_count}.png"
            else:
                host_count += 1
                blue_count = 0
                new_name = f"host{host_count}.png"
                last_host_name = f"host{host_count}"
            vuln_counters = {}
            last_vuln_name = None
            renames.append((file, input_dir / new_name))
            processed.add(file)
            prev_color = "Blue"
            continue

        # ---- VULNERABILITIES ----
        if color in ("Red", "Yellow"):
            blue_count = 0
            regions = detect_color_regions(arr, RED_LOW, RED_HIGH) if color == "Red" else detect_color_regions(arr, YELLOW_LOW, YELLOW_HIGH)
            x1, y1, x2, y2 = regions[0]
            text = pytesseract.image_to_string(Image.fromarray(arr[y1:y2, x1:x2]))
            new_name = generate_unique_name(text, vuln_counters)
            last_vuln_name = re.sub(r'\d+\.png$', '', new_name)
            renames.append((file, input_dir / new_name))
            processed.add(file)
            prev_color = color
            continue

        # ---- NO COLOR ----
        if last_vuln_name:
            if last_vuln_name not in vuln_counters:
                vuln_counters[last_vuln_name] = 1
            else:
                vuln_counters[last_vuln_name] += 1
            new_name = f"{last_vuln_name}{vuln_counters[last_vuln_name]}.png"
        else:
            new_name = f"others_{file.stem}.png"

        renames.append((file, input_dir / new_name))
        processed.add(file)
        prev_color = None

        # ---- RENAME FILES ----
    for rename_idx, (old, new) in enumerate(renames):
        if progress_callback and len(renames) > 0:
            progress_callback(0.8 + 0.2 * (rename_idx + 1) / len(renames))
        if old != new:
            if new.exists():
                log(f"ℹ️ {old.name} deleted, {new.name} already exists.")
                try:
                    if old.exists():
                        old.unlink()  # Delete old file
                except FileNotFoundError:
                    pass  # File already deleted or renamed
                continue
            try:
                if old.exists():
                    old.rename(new)
                    time.sleep(DELAY)
            except FileNotFoundError:
                log(f"⚠️ {old.name} not found, skipping.")
                continue
        log(f"ℹ️ {old.name} → {new.name}")

    if progress_callback:
        progress_callback(1.0)

    log(f"✅ Process finished, renamed {len(renames)} images.")
