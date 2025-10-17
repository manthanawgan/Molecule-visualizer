from __future__ import annotations

from pathlib import Path
from typing import Callable, Tuple
from uuid import uuid4

from .molecules import AtomData, BondData, MoleculeData


class MoleculeParseError(Exception):
    """Raised when a supported file cannot be parsed into a molecule."""


class UnsupportedFileTypeError(Exception):
    """Raised when an uploaded file extension is not supported."""


ParsedResult = Tuple[list[AtomData], list[BondData]]


def parse_uploaded_file(filename: str | None, data: bytes) -> MoleculeData:
    """Parse ``data`` according to the extension in ``filename``.

    The function understands a small subset of common molecule formats used by
    the prototype and returns a :class:`~backend.molecules.MoleculeData` ready to
    be stored in the in-memory database.
    """

    derived_name = filename or "uploaded"
    extension = Path(derived_name).suffix.lower()

    parser = _PARSERS.get(extension)
    if parser is None:
        supported = ", ".join(sorted(_PARSERS.keys()))
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension or derived_name}'. Supported types: {supported}."
        )

    text = data.decode("utf-8", errors="ignore").strip()
    if not text:
        raise MoleculeParseError("Uploaded file is empty.")

    atoms, bonds = parser(text)

    if not atoms:
        raise MoleculeParseError("No atoms detected in the uploaded file.")

    smiles = Path(derived_name).stem or "uploaded-molecule"
    return MoleculeData(
        id=str(uuid4()),
        smiles=smiles,
        atoms=atoms,
        bonds=bonds,
        minimized=False,
    )


def _parse_xyz(text: str) -> ParsedResult:
    lines = text.splitlines()
    if len(lines) < 2:
        raise MoleculeParseError("XYZ file is missing header information.")

    try:
        atom_count = int(lines[0].split()[0])
    except (IndexError, ValueError) as exc:
        raise MoleculeParseError("XYZ file does not declare a valid atom count.") from exc

    atom_lines = [line for line in lines[2:] if line.strip()]
    if len(atom_lines) < atom_count:
        raise MoleculeParseError("XYZ file ended before all atoms were defined.")

    atoms: list[AtomData] = []
    for idx, raw in enumerate(atom_lines[:atom_count]):
        parts = raw.split()
        if len(parts) < 4:
            raise MoleculeParseError("XYZ atom line is malformed.")
        element = parts[0]
        try:
            x, y, z = map(float, parts[1:4])
        except ValueError as exc:
            raise MoleculeParseError("XYZ coordinates must be numeric.") from exc
        atoms.append(AtomData(index=idx, element=element, x=x, y=y, z=z))

    return atoms, []


def _parse_pdb(text: str) -> ParsedResult:
    atoms: list[AtomData] = []

    for line in text.splitlines():
        record = line[:6].strip().upper()
        if record not in {"ATOM", "HETATM"}:
            continue

        x_str = line[30:38].strip()
        y_str = line[38:46].strip()
        z_str = line[46:54].strip()
        if not (x_str and y_str and z_str):
            raise MoleculeParseError("PDB atom line is missing coordinates.")

        try:
            x = float(x_str)
            y = float(y_str)
            z = float(z_str)
        except ValueError as exc:
            raise MoleculeParseError("PDB coordinates must be numeric.") from exc

        element = line[76:78].strip()
        if not element:
            element = "".join(filter(str.isalpha, line[12:16])).strip()
        element = element or "X"

        atoms.append(AtomData(index=len(atoms), element=element, x=x, y=y, z=z))

    if not atoms:
        raise MoleculeParseError("No atoms found in PDB file.")

    return atoms, []


def _parse_molfile(text: str) -> ParsedResult:
    # Handle multi-molecule SDF files by selecting the first block.
    block = text.split("$$$$", 1)[0]
    lines = block.splitlines()
    if len(lines) < 4:
        raise MoleculeParseError("Molfile is missing the counts line.")

    counts_line = lines[3]
    parts = counts_line.split()
    if len(parts) < 2:
        raise MoleculeParseError("Molfile counts line is malformed.")

    try:
        atom_total = int(parts[0])
        bond_total = int(parts[1])
    except ValueError as exc:
        raise MoleculeParseError("Molfile counts line is invalid.") from exc

    current = 4
    atoms: list[AtomData] = []
    while len(atoms) < atom_total and current < len(lines):
        line = lines[current]
        current += 1
        if not line.strip():
            continue

        try:
            if len(line) >= 34:
                x_str = line[0:10].strip()
                y_str = line[10:20].strip()
                z_str = line[20:30].strip()
                element = line[31:34].strip()
            else:
                tokens = line.split()
                if len(tokens) < 4:
                    raise ValueError
                x_str, y_str, z_str, element = tokens[:4]
            x = float(x_str)
            y = float(y_str)
            z = float(z_str)
        except ValueError as exc:
            raise MoleculeParseError("Molfile atom entry is malformed.") from exc

        element = element or "X"
        atoms.append(AtomData(index=len(atoms), element=element, x=x, y=y, z=z))

    if len(atoms) != atom_total:
        raise MoleculeParseError("Molfile ended before all atoms were defined.")

    bonds: list[BondData] = []
    while len(bonds) < bond_total and current < len(lines):
        line = lines[current]
        current += 1
        if not line.strip():
            continue

        try:
            if len(line) >= 9:
                atom1_str = line[0:3].strip()
                atom2_str = line[3:6].strip()
                order_str = line[6:9].strip() or "1"
            else:
                tokens = line.split()
                if len(tokens) < 3:
                    raise ValueError
                atom1_str, atom2_str, order_str = tokens[:3]
            atom1 = int(atom1_str) - 1
            atom2 = int(atom2_str) - 1
            order = int(order_str)
        except ValueError as exc:
            raise MoleculeParseError("Molfile bond entry is malformed.") from exc

        if atom1 < 0 or atom2 < 0 or atom1 >= len(atoms) or atom2 >= len(atoms):
            raise MoleculeParseError("Molfile bond references an unknown atom index.")

        bonds.append(BondData(atom1=atom1, atom2=atom2, order=order))

    if len(bonds) != bond_total:
        raise MoleculeParseError("Molfile ended before all bonds were defined.")

    return atoms, bonds


_PARSERS: dict[str, Callable[[str], ParsedResult]] = {
    ".mol": _parse_molfile,
    ".sdf": _parse_molfile,
    ".pdb": _parse_pdb,
    ".xyz": _parse_xyz,
}
