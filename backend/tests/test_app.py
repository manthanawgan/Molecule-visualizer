from __future__ import annotations

from typing import Any

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from backend.app import FRONTEND_ORIGIN, app, create_app
from backend.app.models import Atom, Bond, MoleculeData, MoleculeMetadata, MoleculePayload


def test_health_route_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_factory_configures_cors_for_frontend_origin() -> None:
    new_app = create_app()

    cors_middleware = next(
        (middleware for middleware in new_app.user_middleware if middleware.cls is CORSMiddleware),
        None,
    )

    assert cors_middleware is not None
    assert cors_middleware.options["allow_origins"] == [FRONTEND_ORIGIN]


def test_app_initialises_empty_molecule_store() -> None:
    new_app = create_app()
    assert hasattr(new_app.state, "molecule_store")
    assert new_app.state.molecule_store == {}


def test_models_support_round_trip_serialisation() -> None:
    metadata = MoleculeMetadata(name="Water", formula="H2O")
    payload = MoleculePayload(
        metadata=metadata,
        atoms=[
            Atom(id=0, element="O", x=0.0, y=0.0, z=0.0),
            Atom(id=1, element="H", x=0.95, y=0.0, z=0.0),
            Atom(id=2, element="H", x=-0.95, y=0.0, z=0.0),
        ],
        bonds=[
            Bond(id=0, atom1_id=0, atom2_id=1, order=1),
            Bond(id=1, atom1_id=0, atom2_id=2, order=1),
        ],
    )

    stored = MoleculeData(**payload.model_dump())

    serialised: dict[str, Any] = stored.model_dump()
    assert serialised["metadata"]["name"] == "Water"
    assert len(serialised["atoms"]) == 3
    assert serialised["bonds"][0]["atom1_id"] == 0
