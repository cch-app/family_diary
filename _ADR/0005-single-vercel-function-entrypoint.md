# 0005: Single Vercel serverless function with catch-all routing

## Status

Accepted

## Context

Vercel's Python runtime can deploy either one function per route file under `api/`,
or a single function handling all routes via a catch-all rewrite. The app has a
single `ContentRepository` singleton built once per warm process
(see [0003](./0003-in-memory-content-repository.md)) and a shared `Jinja2Templates`
instance.

## Decision

Deploy as one function, `api/index.py`, which imports the FastAPI `app` from
`diary.main`. `vercel.json` routes every path to it via a catch-all rewrite:

```json
{
  "framework": null,
  "functions": { "api/index.py": { "includeFiles": "{content,diary/templates}/**" } },
  "rewrites": [{ "source": "/(.*)", "destination": "/api/index" }]
}
```

`framework: null` forces Vercel's Framework Preset to "Other". Without it, Vercel
auto-detects "FastAPI" (it scans `pyproject.toml`/`requirements.txt` for the string
`fastapi`) and applies that framework's own zero-config `defaultRoutes`, which
conflicts with this project's explicit `rewrites`-to-`api/index.py` catch-all —
every request ends up unmatched by FastAPI's router and falls through to this
app's own 404 handler, even for routes that exist (e.g. `/`). Setting `framework:
null` makes this `vercel.json` the sole source of routing truth, matching the
single-function architecture this ADR decided on.

`includeFiles` bundles `content/` and `diary/templates/`, non-code assets not
picked up by Vercel's import-graph analysis. `public/` is deliberately **not**
included here: Vercel's Python builder always excludes `public/**` from the
function bundle and serves it directly off its own CDN instead (filesystem
routes are checked before the catch-all rewrite reaches the function), so
`public/static/css/style.css` is already served at `/static/css/style.css`
with no code involved. `diary/main.py` only mounts `/static` via
`StaticFiles` when `public/static` exists on disk (true locally and in
Docker, false on Vercel) — an earlier version mounted it unconditionally,
which crashed the whole app on import on Vercel since the directory is never
present there.

`.vercelignore` separately excludes `.venv/`, `tests/`, `backups/`, and
`content/denylists/*.yaml` from ever being uploaded, as defense in depth alongside
`.gitignore` in case of a non-git-based deploy path.

## Consequences

- One `ContentRepository` build per cold start serves every route, rather than each
  route's function needing to rebuild its own copy.
- All routes share one process's memory and `lru_cache`d dependencies, so behavior
  matches local `uvicorn` runs closely (fewer surprises from multi-function
  fan-out).
- Every route pays the cold-start cost of loading and indexing all of `content/`,
  which is fine at diary scale but would need revisiting if the function grows to
  handle write traffic or much larger content volumes.
