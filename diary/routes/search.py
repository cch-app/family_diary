"""Search and filter route."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request

from diary.content.repository import ContentRepository, get_repository
from diary.pagination import paginate, resolve_page_size
from diary.routes.pages import set_cache_headers
from diary.templating import templates

router = APIRouter()


@router.get("/search")
def search(
    request: Request,
    q: str | None = None,
    family_member: str | None = None,
    tag: str | None = None,
    milestone: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int | None = None,
    repo: ContentRepository = Depends(get_repository),
):
    has_filters = any([q, family_member, tag, milestone is not None, date_from, date_to])
    results = (
        repo.filter(
            family_member=family_member,
            tag=tag,
            milestone=milestone,
            date_from=date_from,
            date_to=date_to,
            query=q,
        )
        if has_filters
        else []
    )
    entries_page = paginate(results, page, resolve_page_size(page_size))
    response = templates.TemplateResponse(
        request,
        "search.html",
        {
            "entries_page": entries_page,
            "title": "Search",
            "has_filters": has_filters,
            "query": q or "",
            "family_member": family_member or "",
            "tag": tag or "",
            "milestone": milestone,
            "date_from": date_from,
            "date_to": date_to,
            "all_tags": repo.all_tags(),
            "family_members": repo.family_members,
        },
    )
    set_cache_headers(response)
    return response
