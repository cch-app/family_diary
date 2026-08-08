# 0001: FastAPI + server-rendered Jinja2 on Vercel serverless functions

## Status

Accepted

## Context

`BUSINESS_REQUIREMENTS.md` calls for a publicly readable diary with dynamic
search/filter (by keyword, date range, family member, tag, milestone), pagination,
and content that should be "statically renderable where practical" for performance,
deployed to Vercel. Two broad architectures were considered: a static-site generator
(pre-rendering pages at build time) vs. a small server-rendered app.

## Decision

Build the app as FastAPI, server-rendering HTML with Jinja2 templates, and deploy it
as a Python serverless function on Vercel (`api/index.py` imports the FastAPI `app`).
Every response still carries `Cache-Control` headers
(`public, max-age=60, s-maxage=300, stale-while-revalidate=86400`) so Vercel's edge
network can cache pages, giving most of the performance benefit of static rendering
without giving up dynamic routes.

## Consequences

- Search/filter/pagination work as ordinary query-param routes with no client-side
  JavaScript required.
- A single warm serverless process builds the `ContentRepository` once and reuses it
  across requests (see [0003](./0003-in-memory-content-repository.md)), rather than
  needing a rebuild-and-redeploy step for every new entry.
- Non-code assets (`content/`, `diary/templates/`, `public/`) aren't detected by
  Vercel's import-graph analysis and must be declared explicitly via
  `vercel.json`'s `includeFiles` (see
  [0005](./0005-single-vercel-function-entrypoint.md)).
- Template and static-file paths must be resolved as absolute paths anchored to
  `PROJECT_ROOT`, not CWD-relative strings, since a serverless runtime doesn't
  guarantee the process's working directory is the project root.
