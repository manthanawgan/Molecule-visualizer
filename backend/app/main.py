"""ASGI entrypoint used by Uvicorn."""

from __future__ import annotations

from . import create_app

app = create_app()

__all__ = ["app"]
