# 0002: Two-layer Markdown sanitization (markdown-it-py + nh3)

## Status

Accepted

## Context

Diary entries are authored as Markdown and rendered to HTML for public visitors.
`BUSINESS_REQUIREMENTS.md` requires Markdown rendering to be safe and to not allow
unsafe scripts or uncontrolled HTML injection. A single point of failure in the
rendering pipeline (e.g. relying only on the Markdown parser's own HTML handling)
would be a direct XSS risk against every visitor.

## Decision

Use two independent defenses in `diary/content/markdown_renderer.py`:

1. `markdown-it-py` parses Markdown with `html=False`, so any raw HTML written in an
   entry's source is escaped rather than passed through.
2. The resulting HTML is then sanitized with `nh3` (a Rust/`ammonia`-based sanitizer)
   against a strict tag/attribute allowlist, stripping `javascript:`/`data:` URIs.
   `nh3` was chosen over `bleach`, which is unmaintained.

Only the sanitized `body_html` field is ever rendered with Jinja2's `| safe` filter;
every other field (title, tags, author_label, excerpt) stays auto-escaped.

## Consequences

- A bug or gap in either layer alone doesn't automatically produce an XSS
  vulnerability — the other layer still blocks it.
- Entry authors cannot embed arbitrary HTML/JS even intentionally, which is
  acceptable since entries are meant to be plain Markdown, not custom HTML.
- Any future addition of a template field to the "rendered as safe HTML" list must
  go through the same sanitization path, not be added ad hoc.
