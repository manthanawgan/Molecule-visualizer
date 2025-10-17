from __future__ import annotations

from pydantic import BaseModel, Field


class AtomCoordinates(BaseModel):
    x: float = Field(..., description="X coordinate in angstroms")
    y: float = Field(..., description="Y coordinate in angstroms")
    z: float = Field(..., description="Z coordinate in angstroms")


class AtomData(BaseModel):
    symbol: str = Field(..., min_length=1, description="Chemical symbol of the atom")
    atomic_number: int = Field(..., ge=1, description="Atomic number from the periodic table")
    coordinates: AtomCoordinates


class BondData(BaseModel):
    atom1: int = Field(..., ge=0, description="Zero-based index of the first atom in the bond")
    atom2: int = Field(..., ge=0, description="Zero-based index of the second atom in the bond")
    order: int = Field(..., ge=1, description="Integer bond order")


class MoleculeData(BaseModel):
    name: str | None = Field(default=None, description="Optional name parsed from the source document")
    formula: str = Field(..., description="Hill notation chemical formula")
    atom_count: int = Field(..., ge=0, description="Total number of atoms in the molecule")
    molecular_weight: float = Field(..., ge=0, description="Molecular weight in atomic mass units")
    atoms: list[AtomData]
    bonds: list[BondData]
