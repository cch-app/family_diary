class TestAbout:
    def test_about_returns_200(self, client):
        response = client.get("/about")
        assert response.status_code == 200
        assert "About" in response.text

    def test_about_has_cache_control_header(self, client):
        response = client.get("/about")
        assert "max-age" in response.headers.get("cache-control", "")

    def test_about_link_present_in_nav(self, client):
        response = client.get("/")
        assert 'href="/about"' in response.text
