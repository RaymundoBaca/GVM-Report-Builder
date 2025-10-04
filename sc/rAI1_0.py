#rAI1_0
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pathlib import Path
import camelot
import fitz  # PyMuPDF
from collections import defaultdict

# =========================
# Utilities
# =========================

def iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter_w, inter_h = max(0, inter_x2 - inter_x1), max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    a_area = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    b_area = max(0, bx2 - bx1) * max(0, by2 - by1)
    denom = a_area + b_area - inter_area
    return inter_area / denom if denom > 0 else 0.0

def deduplicate_bboxes(boxes, iou_threshold=0.35):
    out = []
    for bb in boxes:
        if not any(bb["page"] == aa["page"] and iou(bb["bbox"], aa["bbox"]) >= iou_threshold for aa in out):
            out.append(bb)
    return out

# =========================
# Table detection
# =========================

def extract_tables(pdf_path, log):
    log("ℹ️ Detecting tables...", "info")
    try:
        tables = camelot.read_pdf(
            pdf_path,
            pages="all",
            flavor="lattice",
            line_scale=110,
            process_background=False,
            strip_text="\n"
        )
    except Exception as e:
        log(f"ℹ️ Error reading PDF: {e}")
        return []

    log(f"✅ Tables detected: {len(tables)}")

    boxes = []
    for t in tables:
        bbox = getattr(t, "_bbox", None)
        if bbox:
            try:
                page_idx = int(str(getattr(t, "page", "1")))
            except ValueError:
                page_idx = 1
            x1, y1, x2, y2 = map(float, bbox)
            boxes.append({"page": page_idx, "bbox": (x1, y1, x2, y2)})

    boxes = deduplicate_bboxes(boxes)
    return boxes

# =========================
# Export images
# =========================

def export_table_images(pdf_path, boxes, out_dir, log, dpi=200, max_area_ratio=0.97):
    if not boxes:
        log("[!] No tables to export.")
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)

    boxes.sort(key=lambda r: (r["page"], -r["bbox"][3], r["bbox"][0]))

    global_idx = 1
    for bb in boxes:
        pno = bb["page"] - 1
        if not (0 <= pno < len(doc)):
            continue

        page = doc[pno]
        page_w, page_h = page.rect.width, page.rect.height
        x1, y1, x2, y2 = bb["bbox"]

        area_box = max(0, x2 - x1) * max(0, y2 - y1)
        if area_box / (page_w * page_h) > max_area_ratio:
            continue

        clip = fitz.Rect(x1, page_h - y2, x2, page_h - y1)
        mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)

        img_path = out_dir / f"{global_idx}.png"
        pix.save(str(img_path))
        global_idx += 1

    doc.close()
    log(f"✅ Images saved in: {out_dir} (Total: {global_idx-1})")
    return global_idx > 1

# =========================
# TXT report cleaning
# =========================

def clean_report(input_file, output_file, log):
    log("ℹ️ Cleaning TXT report...")
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    def clean_field(txt):
        txt = re.sub(r"!\s*", "", txt)
        txt = re.sub(r"\n\s+", " ", txt)
        txt = re.sub(r"[ ]{2,}", " ", txt)
        txt = re.sub(r"\s+([.,;:])", r"\1", txt)
        return txt.strip()

    content = re.sub(
        r"(Summary:\n)(.*?)(\n(?:Vulnerability Detection Result|Solution:))",
        lambda m: m.group(1) + clean_field(m.group(2)) + m.group(3),
        content,
        flags=re.DOTALL
    )

    content = re.sub(
        r"(Solution:\n)(.*?)(\n(?:Vulnerability Detection Method|References:|$))",
        lambda m: m.group(1) + clean_field(m.group(2)) + m.group(3),
        content,
        flags=re.DOTALL
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    log(f"✅ Clean report generated: {output_file}")

# =========================
# MAIN
# =========================

def main(pdf_path, txt_path, log, output_dir=None, progress_callback=None):
    """
    pdf_path: PDF path
    txt_path: TXT path
    log: logging function (e.g., print or GUI callback)
    output_dir: desired results folder
    progress_callback: optional callback(float) to report progress (0.0 to 1.0)
    """
    pdf_path = Path(pdf_path)
    txt_in = Path(txt_path)

    if not pdf_path.exists():
        log(f"⛔ {pdf_path} not found")
        return
    if not txt_in.exists():
        log(f"⛔ {txt_in} not found")
        return

    # Results folder: respect output_dir if provided
    if output_dir:
        results_dir = Path(output_dir) / "Results"
    else:
        results_dir = pdf_path.parent / "Results"

    results_dir.mkdir(parents=True, exist_ok=True)

    # Output files
    txt_out = results_dir / "report2.txt"
    tables_png_dir = results_dir / "tables_png"
    tables_png_dir.mkdir(parents=True, exist_ok=True)

    # Processes
    if progress_callback:
        progress_callback(0.0)
    boxes = extract_tables(str(pdf_path), log)
    if progress_callback:
        progress_callback(0.25)
    boxes = deduplicate_bboxes(boxes, iou_threshold=0.35)
    if progress_callback:
        progress_callback(0.40)
    export_table_images(str(pdf_path), boxes, tables_png_dir, log, dpi=200, max_area_ratio=0.97)
    if progress_callback:
        progress_callback(0.80)
    clean_report(txt_in, txt_out, log)
    if progress_callback:
        progress_callback(1.0)

    log(f"✅ Process completed — everything saved in {results_dir}")
