class TestSearchAndFilter:
    def test_search_page_without_query_shows_no_results(self, client):
        response = client.get("/search")
        assert response.status_code == 200
        assert "First Steps" not in response.text

    def test_keyword_search_matches_title(self, client):
        response = client.get("/search?q=Picnic")
        assert response.status_code == 200
        assert "Picnic Day" in response.text
        assert "First Steps" not in response.text

    def test_keyword_search_matches_body(self, client):
        response = client.get("/search?q=bubbles")
        assert "Picnic Day" in response.text

    def test_keyword_search_no_match(self, client):
        response = client.get("/search?q=zzz-nonexistent")
        assert "No entries match" in response.text

    def test_filter_by_family_member(self, client):
        response = client.get("/search?family_member=Dad")
        assert "Picnic Day" in response.text
        assert "First Steps" not in response.text

    def test_filter_by_tag(self, client):
        response = client.get("/search?tag=walking")
        assert "First Steps" in response.text
        assert "Picnic Day" not in response.text

    def test_filter_combined_date_range_and_milestone(self, client):
        response = client.get(
            "/search?milestone=true&date_from=2026-04-01&date_to=2026-05-31"
        )
        assert "First Steps" in response.text
        assert "Picnic Day" not in response.text

    def test_search_never_returns_drafts(self, client):
        response = client.get("/search?q=unfinished")
        assert "Draft Thoughts" not in response.text
        assert "No entries match" in response.text

    def test_pagination_link_preserves_search_filters(self, client_factory, tmp_path):
        content_dir = tmp_path / "content"
        entries_dir = content_dir / "entries"
        entries_dir.mkdir(parents=True)
        for i in range(7):
            (entries_dir / f"2026-02-{i + 1:02d}-picnic-{i:02d}.md").write_text(
                "---\n"
                f'title: "Picnic {i:02d}"\n'
                f"date: 2026-02-{i + 1:02d}\n"
                'tags: ["outdoors"]\n'
                "status: published\n"
                "reviewed: true\n"
                "safety_scan:\n"
                "  passed: true\n"
                "  findings: []\n"
                "  overrides: []\n"
                "---\n"
                "We had a picnic.\n",
                encoding="utf-8",
            )
        client = client_factory(content_dir)
        response = client.get("/search?q=picnic&page_size=5")
        assert "q=picnic" in response.text
        assert "page_size=5" in response.text
