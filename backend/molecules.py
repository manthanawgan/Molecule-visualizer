"""Utilities and data models describing simple molecule representations.

The project intentionally implements a lightweight SMILES parser so that the
backend can run without heavy third-party chemistry dependencies.  The parser
supports a restricted subset of SMILES where atoms are encoded as the usual
uppercase symbol optionally followed by a single lowercase character (e.g.
``C``, ``O`` or ``Cl``).  Any other characters are ignored which allows numbers
and branch markers present in more complex SMILES strings without failing the
request outright.  The resulting geometry is synthetic but deterministic which
is sufficient for validating client integrations and distance calculations.
"""

from __future__ import annotations

from typing import Iterable, List
from uuid import uuid4

from pydantic import BaseModel, Field

INITIAL_BOND_LENGTH = 1.58
"""Default bond length (in Ångström) for the procedurally generated geometry."""

MINIMIZED_BOND_LENGTH = 1.24
"""Bond length used when the minimisation flag is enabled."""


class AtomData(BaseModel):
    """Simple record describing an atom and its 3D coordinates."""

    index: int = Field(..., ge=0)
    element: str = Field(..., min_length=1)
    x: float
    y: float
    z: float


class BondData(BaseModel):
    """Connectivity information between two atoms."""

    atom1: int = Field(..., ge=0)
    atom2: int = Field(..., ge=0)
    order: int = Field(default=1, ge=1)


class MoleculeData(BaseModel):
    """Container returned by the SMILES endpoint and stored in memory."""

    id: str
    smiles: str
    atoms: List[AtomData]
    bonds: List[BondData]
    minimized: bool = False


def _tokenize_smiles(smiles: str) -> List[str]:
    """Return a list of element symbols detected in a SMILES string.

    The implementation focuses on the common subset used by the prototype where
    atoms are expressed as an uppercase character optionally followed by a
    lowercase one.  Aromatic atoms written in lowercase (e.g. ``c``) are
    normalised to their capitalised form so downstream consumers get a
    consistent representation.
    """

    cleaned = smiles.strip()
    tokens: List[str] = []
    i = 0
    while i < len(cleaned):
        char = cleaned[i]
        if char.isalpha():
            if i + 1 < len(cleaned) and cleaned[i + 1].islower():
                symbol = f"{char}{cleaned[i + 1]}"
                i += 2
            else:
                symbol = char
                i += 1
            tokens.append(symbol.capitalize())
        else:
            i += 1
    return tokens


def _generate_atoms(symbols: Iterable[str], spacing: float, *, center: bool) -> List[AtomData]:
    """Create atom records spaced along the X axis."""

    symbols = list(symbols)
    if not symbols:
        raise ValueError("SMILES string must contain at least one atom symbol.")

    count = len(symbols)
    offset = ((count - 1) * spacing) / 2 if center and count > 1 else 0.0

    atoms: List[AtomData] = []
    for idx, element in enumerate(symbols):
        x_coord = idx * spacing - offset
        atoms.append(
            AtomData(
                index=idx,
                element=element,
                x=x_coord,
                y=0.0,
                z=0.0,
            )
        )
    return atoms


def _generate_bonds(atom_count: int) -> List[BondData]:
    """Create single bonds between adjacent atoms."""

    if atom_count <= 1:
        return []

    bonds: List[BondData] = []
    for idx in range(atom_count - 1):
        bonds.append(BondData(atom1=idx, atom2=idx + 1, order=1))
    return bonds


def create_molecule(smiles: str, *, minimize: bool = False) -> MoleculeData:
    """Create a new molecule representation from a SMILES string."""

    symbols = _tokenize_smiles(smiles)
    if not symbols:
        raise ValueError("Unable to detect any atoms in the supplied SMILES string.")

    spacing = MINIMIZED_BOND_LENGTH if minimize else INITIAL_BOND_LENGTH
    atoms = _generate_atoms(symbols, spacing, center=minimize)
    bonds = _generate_bonds(len(symbols))

    return MoleculeData(
        id=str(uuid4()),
        smiles=smiles.strip(),
        atoms=atoms,
        bonds=bonds,
        minimized=minimize,
    )


def update_molecule_geometry(molecule: MoleculeData, *, minimize: bool) -> MoleculeData:
    """Return a copy of ``molecule`` with refreshed coordinates."""

    symbols = _tokenize_smiles(molecule.smiles)
    spacing = MINIMIZED_BOND_LENGTH if minimize else INITIAL_BOND_LENGTH
    atoms = _generate_atoms(symbols, spacing, center=minimize)
    bonds = _generate_bonds(len(symbols))

    return molecule.model_copy(update={"atoms": atoms, "bonds": bonds, "minimized": minimize})


__all__ = [
    "AtomData",
    "BondData",
    "MoleculeData",
    "INITIAL_BOND_LENGTH",
    "MINIMIZED_BOND_LENGTH",
    "create_molecule",
    "update_molecule_geometry",
]
