from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from diary.content.repository import ContentRepository, get_repository
from diary.main import app

SAMPLE_CONTENT = Path(__file__).parent / "fixtures" / "sample_content"


@pytest.fixture
def client_factory():
    """Factory fixture: build a TestClient wired to an arbitrary content dir.

    Never touches the real project content/ directory.
    """

    def _make(content_dir: Path) -> TestClient:
        app.dependency_overrides[get_repository] = lambda: ContentRepository(content_dir)
        return TestClient(app)

    yield _make
    app.dependency_overrides.clear()


@pytest.fixture
def client(client_factory) -> TestClient:
    return client_factory(SAMPLE_CONTENT)


@pytest.fixture
def tmp_content_dir(tmp_path: Path):
    """Build a throwaway content_dir tree for tests that need custom entries."""

    def _write(
        filename: str,
        frontmatter_yaml: str,
        body: str = "Body text.",
    ) -> Path:
        entries_dir = tmp_path / "entries"
        entries_dir.mkdir(parents=True, exist_ok=True)
        path = entries_dir / filename
        path.write_text(f"---\n{frontmatter_yaml}\n---\n{body}\n", encoding="utf-8")
        return path

    _write.content_dir = tmp_path
    return _write
