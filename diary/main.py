"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from diary.config import PROJECT_ROOT
from diary.routes import export, health, media, pages, search
from diary.templating import templates

app = FastAPI(title="Family Diary")

app.mount(
    "/static", StaticFiles(directory=str(PROJECT_ROOT / "public" / "static")), name="static"
)

app.include_router(pages.router)
app.include_router(search.router)
app.include_router(media.router)
app.include_router(export.router)
app.include_router(health.router)


@app.exception_handler(404)
async def not_found(request: Request, exc) -> HTMLResponse:
    return templates.TemplateResponse(request, "404.html", {"title": "Not Found"}, status_code=404)
