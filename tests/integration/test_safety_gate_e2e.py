"""The actual pre-deploy publication gate.

Running this test is equivalent to running `uv run python scripts/scan_content.py`
against the real content/ directory -- CI failing here is what blocks a bad
publish.
"""

import subprocess
import sys
from pathlib import Path

from diary.safety.scanner import scan_all_entries

PROJECT_ROOT = Path(__file__).parent.parent.parent
REAL_CONTENT_DIR = PROJECT_ROOT / "content"
FIXTURES_WITH_SECRET = PROJECT_ROOT / "tests" / "fixtures" / "sample_entries"


class TestRealContentHasNoBlockingFindings:
    def test_real_content_directory_passes_the_safety_gate(self):
        reports = scan_all_entries(REAL_CONTENT_DIR)
        blocking = [r for r in reports if r.blocking]
        assert blocking == [], f"Blocking findings in real content: {blocking}"


class TestScanContentCli:
    def _run_cli(self, content_dir: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "scan_content.py"), str(content_dir)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_exits_zero_on_clean_content(self):
        result = self._run_cli(PROJECT_ROOT / "tests" / "fixtures" / "sample_content")
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_exits_nonzero_on_fixture_with_blocking_secret(self, tmp_path):
        entries_dir = tmp_path / "entries"
        entries_dir.mkdir()
        secret_entry = FIXTURES_WITH_SECRET / "entry_with_secret.md"
        (entries_dir / secret_entry.name).write_text(
            secret_entry.read_text(encoding="utf-8"), encoding="utf-8"
        )
        result = self._run_cli(tmp_path)
        assert result.returncode == 1
        assert "BLOCKED" in result.stdout
