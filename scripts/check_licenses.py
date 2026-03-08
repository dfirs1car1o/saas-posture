#!/usr/bin/env python3
"""
check_licenses.py — run pip-licenses with the same LGPL allowlist used in CI.

Usage:
    python3 scripts/check_licenses.py
"""

import json
import subprocess
import sys

# Packages with LGPL licenses explicitly approved for this repo
# (used unmodified; LGPL is acceptable for internal tooling)
LGPL_ALLOWLIST = {
    "docxtpl",  # LGPL-2.1-only; Jinja2 DOCX templating
    "fpdf2",  # LGPL-3.0-only; pure-Python PDF generation
}

result = subprocess.run(["pip-licenses", "--format=json"], capture_output=True, text=True)
if result.returncode != 0:
    print("ERROR: pip-licenses failed. Install with: pip install pip-licenses")
    sys.exit(1)

packages = json.loads(result.stdout)
blocked = [
    f"  {p['Name']} {p.get('Version', '')}: {p['License']}"
    for p in packages
    if any(x in p.get("License", "") for x in ("GPL-2", "GPL-3", "AGPL", "LGPL"))
    and p["Name"].lower() not in {a.lower() for a in LGPL_ALLOWLIST}
]

if blocked:
    print(f"FAIL: {len(blocked)} package(s) with unapproved copyleft license:")
    print("\n".join(blocked))
    sys.exit(1)

print(f"OK: all {len(packages)} package licenses approved (LGPL allowlist: {sorted(LGPL_ALLOWLIST)})")
