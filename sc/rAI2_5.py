# rAI2_5.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re

# =========================
# MAIN
# =========================
def main(pdf_path, txt_path, log, output_dir, progress_callback=None):
    """
    pdf_path, txt_path: received from GUI (not used directly)
    log: logging callback
    output_dir: root folder where Results and tables_png folders will be created
    """

    # ✅ Always use the selected folder
    results_dir = Path(output_dir) / "Results"
    results_dir.mkdir(parents=True, exist_ok=True)

    input_file = results_dir / "Summary0.txt"
    output_file = results_dir / "Summary.txt"

    if not input_file.exists():
        log(f"⛔ {input_file} not found")
        return

    if progress_callback:
        progress_callback(0.0)

    # ... rest of the code remains the same ...


    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if progress_callback:
        progress_callback(0.1)

    host_pattern = re.compile(r'^Host\s+')
    vuln_pattern = re.compile(r'^The following vulnerability is named NVT: (.+)')
    described_pattern = re.compile(r'^This vulnerability has already been described previously\.$')

    output_lines = []
    vulns_in_host = set()
    current_host = None
    total_lines = len(lines)

    i = 0
    while i < len(lines):
        if progress_callback and total_lines > 0:
            progress_callback(0.1 + 0.8 * i / total_lines)
        line = lines[i]

        # Detect new host
        if host_pattern.match(line):
            current_host = line.strip()
            vulns_in_host = set()  # reset vulnerabilities set per host
            output_lines.append(line)
            i += 1
            continue

        # Detect vulnerability
        m = vuln_pattern.match(line)
        if m:
            vuln_name = m.group(1).strip()
            if vuln_name in vulns_in_host:
                # Repeated in this host → skip this line and the next if applicable
                i += 1
                if i < len(lines) and described_pattern.match(lines[i].strip()):
                    i += 1
                if i < len(lines) and lines[i].strip() == "":
                    i += 1
                continue
            else:
                vulns_in_host.add(vuln_name)
                output_lines.append(line)
                i += 1
                continue

        # Copy any other normal line
        output_lines.append(line)
        i += 1

    if progress_callback:
        progress_callback(0.95)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    if progress_callback:
        progress_callback(1.0)

    log(f"✅ Clean summary saved in {output_file}")