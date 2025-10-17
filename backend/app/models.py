"""Pydantic models that describe the molecule payload structure."""

from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Atom(BaseModel):
    """Representation of an atom within a molecule."""

    id: int = Field(ge=0, description="Zero-based index of the atom within the payload.")
    element: str = Field(..., min_length=1, description="Chemical symbol for the atom.")
    x: float = Field(..., description="Cartesian X coordinate in angstroms.")
    y: float = Field(..., description="Cartesian Y coordinate in angstroms.")
    z: float = Field(..., description="Cartesian Z coordinate in angstroms.")


class Bond(BaseModel):
    """Representation of a bond connecting two atoms."""

    id: int = Field(ge=0, description="Zero-based index of the bond within the payload.")
    atom1_id: int = Field(ge=0, description="Index of the first atom participating in the bond.")
    atom2_id: int = Field(ge=0, description="Index of the second atom participating in the bond.")
    order: int = Field(default=1, ge=1, le=3, description="Bond order (single, double, triple).")


class MoleculeMetadata(BaseModel):
    """Descriptive attributes associated with a molecule payload."""

    name: Optional[str] = Field(default=None, description="Human friendly molecule name.")
    formula: Optional[str] = Field(default=None, description="Empirical formula for the molecule.")
    description: Optional[str] = Field(default=None, description="Additional notes about the molecule.")


class MoleculePayload(BaseModel):
    """Full payload exchanged between the frontend and backend for a molecule."""

    atoms: list[Atom] = Field(default_factory=list, description="Atoms that make up the molecule.")
    bonds: list[Bond] = Field(default_factory=list, description="Bonds connecting atoms in the molecule.")
    metadata: Optional[MoleculeMetadata] = Field(
        default=None,
        description="Descriptive metadata fields associated with the molecule.",
    )


class MoleculeData(MoleculePayload):
    """Persisted molecule model stored on the backend."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier assigned by the backend.")

