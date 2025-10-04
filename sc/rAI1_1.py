# rAI1_1.py
# -*- coding: utf-8 -*-

import re
import time
from pathlib import Path
from PIL import Image
import numpy as np

# =========================
# Reference colors
# =========================
SKY_BLUE = (135, 186, 218)
OPAQUE_BLUE = (136, 195, 255)
YELLOW_ORANGE = (247, 158, 49)
RED = (202, 29, 23)

# Tolerances
TOL_SKY_BLUE = 10
TOL_STOP = 10

DELAY = 0.2  # seconds

# =========================
# Color utilities
# =========================

def contains_color(img_path, color_ref, tol):
    try:
        img = Image.open(img_path).convert("RGB")
        arr = np.array(img)
        diff = np.abs(arr - np.array(color_ref))
        dist = np.sqrt(np.sum(diff ** 2, axis=2))
        mask = dist < tol
        if np.any(mask):
            mean_color = tuple(np.mean(arr[mask], axis=0).astype(int))
            return True, mean_color
        return False, None
    except Exception:
        return False, None

def is_sky_blue(p):
    ok, _ = contains_color(p, SKY_BLUE, TOL_SKY_BLUE)
    return ok

def is_opaque_blue(p):
    ok, _ = contains_color(p, OPAQUE_BLUE, TOL_STOP)
    return ok

def is_yellow(p):
    ok, _ = contains_color(p, YELLOW_ORANGE, TOL_STOP)
    return ok

def is_red(p):
    ok, _ = contains_color(p, RED, TOL_STOP)
    return ok

def is_stop_any(p):
    return is_opaque_blue(p) or is_yellow(p) or is_red(p)

def is_stop_yellow_or_red(p):
    return is_yellow(p) or is_red(p)

# =========================
# Misc utilities
# =========================

def sort_files(files):
    def key_func(f):
        m = re.search(r"(\d+)", f.stem)
        return int(m.group(1)) if m else 0
    return sorted(files, key=key_func)

def renumber(input_dir, log):
    files = sort_files(list(input_dir.glob("*.png")))
    for idx, file in enumerate(files, start=1):
        new_name = input_dir / f"{idx}.png"
        if file != new_name:
            file.rename(new_name)
    log(f"✅ Renumbered {len(files)} images.")
    return sort_files(list(input_dir.glob("*.png")))

def initial_aop_block_length(files, log):
    k = 0
    while k < len(files) and is_opaque_blue(files[k]):
        time.sleep(DELAY)
        log(f"✅ Preserved {files[k].name} (Initial Opaque Blue)")
        k += 1
    return k

# =========================
# MAIN
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
    total_files = len(files)
    deleted = 0
    checked = 0
    
    # Helper to report progress
    def report_progress(current, total, phase_weight, phase_offset):
        if progress_callback and total > 0:
            phase_progress = (current / total) * phase_weight
            progress_callback(phase_offset + phase_progress)

    # 1) Initial AOP block (5% of progress)
    if progress_callback:
        progress_callback(0.0)
    prefix_len = initial_aop_block_length(files, log)
    if progress_callback:
        progress_callback(0.05)

    # 2) First pass (deletion from Sky Blue until STOP) - 50% of progress
    i = prefix_len
    pass1_total = total_files - prefix_len
    pass1_current = 0
    while i < len(files):
        f = files[i]
        checked += 1
        pass1_current += 1
        report_progress(pass1_current, pass1_total, 0.5, 0.05)
        time.sleep(DELAY)

        if is_sky_blue(f):
            log(f"ℹ️ Deleted {f.name}")
            try:
                f.unlink()
                deleted += 1
            except FileNotFoundError:
                pass

            j = i + 1
            while j < len(files):
                g = files[j]
                time.sleep(DELAY)

                if is_opaque_blue(g):
                    run_start = j
                    run_end = j
                    while run_end + 1 < len(files) and is_opaque_blue(files[run_end + 1]):
                        time.sleep(DELAY)
                        run_end += 1
                    next_idx = run_end + 1
                    if next_idx < len(files) and is_stop_yellow_or_red(files[next_idx]):
                        log(f"ℹ️ Detected ({files[run_start].name}..{files[run_end].name}) "
                            f"followed by Yellow/Red ({files[next_idx].name}).")
                        break
                    else:
                        for k in range(run_start, run_end + 1):
                            time.sleep(DELAY)
                            log(f"ℹ️ Deleted {files[k].name} between Sky Blue and STOP")
                            try:
                                files[k].unlink()
                                deleted += 1
                            except FileNotFoundError:
                                pass
                        j = run_end + 1
                        continue

                if is_stop_any(g):
                    log(f"ℹ️ STOP at {g.name}. End of Sky Blue deletion.")
                    break

                log(f"ℹ️ Deleted {g.name} between Sky Blue and STOP")
                try:
                    g.unlink()
                    deleted += 1
                except FileNotFoundError:
                    pass
                j += 1

        i += 1

    # 3) Renumber (1st time) - 5% of progress
    if progress_callback:
        progress_callback(0.55)
    files = renumber(input_dir, log)
    if progress_callback:
        progress_callback(0.60)

    # 4) Recheck with delay - 35% of progress
    files = sort_files(list(input_dir.glob("*.png")))
    prefix_len = initial_aop_block_length(files, log)
    to_delete = []

    i = prefix_len
    n = len(files)
    recheck_total = n - prefix_len
    recheck_current = 0
    while i < n:
        recheck_current += 1
        report_progress(recheck_current, recheck_total, 0.30, 0.60)
        time.sleep(DELAY)
        if not is_opaque_blue(files[i]):
            i += 1
            continue

        run_start = i
        run_end = i
        while run_end + 1 < n and is_opaque_blue(files[run_end + 1]):
            time.sleep(DELAY)
            run_end += 1

        next_idx = run_end + 1
        if next_idx < n and is_stop_yellow_or_red(files[next_idx]):
            log(f"✅ Preserved {files[run_start].name}..{files[run_end].name} "
                f"because followed by Yellow/Red ({files[next_idx].name}).")
        else:
            if next_idx >= n:
                for k in range(run_start, run_end + 1):
                    log(f"ℹ️ Deleted (end of list) {files[k].name}")
                    to_delete.append(files[k])
            else:
                for k in range(run_start, run_end):
                    log(f"ℹ️ Deleted {files[k].name}")
                    to_delete.append(files[k])

        i = run_end + 1

    for p in dict.fromkeys(to_delete):
        time.sleep(DELAY)
        try:
            p.unlink()
            deleted += 1
            log(f"ℹ️ Deleted {p.name} (recheck)")
        except FileNotFoundError:
            pass

    # Final renumber - 5% of progress
    if progress_callback:
        progress_callback(0.90)
    files = renumber(input_dir, log)
    if progress_callback:
        progress_callback(1.0)

    log(f"✅ Process finished — Checked: {checked}, Deleted: {deleted}")