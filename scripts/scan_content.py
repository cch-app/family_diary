#!/usr/bin/env python3
"""Content safety-gate CLI.

Scans every entry under a content directory for credentials/secrets and
personal information. Exits non-zero if any entry destined for
approved/published status has a blocking finding, making this script
(and the pytest integration test that calls the same function) the
pre-deploy publication gate.

Usage: uv run python scripts/scan_content.py [content_dir]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from diary.safety.scanner import ScanReport, scan_all_entries


def print_report_table(reports: list[ScanReport]) -> None:
    for report in reports:
        status = "BLOCKED" if report.blocking else "ok"
        print(f"[{status}] {report.file_path}")
        for finding in report.findings:
            print(
                f"    - ({finding.severity.value}) {finding.code} @ {finding.location}: "
                f"{finding.message} :: {finding.excerpt}"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan diary content for secrets and PII.")
    parser.add_argument(
        "content_dir",
        nargs="?",
        default="content",
        help="Path to the content directory (default: content)",
    )
    args = parser.parse_args(argv)

    reports = scan_all_entries(Path(args.content_dir))
    print_report_table(reports)

    blocking = [r for r in reports if r.blocking]
    if blocking:
        print(f"\nBLOCKED: {len(blocking)} entr{'y' if len(blocking) == 1 else 'ies'} "
              f"failed the safety gate.")
        return 1

    print(f"\nOK: {len(reports)} entries scanned, no blocking findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
