# rAI2_1.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from collections import defaultdict
from pathlib import Path

# =========================
# Functions
# =========================
def clean_text(txt, remove_headers=True):
    """Cleans general text: line breaks, extra spaces, and unnecessary headers"""
    if not txt:
        return ""
    txt = re.sub(r"!\s*", "", txt)  
    txt = re.sub(r"\n\s+", " ", txt)  
    txt = re.sub(r"[ ]{2,}", " ", txt)  
    txt = re.sub(r"\s+([.,;:])", r"\1", txt)  

    phrases_to_remove = [
        "Please see the references for more resources supporting you with this task.",
        "Please see the references for more resources supporting you in this task."
    ]
    for phrase in phrases_to_remove:
        txt = txt.replace(phrase, "").strip()

    if remove_headers:
        headers = [
            "Vulnerability Detection Result",
            "Vulnerability Detection Method",
            "Details",
            "Solution type",
            "Affected Software/OS",
            "Vulnerability Insight"
        ]
        for header in headers:
            txt = re.sub(rf"^\s*{header}:.*(?:\n.+?)*(?=\n|$)", "", txt, flags=re.IGNORECASE | re.MULTILINE)

    return txt.strip()


def clean_solution(txt):
    """
    Keeps the actual mitigation and removes unnecessary headers:
    - Removes any line starting with 'Solution type:' (all variants).
    - Completely removes: 'Vulnerability Insight:', 'Vulnerability Detection Method:', 'Affected Software/OS:'.
    - Removes unnecessary reference comments.
    """
    if not txt:
        return ""

    # Clean line breaks and extra spaces
    txt = re.sub(r"\n\s+", " ", txt)
    txt = re.sub(r"[ ]{2,}", " ", txt)
    txt = re.sub(r"\s+([.,;:])", r"\1", txt)

    # Remove any line starting with 'Solution type:'
    txt = re.sub(r"Solution type:.*", "", txt, flags=re.IGNORECASE)

    # Cut everything after these headers if they appear
    headers_to_cut = [
        "Vulnerability Insight:",
        "Vulnerability Detection Method:",
        "Affected Software/OS:"
    ]
    for header in headers_to_cut:
        idx = txt.find(header)
        if idx != -1:
            txt = txt[:idx].strip()

    # Remove unnecessary reference comments
    references = [
        "Please see the references for more resources supporting you with this task.",
        "Please see the references for more resources supporting you in this task."
    ]
    for ref in references:
        txt = txt.replace(ref, "").strip()

    # Clean extra spaces
    txt = re.sub(r"\s{2,}", " ", txt).strip()
    return txt


# =========================
# MAIN
# =========================
def main(pdf_path, txt_path, log, output_dir, progress_callback=None):
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
        progress_callback(0.05)

    host_blocks = re.split(r"\nHost\s+(\d+\.\d+\.\d+\.\d+)", content)
    vuln_hosts = defaultdict(set)
    vuln_details = {}
    valid_hosts = set()
    
    total_hosts = len(host_blocks) // 2

    # -------------------------
    # First pass: collect info
    # -------------------------
    for i in range(1, len(host_blocks), 2):
        if progress_callback and total_hosts > 0:
            progress_callback(0.05 + 0.40 * (i // 2 + 1) / total_hosts)
        ip = host_blocks[i].strip()
        block = host_blocks[i+1]
        vulnerabilities = re.split(r"\nIssue\s*\n-----", block)
        host_has_high = False

        for v in vulnerabilities[1:]:
            nvt_match = re.search(r"NVT:\s*(.*)", v)
            threat_match = re.search(r"Threat:\s*(.*CVSS:\s*([\d\.]+))", v)
            summary_match = re.search(r"Summary:\s*(.*?)\n\n", v, re.DOTALL)
            solution_match = re.search(r"Solution:\s*(.*?)\n\n", v, re.DOTALL)
            impact_match = re.search(r"Impact:\s*(.*?)\n\n", v, re.DOTALL)

            if not nvt_match or not threat_match:
                continue

            cvss = float(threat_match.group(2)) if threat_match else 0.0
            if cvss <= 3.9:
                continue

            host_has_high = True
            nvt = nvt_match.group(1).strip()
            summary = clean_text(summary_match.group(1) if summary_match else "")
            solution = clean_solution(solution_match.group(1) if solution_match else "")
            impact = clean_text(impact_match.group(1) if impact_match else "")

            vuln_hosts[nvt].add(ip)
            if nvt not in vuln_details:
                vuln_details[nvt] = {
                    "desc": summary,
                    "mitigation": solution,
                    "impact": impact
                }

        if host_has_high:
            valid_hosts.add(ip)

    if progress_callback:
        progress_callback(0.45)

    # -------------------------
    # Second pass: generate summary
    # -------------------------
    output = []
    valid_hosts_list = list(valid_hosts)
    total_valid_hosts = len(valid_hosts_list)

    for i in range(1, len(host_blocks), 2):
        if progress_callback and total_valid_hosts > 0:
            current_valid = len([h for h in valid_hosts_list if h == host_blocks[i].strip()[:len(h)]])
            progress_callback(0.45 + 0.50 * (i // 2 + 1) / total_hosts)
        ip = host_blocks[i].strip()
        if ip not in valid_hosts:
            continue

        block = host_blocks[i+1]
        vulnerabilities = re.split(r"\nIssue\s*\n-----", block)

        output.append(f"Host {ip}")
        output.append("The following image shows a summary of the affected ports for this particular host.")

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

            other_hosts = list(vuln_hosts[nvt] - {ip})
            if vuln_details[nvt]["desc"] != "DESCRIBED" and other_hosts:
                if len(other_hosts) == 1:
                    output.append(f"The described vulnerability is also present in the following host within the network: {other_hosts}")
                else:
                    output.append(f"The described vulnerability is also present in the following hosts within the network: {other_hosts}")

            if vuln_details[nvt]["desc"] != "DESCRIBED":
                output.append(f"Description:\n{vuln_details[nvt]['desc']}")
                output.append(f"Impact:\n{vuln_details[nvt]['impact']}")
                output.append(f"Mitigation:\n{vuln_details[nvt]['mitigation']}\n")
                vuln_details[nvt]["desc"] = "DESCRIBED"
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
