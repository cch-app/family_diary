"""Safe Markdown -> HTML rendering with two independent XSS defenses.

1. markdown-it-py is configured with html=False, so any raw HTML written in
   the Markdown source is escaped as text rather than emitted as a tag.
2. nh3 (Rust/ammonia-based, actively maintained) sanitizes the resulting
   HTML against a strict tag/attribute/URL-scheme allowlist as an
   independent second gate.
"""

from __future__ import annotations

import nh3
from markdown_it import MarkdownIt

_MD = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])

ALLOWED_TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "a",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "hr",
    "s",
}

ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title", "width", "height"},
}

ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


def render_markdown_safe(markdown_text: str) -> str:
    """Render Markdown to sanitized, XSS-safe HTML."""
    raw_html = _MD.render(markdown_text)
    return nh3.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="noopener noreferrer nofollow",
    )
