"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from diary.config import PROJECT_ROOT
from diary.routes import export, health, media, pages, search
from diary.templating import templates

app = FastAPI(title="Family Diary")

# On Vercel, files under public/ are served directly by the platform's CDN
# (see ADR 0005) and are never bundled into this function, so the directory
# doesn't exist at runtime there. Mounting is local/Docker-dev only.
_static_dir = PROJECT_ROOT / "public" / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

app.include_router(pages.router)
app.include_router(search.router)
app.include_router(media.router)
app.include_router(export.router)
app.include_router(health.router)


@app.exception_handler(404)
async def not_found(request: Request, exc) -> HTMLResponse:
    return templates.TemplateResponse(request, "404.html", {"title": "Not Found"}, status_code=404)
