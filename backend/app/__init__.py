"""Aliased ASGI entrypoint for deployment."""

from __future__ import annotations

from . import create_app

app = create_app()

__all__ = ["app"]
