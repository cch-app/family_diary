from diary.content.markdown_renderer import render_markdown_safe


class TestSafeMarkdownRendering:
    def test_renders_basic_formatting(self):
        html = render_markdown_safe("**bold** and *italic*")
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_renders_links_and_images(self):
        html = render_markdown_safe(
            "[link](https://example.com)\n\n![alt text](https://example.com/a.jpg)"
        )
        assert 'href="https://example.com"' in html
        assert 'src="https://example.com/a.jpg"' in html
        assert 'alt="alt text"' in html

    def test_external_links_get_safe_rel(self):
        html = render_markdown_safe("[link](https://example.com)")
        assert 'rel="noopener noreferrer nofollow"' in html

    def test_raw_script_tag_in_source_is_not_executed(self):
        html = render_markdown_safe("<script>alert('xss')</script>")
        assert "<script" not in html
        assert "&lt;script&gt;" in html

    def test_raw_html_in_source_is_escaped_not_rendered(self):
        html = render_markdown_safe("<div onclick='alert(1)'>hi</div>")
        # No real <div> element is ever created, so the onclick text (kept
        # only as inert escaped characters) can never execute.
        assert "<div" not in html
        assert "&lt;div" in html

    def test_img_onerror_attribute_stripped(self):
        html = render_markdown_safe('<img src="x" onerror="alert(1)">')
        # The raw <img ...> tag is escaped to inert text, not a real element.
        assert "<img" not in html
        assert "&lt;img" in html

    def test_javascript_uri_in_link_blocked(self):
        html = render_markdown_safe("[click me](javascript:alert(1))")
        # markdown-it's link validator refuses the javascript: scheme, so no
        # <a> element is created at all (nh3's url_schemes is a second gate).
        assert "<a " not in html
        assert "href" not in html

    def test_data_uri_in_image_blocked(self):
        html = render_markdown_safe("![x](data:text/html;base64,PHNjcmlwdD4=)")
        assert "<img" not in html

    def test_disallowed_tag_stripped_but_content_kept(self):
        html = render_markdown_safe("Hello <marquee>world</marquee>")
        assert "<marquee>" not in html
        assert "world" in html

    def test_nh3_layer_independently_blocks_dangerous_url_scheme(self):
        """Defense-in-depth: nh3's url_schemes allowlist blocks a dangerous
        scheme directly, independent of markdown-it's own link validator."""
        import nh3

        from diary.content.markdown_renderer import (
            ALLOWED_ATTRS,
            ALLOWED_TAGS,
            ALLOWED_URL_SCHEMES,
        )

        raw_html = '<a href="javascript:alert(1)">click</a>'
        cleaned = nh3.clean(
            raw_html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            url_schemes=ALLOWED_URL_SCHEMES,
            link_rel="noopener noreferrer nofollow",
        )
        assert "javascript:" not in cleaned

    def test_allowed_tags_render(self):
        html = render_markdown_safe("# Heading\n\n- item one\n- item two\n\n> quote\n\n`code`")
        assert "<h1>" in html
        assert "<ul>" in html
        assert "<li>" in html
        assert "<blockquote>" in html
        assert "<code>" in html

    def test_table_extension_renders(self):
        html = render_markdown_safe("| a | b |\n| - | - |\n| 1 | 2 |")
        assert "<table>" in html

    def test_style_tag_and_content_stripped(self):
        html = render_markdown_safe("<style>body{display:none}</style>text")
        assert "<style>" not in html
        assert "text" in html
