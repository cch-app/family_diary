# Family Diary

A public, read-only, Markdown-authored diary for publishing family growth records and
everyday moments — with anonymization and credential/PII scanning built into the
publication pipeline so nothing unsafe ever reaches a public visitor. See
[`BUSINESS_REQUIREMENTS.md`](./BUSINESS_REQUIREMENTS.md) for the full product spec.

## Stack

- **Python 3.13**, managed with [`uv`](https://docs.astral.sh/uv/)
- **FastAPI**, server-rendered with Jinja2 (no JS framework, no build step)
- **markdown-it-py** + **nh3** for safe Markdown → sanitized HTML rendering
- **Pydantic v2 / pydantic-settings** for content models and config
- Deployed to **Vercel** as a single Python serverless function (`api/index.py`)

## Prerequisites

Either of the following is enough to run the app locally:

- **Native:** [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
  (installs and manages Python 3.13 itself — a separate Python install isn't
  required), `git`.
- **Docker:** [Docker](https://docs.docker.com/get-docker/) with Compose v2
  (`docker compose version`) — no local Python or `uv` install needed.

Deploying (optional, maintainer-only) additionally requires a
[Vercel](https://vercel.com) account and the `vercel` CLI.

## Project layout

```
diary/            FastAPI app package
  models/          entry, media, family member, review-status models
  content/          Markdown loader, safe renderer, in-memory ContentRepository
  safety/           credential/PII scanner + regex patterns
  routes/           pages, search, media, export, health
  templates/        Jinja2 templates
  main.py           FastAPI app instance
  templating.py     shared Jinja2Templates instance (absolute-path based)
  config.py         Settings (content_dir, ...)
  pagination.py     Page dataclass + selectable page-size options (5/10/20, default 5)
content/           real diary content (entries, media, family_members.yaml)
  denylists/        local-only real-name/school/workplace lists (gitignored)
public/static/     CSS, served directly
scripts/           scan_content.py (safety gate CLI), export_content.py (backup CLI)
tests/             unit/ and integration/ test suites
api/index.py       Vercel entrypoint
vercel.json / .vercelignore   Vercel deployment config
Dockerfile / docker-compose.yml   local dev container (not the deploy target)
_ADR/              architecture decision records
```

## Setup

```bash
uv venv --python 3.13
uv sync
```

This installs runtime and dev dependencies (FastAPI, pytest, ruff, etc.) into `.venv/`,
matching the versions pinned in `uv.lock`.

## Running locally

```bash
uv run uvicorn diary.main:app --reload
```

Visit `http://127.0.0.1:8000/`. Routes:

| Path | Description |
| --- | --- |
| `/` | Paginated timeline of published entries |
| `/entries/{slug}` | Entry detail page |
| `/archive/{year}[/{month}[/{day}]]` | Browse by date |
| `/milestones` | Milestone entries only |
| `/family/{label}` | Entries for one anonymized family member |
| `/tags/{tag}` | Entries with a given tag |
| `/search` | Keyword + filter search (works without JS) |
| `/media/{path}` | Reviewed-safe media files only |
| `/export.json`, `/export.zip` | Published-only content export |
| `/healthz` | Health check |

## Running locally with Docker

An alternative to the native `uv` setup above — no local Python or `uv` install
needed:

```bash
docker compose up --build
```

Visit `http://127.0.0.1:8000/`. The container runs `uvicorn --reload`, and
`content/`, `diary/`, and `public/` are bind-mounted, so edits on the host are
picked up without rebuilding the image. This is a local development convenience
only — the deployment target remains Vercel (see [Deployment](#deployment) and
[`_ADR/0006`](./_ADR/0006-docker-compose-for-local-dev-only.md)).

## Testing and linting

```bash
uv run pytest                    # unit + integration suite
uv run ruff check .              # lint
```

The integration suite includes a safety-gate end-to-end test that runs the scanner
against the real `content/` directory, so a green `pytest` run is itself a pre-deploy
safety gate.

## Content safety pipeline

Every entry's `frontmatter.status` must be `published`, `reviewed: true`, and
`safety_scan.passed: true` before it is visible on any public route — this is checked
directly in code (`DiaryEntry.is_public`), independent of whether the CLI below was
ever run, so a bad frontmatter combination can never leak.

Before publishing new content, run the scanner:

```bash
uv run python scripts/scan_content.py
```

It checks entry text, frontmatter, links, and media alt text/captions for credentials,
API keys, emails, phone numbers, and other PII patterns, and exits non-zero if a
blocking finding exists on an `approved`/`published` entry. Optional local-only
denylists for real names and school/workplace names can be added at
`content/denylists/real_names.yaml` and `content/denylists/school_workplace.yaml` (see
[`content/denylists/README.md`](./content/denylists/README.md) for the format) — these
files are gitignored and never deployed.

## Backups

```bash
uv run python scripts/export_content.py
```

Writes a full local zip backup (including drafts) to the gitignored `backups/`
directory. This is separate from the public `/export.json` and `/export.zip` routes,
which only ever include published, reviewed-safe content.

## Deployment

The app deploys to Vercel as a single Python serverless function. `vercel.json` routes
all paths to `api/index.py`, which imports the FastAPI `app` from `diary.main`, and
declares `includeFiles` for `content/`, `diary/templates/`, and `public/` so Vercel
bundles them alongside the code. `.vercelignore` excludes `.venv/`, `tests/`,
`backups/`, and the local denylist YAML files from any deploy.

## Design decisions

Significant architecture and design decisions, with context and tradeoffs, are
recorded as ADRs in [`_ADR/`](./_ADR/README.md) — start there for the "why" behind
the server-rendered-on-Vercel architecture, the sanitization approach, the
in-memory content repository, and the publication safety gate.
