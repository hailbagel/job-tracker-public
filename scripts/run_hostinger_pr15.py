#!/usr/bin/env python3
"""Run the checked-in PR15 Hostinger production procedure exactly once.

Invoke only from a fresh root shell after updating main. Do not retry on failure.
The Markdown runbook contains the authoritative complete procedure.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    runbook = repo / "docs" / "HOSTINGER_PR15_IMMEDIATE_PRODUCTION_RUN.md"

    if os.geteuid() != 0:
        raise SystemExit("STOP: run only from the Hostinger root terminal")

    text = runbook.read_text(encoding="utf-8")
    section_marker = "## Single bounded Hostinger command block"
    if text.count(section_marker) != 1:
        raise SystemExit("STOP: authoritative Hostinger runbook section missing or duplicated")
    section = text.split(section_marker, 1)[1]
    fence = "```bash\n"
    if fence not in section:
        raise SystemExit("STOP: runbook bash block missing")
    rest = section.split(fence, 1)[1]
    if "\n```" not in rest:
        raise SystemExit("STOP: runbook bash block not terminated")
    script = rest.split("\n```", 1)[0]

    required = (
        "=== PRECHECK SERVICE ===",
        "=== VERIFY PR15 CODE PRESENT ===",
        "HYIMPULSE CONFIG OK",
        "=== START ONE PRODUCTION RUN THROUGH SYSTEMD ===",
        "HYIMPULSE DATA QUALITY OK",
        "=== MANUAL PRODUCTION VERIFICATION COMPLETE ===",
    )
    if not all(marker in script for marker in required):
        raise SystemExit("STOP: incomplete or outdated Hostinger runbook")

    print("RUNNING: versioned Hostinger PR15 single-run procedure", flush=True)
    result = subprocess.run(
        ["bash", "-e", "-u", "-o", "pipefail"],
        input=script,
        text=True,
        cwd=repo,
        check=False,
    )
    if result.returncode:
        raise SystemExit(f"STOP: Hostinger runbook exited {result.returncode}; DO NOT RETRY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
