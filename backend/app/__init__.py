"""Application factory and API configuration for the molecule backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .storage import MoleculeStore, create_store

FRONTEND_ORIGIN = "http://localhost:5173"


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance."""

    app = FastAPI(title="Molecule Visualizer API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_ORIGIN],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    register_routes(app)

    app.state.molecule_store = create_store()

    return app


def register_routes(app: FastAPI) -> None:
    """Attach API routes to the supplied application instance."""

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}


app = create_app()

__all__ = ["MoleculeStore", "create_app", "app"]
