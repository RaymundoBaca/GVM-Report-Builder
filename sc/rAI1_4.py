# rAI1_4.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import fitz
import numpy as np
from pathlib import Path
from PIL import Image
import pytesseract
import re
import sys
import os

# =========================
# Tesseract Configuration (Portable)
# =========================
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

# =========================
# Color Ranges (RGB)
# =========================
RED_LOW = np.array([180, 0, 0], dtype=np.uint8)
RED_HIGH = np.array([220, 50, 50], dtype=np.uint8)

YELLOW_LOW = np.array([225, 135, 35], dtype=np.uint8)
YELLOW_HIGH = np.array([255, 180, 70], dtype=np.uint8)

MIN_AREA = 80

# =========================
# Functions
# =========================
def detect_all_rgb_regions(arr, ranges):
    results = {i: [] for i in range(len(ranges))}
    for idx, (low, high) in enumerate(ranges):
        mask = np.all((arr[:, :, :3] >= low) & (arr[:, :, :3] <= high), axis=2)
        if mask.any():
            ys, xs = np.where(mask)
            x1, y1, x2, y2 = xs.min(), ys.min(), xs.max(), ys.max()
            if (x2 - x1) * (y2 - y1) >= MIN_AREA:
                results[idx].append((x1, y1, x2, y2))
    return results

def generate_unique_name(text, existing):
    text = re.sub(r'(High|Medium)\s*\(CVSS:[^)]+\)', '', text, flags=re.IGNORECASE)
    words = text.split()[:4]
    name = "_".join(words) if words else "crop"
    name = re.sub(r'[^\w\-]', '', name)
    if name.startswith("NVT_"):
        name = name[4:]
    if name in existing:
        return None
    existing.add(name)
    return name

def export_fast_crops(pdf_path, output_dir, log, progress_callback=None):
    doc = fitz.open(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    high_count = 0
    medium_count = 0
    existing_text = set()
    total_pages = len(doc)

    for page_num, page in enumerate(doc, start=1):
        if progress_callback and total_pages > 0:
            progress_callback((page_num - 1) / total_pages)
        pix = page.get_pixmap(dpi=200)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        arr = arr[:, :, :3]

        regions = detect_all_rgb_regions(arr, [(RED_LOW, RED_HIGH), (YELLOW_LOW, YELLOW_HIGH)])

        for color_idx, regions_color in regions.items():
            for (x1, y1, x2, y2) in regions_color:
                crop = Image.fromarray(arr[y1:y2, x1:x2])
                text = pytesseract.image_to_string(crop)
                name = generate_unique_name(text, existing_text)
                if name is None:
                    continue
                crop.save(output_dir / f"{name}.png")
                if color_idx == 0:
                    high_count += 1
                else:
                    medium_count += 1
                log(f"ℹ️ Saved crop {name}.png (Page {page_num})")

    if progress_callback:
        progress_callback(1.0)

    log(f"✅ HIGH crops saved: {high_count}")
    log(f"✅ MEDIUM crops saved: {medium_count}")

# =========================
# MAIN
# =========================
def main(pdf_path, txt_path, log, output_dir=None, progress_callback=None):
    if not pdf_path or not Path(pdf_path).exists():
        log(f"⛔ {pdf_path} not found")
        return

    if not output_dir:
        log("⛔ No output folder specified")
        return

    # Always use "Results/tables_png" inside the output_dir
    results_dir = Path(output_dir) / "Results"
    input_dir = results_dir / "tables_png"
    input_dir.mkdir(parents=True, exist_ok=True)

    export_fast_crops(pdf_path, input_dir, log, progress_callback=progress_callback)
