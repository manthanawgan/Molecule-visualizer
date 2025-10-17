from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from typing import Dict, List, Tuple
from uuid import uuid4


@dataclass(frozen=True)
class AtomData:
    index: int
    element: str
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class BondData:
    atom1: int
    atom2: int
    order: int = 1


@dataclass
class MoleculeData:
    id: str
    smiles: str
    atoms: List[AtomData]
    bonds: List[BondData]
    minimized: bool = False


def create_molecule(smiles: str, minimize: bool = False) -> MoleculeData:
    """Create a naive 3D layout from a SMILES-like string.

    This is a lightweight placeholder that arranges detected element tokens on a
    circle and connects consecutive atoms with single bonds. It is sufficient for
    visualisation demos without heavy cheminformatics dependencies.
    """

    tokens: List[str] = _tokenize_smiles_light(smiles)
    if not tokens:
        raise ValueError("SMILES string did not contain any atoms.")

    radius = max(1.5, 1.2 * len(tokens) / pi)
    atoms: List[AtomData] = []
    bonds: List[BondData] = []

    for i, element in enumerate(tokens):
        angle = 2 * pi * (i / max(1, len(tokens)))
        atoms.append(AtomData(index=i, element=element, x=radius * cos(angle), y=radius * sin(angle), z=0.0))
        if i > 0:
            bonds.append(BondData(atom1=i - 1, atom2=i, order=1))

    molecule = MoleculeData(id=str(uuid4()), smiles=smiles, atoms=atoms, bonds=bonds, minimized=False)
    if minimize:
        molecule = update_molecule_geometry(molecule, minimize=True)
    return molecule


def update_molecule_geometry(molecule: MoleculeData, minimize: bool = False) -> MoleculeData:
    """Apply very light geometry adjustments.

    - Recentre atoms to the origin.
    - Optionally scale bond lengths slightly shorter to "tidy" the layout.
    """

    if not molecule.atoms:
        return molecule

    cx = sum(a.x for a in molecule.atoms) / len(molecule.atoms)
    cy = sum(a.y for a in molecule.atoms) / len(molecule.atoms)
    cz = sum(a.z for a in molecule.atoms) / len(molecule.atoms)

    scale = 0.92 if minimize else 1.0
    new_atoms = [
        AtomData(index=a.index, element=a.element, x=(a.x - cx) * scale, y=(a.y - cy) * scale, z=(a.z - cz) * scale)
        for a in molecule.atoms
    ]

    return MoleculeData(
        id=molecule.id,
        smiles=molecule.smiles,
        atoms=new_atoms,
        bonds=list(molecule.bonds),
        minimized=minimize or molecule.minimized,
    )


def _tokenize_smiles_light(smiles: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    while i < len(smiles):
        ch = smiles[i]
        if ch.isalpha():
            # Two-letter elements like Cl, Br
            if i + 1 < len(smiles) and smiles[i + 1].islower():
                tokens.append(ch + smiles[i + 1])
                i += 2
                continue
            tokens.append(ch)
        i += 1
    return tokens


