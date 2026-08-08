class TestEntryDetail:
    def test_published_entry_returns_200(self, client):
        response = client.get("/entries/first-steps")
        assert response.status_code == 200
        assert "First Steps" in response.text

    def test_response_contains_no_script_tags(self, client):
        response = client.get("/entries/first-steps")
        body_start = response.text.index('class="entry-body')
        body_end = response.text.index("</div>", body_start)
        assert "<script" not in response.text[body_start:body_end]

    def test_response_has_cache_control_header(self, client):
        response = client.get("/entries/first-steps")
        assert "max-age" in response.headers.get("cache-control", "")

    def test_unknown_slug_returns_404(self, client):
        response = client.get("/entries/does-not-exist")
        assert response.status_code == 404

    def test_reviewed_safe_media_referenced_in_entry(self, client):
        response = client.get("/entries/first-steps")
        assert "/media/2026/05/first-steps.jpg" in response.text

    def test_family_and_tag_links_present(self, client):
        response = client.get("/entries/first-steps")
        assert 'href="/family/Kid A"' in response.text
        assert 'href="/tags/milestone"' in response.text
