class TestTimeline:
    def test_home_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_home_lists_only_published_entries(self, client):
        response = client.get("/")
        assert "First Steps" in response.text
        assert "Picnic Day" in response.text
        assert "Draft Thoughts" not in response.text

    def test_home_reverse_chronological(self, client):
        response = client.get("/")
        picnic_pos = response.text.index("Picnic Day")
        first_steps_pos = response.text.index("First Steps")
        assert picnic_pos < first_steps_pos  # picnic (05-10) newer than first-steps (05-01)

    def test_home_has_cache_control_header(self, client):
        response = client.get("/")
        assert "max-age" in response.headers.get("cache-control", "")

    def test_home_pagination_page_param(self, client):
        response = client.get("/?page=1")
        assert response.status_code == 200


class TestArchive:
    def test_archive_by_year(self, client):
        response = client.get("/archive/2026")
        assert response.status_code == 200
        assert "First Steps" in response.text
        assert "Draft Thoughts" not in response.text

    def test_archive_by_year_month(self, client):
        response = client.get("/archive/2026/5")
        assert response.status_code == 200
        assert "First Steps" in response.text
        assert "Picnic Day" in response.text

    def test_archive_by_full_date(self, client):
        response = client.get("/archive/2026/5/1")
        assert response.status_code == 200
        assert "First Steps" in response.text
        assert "Picnic Day" not in response.text

    def test_archive_empty_year_returns_empty_state(self, client):
        response = client.get("/archive/1999")
        assert response.status_code == 200
        assert "No entries" in response.text

    def test_archive_has_cache_control_header(self, client):
        response = client.get("/archive/2026")
        assert "max-age" in response.headers.get("cache-control", "")


class TestMilestones:
    def test_milestones_only_shows_milestone_entries(self, client):
        response = client.get("/milestones")
        assert response.status_code == 200
        assert "First Steps" in response.text
        assert "Picnic Day" not in response.text


class TestFamilyAndTagPages:
    def test_family_page_filters_correctly(self, client):
        response = client.get("/family/Dad")
        assert response.status_code == 200
        assert "Picnic Day" in response.text
        assert "First Steps" not in response.text

    def test_tag_page_filters_correctly(self, client):
        response = client.get("/tags/walking")
        assert response.status_code == 200
        assert "First Steps" in response.text
        assert "Picnic Day" not in response.text


def _build_many_entries_content_dir(tmp_path, count: int):
    content_dir = tmp_path / "content"
    entries_dir = content_dir / "entries"
    entries_dir.mkdir(parents=True)
    for i in range(count):
        (entries_dir / f"2026-01-{i + 1:02d}-entry-{i:02d}.md").write_text(
            "---\n"
            f'title: "Entry {i:02d}"\n'
            f"date: 2026-01-{i + 1:02d}\n"
            "status: published\n"
            "reviewed: true\n"
            "safety_scan:\n"
            "  passed: true\n"
            "  findings: []\n"
            "  overrides: []\n"
            "---\n"
            "Body.\n",
            encoding="utf-8",
        )
    return content_dir


class TestTimelinePageSize:
    def test_default_page_size_is_five(self, client_factory, tmp_path):
        content_dir = _build_many_entries_content_dir(tmp_path, 12)
        client = client_factory(content_dir)
        response = client.get("/")
        assert response.status_code == 200
        assert response.text.count('<article class="entry-card') == 5

    def test_page_size_ten_returns_ten_items(self, client_factory, tmp_path):
        content_dir = _build_many_entries_content_dir(tmp_path, 12)
        client = client_factory(content_dir)
        response = client.get("/?page_size=10")
        assert response.text.count('<article class="entry-card') == 10

    def test_page_size_twenty_returns_all_when_fewer_than_twenty(self, client_factory, tmp_path):
        content_dir = _build_many_entries_content_dir(tmp_path, 12)
        client = client_factory(content_dir)
        response = client.get("/?page_size=20")
        assert response.text.count('<article class="entry-card') == 12

    def test_invalid_page_size_falls_back_to_default(self, client_factory, tmp_path):
        content_dir = _build_many_entries_content_dir(tmp_path, 12)
        client = client_factory(content_dir)
        response = client.get("/?page_size=7")
        assert response.text.count('<article class="entry-card') == 5

    def test_pagination_link_carries_page_size(self, client_factory, tmp_path):
        content_dir = _build_many_entries_content_dir(tmp_path, 12)
        client = client_factory(content_dir)
        response = client.get("/?page_size=10")
        assert "page_size=10" in response.text

    def test_page_size_selector_offers_five_ten_twenty(self, client_factory, tmp_path):
        content_dir = _build_many_entries_content_dir(tmp_path, 12)
        client = client_factory(content_dir)
        response = client.get("/")
        for expected in ('value="5"', 'value="10"', 'value="20"'):
            assert expected in response.text

    def test_page_size_selector_has_no_apply_button(self, client_factory, tmp_path):
        content_dir = _build_many_entries_content_dir(tmp_path, 12)
        client = client_factory(content_dir)
        response = client.get("/")
        assert ">Apply<" not in response.text
        assert 'onchange="this.form.submit()"' in response.text

    def test_pagination_shows_numbered_page_links(self, client_factory, tmp_path):
        content_dir = _build_many_entries_content_dir(tmp_path, 12)
        client = client_factory(content_dir)
        response = client.get("/?page_size=5")
        assert 'aria-current="page"' in response.text
        assert "page=2" in response.text
