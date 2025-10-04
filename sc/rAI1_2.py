# rAI1_2.py
# -*- coding: utf-8 -*-

import re
import time
from pathlib import Path
from PIL import Image
import numpy as np

# =========================
# Colors and tolerances
# =========================
YELLOW_ORANGE = (247, 158, 49)
RED = (202, 29, 23)
TOL_STOP = 20  # tolerance for RGB colors

# =========================
# Color functions
# =========================
def contains_color(img_path, color_ref, tol):
    """Detect exact colors (Red, Yellow-Orange) with per-channel tolerance"""
    try:
        img = Image.open(img_path).convert("RGB")
        arr = np.array(img)
        mask = np.all(np.abs(arr - np.array(color_ref)) <= tol, axis=2)
        return np.any(mask)
    except Exception:
        return False

def rgb2hsv_vectorized(arr):
    """Convert normalized RGB array [0,1] to HSV vectorized"""
    r, g, b = arr[...,0], arr[...,1], arr[...,2]
    mx = np.max(arr, axis=2)
    mn = np.min(arr, axis=2)
    diff = mx - mn

    # H
    h = np.zeros_like(mx)
    mask = diff != 0
    idx = (mx == r) & mask
    h[idx] = (60 * ((g[idx]-b[idx])/diff[idx]) + 0) % 360
    idx = (mx == g) & mask
    h[idx] = (60 * ((b[idx]-r[idx])/diff[idx]) + 120) % 360
    idx = (mx == b) & mask
    h[idx] = (60 * ((r[idx]-g[idx])/diff[idx]) + 240) % 360
    h[~mask] = 0

    # S
    s = np.zeros_like(mx)
    s[mx != 0] = (diff[mx != 0] / mx[mx != 0]) * 100

    # V
    v = mx * 100

    return h, s, v

def contains_opaque_blue_hsv(img_path):
    """Detect opaque blue robustly using HSV vectorized"""
    try:
        img = Image.open(img_path).convert("RGB")
        arr = np.array(img)/255.0
        h, s, v = rgb2hsv_vectorized(arr)
        mask = (h >= 200) & (h <= 240) & (s >= 20) & (v >= 20)
        return np.any(mask)
    except Exception:
        return False

def detect_color(img_path):
    """Detect the declared color or None if none found"""
    if contains_opaque_blue_hsv(img_path):
        return "Opaque Blue"
    for color_ref, name in [
        (YELLOW_ORANGE, "Yellow-Orange"),
        (RED, "Red"),
    ]:
        if contains_color(img_path, color_ref, TOL_STOP):
            return name
    return None

def sort_files(files):
    """Sort files by number in the filename"""
    def key_func(f):
        m = re.search(r"(\d+(\.\d+)?)", f.stem)
        return float(m.group(1)) if m else 0
    return sorted(files, key=key_func)

# =========================
# MAIN adapted
# =========================
def main(pdf_path, txt_path, log, output_dir=None, progress_callback=None):
    """
    pdf_path: PDF path (compatibility only)
    txt_path: TXT path (compatibility only)
    log: logging function (e.g., print or GUI callback)
    output_dir: folder containing images (tables_png)
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

    files = sort_files(list(input_dir.glob("*.png")))
    if not files:
        log("⛔ No images found in the folder.")
        return

    if progress_callback:
        progress_callback(0.0)

    renames = []
    current_index = 1
    sub_index = 0
    i = 0
    total_files = len(files)

    # -------- INITIAL BLOCK OF BLUES --------
    initial_blues = []
    while i < len(files) and detect_color(files[i]) == "Opaque Blue":
        initial_blues.append(files[i])
        i += 1

    # Assign names to initial blues
    for k, f in enumerate(initial_blues):
        if progress_callback and total_files > 0:
            progress_callback(0.2 * (k + 1) / len(initial_blues) if initial_blues else 0.0)
        if k == 0:
            new_name = f"{current_index}.png"
            log(f"ℹ️ {f.name} -> {new_name} (Initial Blue)")
        elif k < len(initial_blues) - 1:
            new_name = f"{current_index}.1.png"
            log(f"ℹ️ {f.name} -> {new_name} (Initial Blue)")
        else:
            current_index += 1
            new_name = f"{current_index}.png"
            log(f"ℹ️ {f.name} -> {new_name} (Last Initial Blue)")
        renames.append((f, input_dir / new_name))

    last_color_index = current_index  # index of the last detected color
    sub_index = 0
    prev_color = None

    # -------- REST OF THE PROCESS --------
    for j in range(i, len(files)):
        if progress_callback and total_files > 0:
            progress_callback(0.2 + 0.7 * (j - i + 1) / (len(files) - i) if len(files) > i else 0.9)
        file = files[j]
        color = detect_color(file)

        if color:
            if color == "Opaque Blue" and prev_color == "Opaque Blue":
                new_name = f"{last_color_index}.1.png"
            else:
                current_index += 1
                new_name = f"{current_index}.png"
                last_color_index = current_index
                sub_index = 0
        else:
            sub_index += 1
            new_name = f"{last_color_index}.{sub_index}.png"

        renames.append((file, input_dir / new_name))
        log(f"ℹ️ {file.name} -> {new_name} ({'NO color' if not color else color})")
        prev_color = color

    # -------- RENAME WITH DELAY --------
    for idx, (old, new) in enumerate(renames):
        if progress_callback and len(renames) > 0:
            progress_callback(0.9 + 0.1 * (idx + 1) / len(renames))
        if old != new:
            old.rename(new)
            time.sleep(0.2)

    if progress_callback:
        progress_callback(1.0)

    log(f"✅ Process finished, renamed {len(renames)} images.")