"""Shared Jinja2Templates instance, keyed off an absolute path.

Using a path relative to this module's own location (rather than a bare
"diary/templates" string, which resolves against the process working
directory) keeps template lookup correct regardless of the CWD a given
deployment environment happens to launch the process from.
"""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import Request
from fastapi.templating import Jinja2Templates

from diary.config import PROJECT_ROOT
from diary.pagination import ALLOWED_PAGE_SIZES

templates = Jinja2Templates(directory=str(PROJECT_ROOT / "diary" / "templates"))
templates.env.globals["page_size_options"] = ALLOWED_PAGE_SIZES


def extra_query_string(request: Request) -> str:
    """The current query string minus page/page_size, for pagination links.

    Keeps filters (search keyword, family member, tag, date range, ...) intact
    when a visitor changes page or page size, e.g. "q=park&tag=fun&".
    """
    pairs = [
        (k, v) for k, v in request.query_params.multi_items() if k not in ("page", "page_size")
    ]
    return f"{urlencode(pairs)}&" if pairs else ""


templates.env.globals["extra_query_string"] = extra_query_string
