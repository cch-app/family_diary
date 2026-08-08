# 0006: Docker Compose for local dev only; Vercel remains the deploy target

## Status

Accepted

## Context

A `Dockerfile` and `docker-compose.yml` were added so contributors without `uv`
installed locally (or who prefer a containerized workflow) can run the app the same
way regardless of host OS. This is separate from the question of where the app is
*deployed* — see [0001](./0001-fastapi-server-rendered-on-vercel.md).

## Decision

`docker-compose.yml` builds the app from a `python:3.13-slim` base image using `uv`
for dependency installation, runs `uvicorn` with `--reload`, and bind-mounts
`content/`, `diary/`, and `public/` for live editing. This is documented and used
for **local development only**. Production deployment continues to target Vercel
serverless functions per ADR 0001/0005; Docker is not a second deployment target
and the two setups are not required to stay in lockstep beyond both running the same
`diary.main:app` ASGI application.

## Consequences

- Contributors can run `docker compose up` as an alternative to `uv venv && uv sync`
  without needing `uv` on the host.
- The Docker image intentionally does not attempt to replicate Vercel's serverless
  runtime (cold starts, single-function routing, `includeFiles` bundling) — it's a
  convenience wrapper around the same app, not a staging environment for Vercel
  behavior. `vercel dev` remains the way to validate Vercel-specific behavior.
- `.dockerignore` excludes `_ADR/`, `tests/`, `backups/`, and local denylist YAML
  files from the build context, matching the same sensitivity boundaries as
  `.gitignore`/`.vercelignore`.
