# 0003: In-memory content repository, singleton per process

## Status

Accepted

## Context

Entries and family members are stored as Markdown/YAML files under `content/`. The
app needs to list, filter, search, and paginate them on every request. A personal
family diary is expected to hold, realistically, tens to low thousands of entries —
not a scale that justifies a database.

## Decision

`ContentRepository` (`diary/content/repository.py`) loads and indexes all entries and
family members once, in memory, at construction. It's exposed via an `lru_cache`d
`get_repository()` FastAPI dependency, so it behaves as a singleton for the lifetime
of a warm process. Filtering, search, sorting, and pagination all operate over the
in-memory collection.

## Consequences

- Reads are fast with no I/O or query layer per request.
- New content only becomes visible after the process restarts (a new Vercel cold
  start, or a local server restart) — there's no live file-watching. Acceptable for
  a diary that's updated by editing Markdown files and redeploying, not authored
  through a live UI.
- Because `get_repository()` is `lru_cache`d, tests must use
  `app.dependency_overrides` to point it at fixture content rather than real
  `content/`; any code path that calls a *different*, non-overridden dependency
  (e.g. `get_settings()` directly instead of reading from the injected `repo`) will
  silently bypass test fixtures — this exact bug was caught and fixed in the media
  route during integration testing.
- If entry counts ever grow into the thousands, revisit with SQLite FTS5 rather than
  scaling the in-memory approach further.
