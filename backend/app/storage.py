"""In-memory persistence utilities for molecule data."""

from __future__ import annotations

from typing import Dict
from uuid import UUID

from .models import MoleculeData

MoleculeStore = Dict[UUID, MoleculeData]


def create_store() -> MoleculeStore:
    """Return a fresh in-memory molecule store."""

    return {}

