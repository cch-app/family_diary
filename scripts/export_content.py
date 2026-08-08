#!/usr/bin/env python3
"""Maintainer-only full local backup CLI.

Unlike the public /export.json and /export.zip endpoints (which only ever
include published, reviewed-safe content), this script backs up the
*entire* content directory -- including drafts and unreviewed media -- for
local disaster recovery. It is never exposed over HTTP and writes only to
the gitignored backups/ directory.

Usage: uv run python scripts/export_content.py [content_dir] [--out backups]
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def export_full_backup(content_dir: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = out_dir / f"family-diary-backup-{timestamp}.zip"

    with zipfile.ZipFile(out_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(content_dir.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=str(path.relative_to(content_dir.parent)))

    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Full local backup of the content directory, including drafts."
    )
    parser.add_argument("content_dir", nargs="?", default="content")
    parser.add_argument("--out", default="backups")
    args = parser.parse_args(argv)

    content_dir = Path(args.content_dir)
    if not content_dir.exists():
        print(f"Content directory not found: {content_dir}", file=sys.stderr)
        return 1

    out_path = export_full_backup(content_dir, Path(args.out))
    print(f"Backup written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
