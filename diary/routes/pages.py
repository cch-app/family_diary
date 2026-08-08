"""Timeline, entry detail, archive, milestone, family, and tag pages."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from diary.content.repository import ContentRepository, get_repository
from diary.pagination import paginate, resolve_page_size
from diary.templating import templates

router = APIRouter()

CACHE_CONTROL = "public, max-age=60, s-maxage=300, stale-while-revalidate=86400"


def set_cache_headers(response: Response) -> None:
    """Set on the response object actually being returned, not an injected placeholder.

    FastAPI's injected `response: Response` param is only merged onto the final
    response when the handler returns a plain value FastAPI itself serializes;
    a `TemplateResponse` returned directly is an independent object, so headers
    must be set on it explicitly.
    """
    response.headers["Cache-Control"] = CACHE_CONTROL


@router.get("/")
def timeline(
    request: Request,
    page: int = 1,
    page_size: int | None = None,
    repo: ContentRepository = Depends(get_repository),
):
    entries_page = paginate(repo.published_entries, page, resolve_page_size(page_size))
    response = templates.TemplateResponse(
        request,
        "index.html",
        {"entries_page": entries_page, "all_tags": repo.all_tags(), "title": "Family Diary"},
    )
    set_cache_headers(response)
    return response


@router.get("/about")
def about(request: Request):
    response = templates.TemplateResponse(request, "about.html", {"title": "About"})
    set_cache_headers(response)
    return response


@router.get("/entries/{slug}")
def entry_detail(
    slug: str,
    request: Request,
    repo: ContentRepository = Depends(get_repository),
):
    entry = repo.get_by_slug(slug)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    response = templates.TemplateResponse(
        request, "entry.html", {"entry": entry, "title": entry.frontmatter.title}
    )
    set_cache_headers(response)
    return response


@router.get("/milestones")
def milestones(
    request: Request,
    page: int = 1,
    page_size: int | None = None,
    repo: ContentRepository = Depends(get_repository),
):
    entries_page = paginate(repo.milestones(), page, resolve_page_size(page_size))
    response = templates.TemplateResponse(
        request,
        "milestones.html",
        {"entries_page": entries_page, "title": "Milestones"},
    )
    set_cache_headers(response)
    return response


@router.get("/archive/{year}")
def archive_year(
    year: int,
    request: Request,
    page: int = 1,
    page_size: int | None = None,
    repo: ContentRepository = Depends(get_repository),
):
    results = repo.by_year_month_day(year)
    entries_page = paginate(results, page, resolve_page_size(page_size))
    response = templates.TemplateResponse(
        request,
        "archive.html",
        {"entries_page": entries_page, "title": f"Archive: {year}", "heading": str(year)},
    )
    set_cache_headers(response)
    return response


@router.get("/archive/{year}/{month}")
def archive_month(
    year: int,
    month: int,
    request: Request,
    page: int = 1,
    page_size: int | None = None,
    repo: ContentRepository = Depends(get_repository),
):
    results = repo.by_year_month_day(year, month)
    entries_page = paginate(results, page, resolve_page_size(page_size))
    response = templates.TemplateResponse(
        request,
        "archive.html",
        {
            "entries_page": entries_page,
            "title": f"Archive: {year}-{month:02d}",
            "heading": f"{year}-{month:02d}",
        },
    )
    set_cache_headers(response)
    return response


@router.get("/archive/{year}/{month}/{day}")
def archive_day(
    year: int,
    month: int,
    day: int,
    request: Request,
    page: int = 1,
    page_size: int | None = None,
    repo: ContentRepository = Depends(get_repository),
):
    results = repo.by_year_month_day(year, month, day)
    entries_page = paginate(results, page, resolve_page_size(page_size))
    response = templates.TemplateResponse(
        request,
        "archive.html",
        {
            "entries_page": entries_page,
            "title": f"Archive: {year}-{month:02d}-{day:02d}",
            "heading": f"{year}-{month:02d}-{day:02d}",
        },
    )
    set_cache_headers(response)
    return response


@router.get("/family/{label}")
def family_member_entries(
    label: str,
    request: Request,
    page: int = 1,
    page_size: int | None = None,
    repo: ContentRepository = Depends(get_repository),
):
    results = repo.filter(family_member=label)
    entries_page = paginate(results, page, resolve_page_size(page_size))
    response = templates.TemplateResponse(
        request,
        "archive.html",
        {"entries_page": entries_page, "title": f"Family: {label}", "heading": label},
    )
    set_cache_headers(response)
    return response


@router.get("/tags/{tag}")
def tag_entries(
    tag: str,
    request: Request,
    page: int = 1,
    page_size: int | None = None,
    repo: ContentRepository = Depends(get_repository),
):
    results = repo.filter(tag=tag)
    entries_page = paginate(results, page, resolve_page_size(page_size))
    response = templates.TemplateResponse(
        request,
        "archive.html",
        {"entries_page": entries_page, "title": f"Tag: {tag}", "heading": f"#{tag}"},
    )
    set_cache_headers(response)
    return response
