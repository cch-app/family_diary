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
  "functions": { "api/index.py": { "includeFiles": "{content,diary/templates,public}/**" } },
  "rewrites": [{ "source": "/(.*)", "destination": "/api/index" }]
}
```

`includeFiles` explicitly bundles `content/`, `diary/templates/`, and `public/`,
since these are non-code assets not picked up by Vercel's import-graph analysis.
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
