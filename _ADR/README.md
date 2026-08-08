# Architecture Decision Records

This folder records the significant design decisions made while building Family
Diary, why they were made, and what tradeoffs they accepted. Each ADR is numbered
sequentially and, once accepted, is treated as immutable — a changed decision gets a
new ADR that supersedes the old one rather than an edit in place.

| # | Title | Status |
| --- | --- | --- |
| [0001](./0001-fastapi-server-rendered-on-vercel.md) | FastAPI + server-rendered Jinja2 on Vercel serverless functions | Accepted |
| [0002](./0002-two-layer-markdown-sanitization.md) | Two-layer Markdown sanitization (markdown-it-py + nh3) | Accepted |
| [0003](./0003-in-memory-content-repository.md) | In-memory content repository, singleton per process | Accepted |
| [0004](./0004-content-safety-gate.md) | Publication safety gate independent of the scan CLI | Accepted |
| [0005](./0005-single-vercel-function-entrypoint.md) | Single Vercel serverless function with catch-all routing | Accepted |
| [0006](./0006-docker-compose-for-local-dev-only.md) | Docker Compose for local dev only; Vercel remains the deploy target | Accepted |
