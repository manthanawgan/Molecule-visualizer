"""Geometry helpers shared by multiple FastAPI routes."""

from __future__ import annotations

import math
from typing import Dict, Tuple

from .molecules import AtomData, MoleculeData


def _atom_lookup(molecule: MoleculeData) -> Dict[int, AtomData]:
    """Return a mapping of atom indices for quick access."""

    return {atom.index: atom for atom in molecule.atoms}


def compute_atom_distance(molecule: MoleculeData, atom1: int, atom2: int) -> float:
    """Compute the Euclidean distance between two atoms in a molecule."""

    atoms = _atom_lookup(molecule)
    try:
        a = atoms[atom1]
        b = atoms[atom2]
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise IndexError("Atom index out of range") from exc

    dx = a.x - b.x
    dy = a.y - b.y
    dz = a.z - b.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def compute_bond_distances(molecule: MoleculeData) -> Dict[Tuple[int, int], float]:
    """Compute distances for all bonds declared in ``molecule``."""

    distances: Dict[Tuple[int, int], float] = {}
    for bond in molecule.bonds:
        key = tuple(sorted((bond.atom1, bond.atom2)))
        distances[key] = compute_atom_distance(molecule, bond.atom1, bond.atom2)
    return distances


__all__ = ["compute_atom_distance", "compute_bond_distances"]
