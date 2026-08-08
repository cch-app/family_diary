"""Vercel Python serverless entrypoint. Imports the module-level ASGI app."""

from diary.main import app

__all__ = ["app"]
