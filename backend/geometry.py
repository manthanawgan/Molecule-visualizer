from __future__ import annotations

from math import sqrt
from typing import Dict, Tuple

from .molecules import AtomData, BondData, MoleculeData


def compute_atom_distance(molecule: MoleculeData, atom1_index: int, atom2_index: int) -> float:
    atoms = molecule.atoms
    if atom1_index < 0 or atom2_index < 0 or atom1_index >= len(atoms) or atom2_index >= len(atoms):
        raise IndexError("Atom index out of range.")

    a = atoms[atom1_index]
    b = atoms[atom2_index]
    return _distance(a, b)


def compute_bond_distances(molecule: MoleculeData) -> Dict[Tuple[int, int], float]:
    distances: Dict[Tuple[int, int], float] = {}
    for bond in molecule.bonds:
        key = (min(bond.atom1, bond.atom2), max(bond.atom1, bond.atom2))
        distances[key] = compute_atom_distance(molecule, bond.atom1, bond.atom2)
    return distances


def _distance(a: AtomData, b: AtomData) -> float:
    dx = a.x - b.x
    dy = a.y - b.y
    dz = a.z - b.z
    return sqrt(dx * dx + dy * dy + dz * dz)


