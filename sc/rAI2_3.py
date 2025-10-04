# rAI2_3.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from collections import defaultdict
from pathlib import Path

# =========================
# MAIN
# =========================
def main(pdf_path, txt_path, log, output_dir, progress_callback=None):
    """
    pdf_path, txt_path: received from GUI (not used directly)
    log: logging callback
    output_dir: root folder where the Results and tables_png folders will be created
    """

    # ✅ Always use the selected folder
    results_dir = Path(output_dir) / "Results"
    results_dir.mkdir(parents=True, exist_ok=True)

    input_file = results_dir / "report2.txt"
    output_file = results_dir / "summary0.txt"

    if not input_file.exists():
        log(f"⛔ {input_file} not found")
        return

    if progress_callback:
        progress_callback(0.0)

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if progress_callback:
        progress_callback(0.1)

    host_blocks = re.split(r"\nHost\s+(\d+\.\d+\.\d+\.\d+)", content)
    vuln_hosts = defaultdict(set)
    valid_hosts = set()
    described_vulns = {}
    total_hosts = len(host_blocks) // 2

    # First pass: map vulnerabilities to hosts
    for i in range(1, len(host_blocks), 2):
        if progress_callback and total_hosts > 0:
            progress_callback(0.1 + 0.4 * (i // 2 + 1) / total_hosts)
        ip = host_blocks[i].strip()
        block = host_blocks[i+1]
        vulnerabilities = re.split(r"\nIssue\s*\n-----", block)
        host_has_high = False

        for v in vulnerabilities[1:]:
            nvt_match = re.search(r"NVT:\s*(.*)", v)
            threat_match = re.search(r"Threat:\s*(.*CVSS:\s*([\d\.]+))", v)

            if not nvt_match or not threat_match:
                continue

            cvss = float(threat_match.group(2)) if threat_match else 0.0
            if cvss <= 3.9:
                continue

            host_has_high = True
            nvt = nvt_match.group(1).strip()
            vuln_hosts[nvt].add(ip)

        if host_has_high:
            valid_hosts.add(ip)

    if progress_callback:
        progress_callback(0.5)

    # Second pass: generate final summary
    output = []

    for i in range(1, len(host_blocks), 2):
        if progress_callback and total_hosts > 0:
            progress_callback(0.5 + 0.4 * (i // 2 + 1) / total_hosts)
        ip = host_blocks[i].strip()
        if ip not in valid_hosts:
            continue

        block = host_blocks[i+1]
        vulnerabilities = re.split(r"\nIssue\s*\n-----", block)

        output.append(f"Host {ip}")
        output.append("The following image shows a summary of the affected ports for this particular host.\n")

        for v in vulnerabilities[1:]:
            nvt_match = re.search(r"NVT:\s*(.*)", v)
            threat_match = re.search(r"Threat:\s*(.*CVSS:\s*([\d\.]+))", v)

            if not nvt_match or not threat_match:
                continue

            cvss = float(threat_match.group(2)) if threat_match else 0.0
            if cvss <= 3.9:
                continue

            nvt = nvt_match.group(1).strip()
            output.append(f"The following vulnerability is called NVT: {nvt} (CVSS: {cvss})")

            if nvt not in described_vulns:
                output.append("Description:")
                output.append("Impact:")
                output.append("Mitigation:\n")
                described_vulns[nvt] = True
            else:
                output.append("This vulnerability has already been described previously.\n")

    if progress_callback:
        progress_callback(0.95)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    if progress_callback:
        progress_callback(1.0)

    log(f"✅ Summary generated at: {output_file}")
