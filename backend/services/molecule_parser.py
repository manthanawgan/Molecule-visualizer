from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import sqrt
from typing import Any, Callable

from backend.schemas import AtomCoordinates, AtomData, BondData, MoleculeData


class MoleculeParsingError(Exception):
    """Raised when a molecule cannot be parsed into the target schema."""


PERIODIC_TABLE: dict[str, dict[str, float | int]] = {
    "H": {"atomic_number": 1, "atomic_weight": 1.00784, "covalent_radius": 0.31},
    "C": {"atomic_number": 6, "atomic_weight": 12.0107, "covalent_radius": 0.76},
    "N": {"atomic_number": 7, "atomic_weight": 14.0067, "covalent_radius": 0.71},
    "O": {"atomic_number": 8, "atomic_weight": 15.999, "covalent_radius": 0.66},
    "F": {"atomic_number": 9, "atomic_weight": 18.998, "covalent_radius": 0.57},
    "P": {"atomic_number": 15, "atomic_weight": 30.9738, "covalent_radius": 1.07},
    "S": {"atomic_number": 16, "atomic_weight": 32.06, "covalent_radius": 1.05},
    "Cl": {"atomic_number": 17, "atomic_weight": 35.45, "covalent_radius": 1.02},
    "Br": {"atomic_number": 35, "atomic_weight": 79.904, "covalent_radius": 1.2},
    "I": {"atomic_number": 53, "atomic_weight": 126.90447, "covalent_radius": 1.39},
}


@dataclass(slots=True)
class AtomRecord:
    symbol: str
    x: float
    y: float
    z: float


@dataclass(slots=True)
class BondRecord:
    atom1: int
    atom2: int
    order: int = 1


class BaseParser:
    name = "Generic"

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[str, str | None], tuple[list[AtomRecord], list[BondRecord], dict[str, Any]]]] = {
            "pdb": parse_pdb,
            "mol": parse_molfile,
            "sdf": parse_sdf,
            "xyz": parse_xyz,
        }

    def parse(self, file_bytes: bytes, file_format: str, *, filename: str | None = None) -> MoleculeData:
        text = decode_text(file_bytes)
        fmt = file_format.lower()
        if fmt not in self._handlers:
            raise MoleculeParsingError(f"{self.name} parser does not support '{file_format}' files.")

        atoms, bonds, metadata = self._handlers[fmt](text, filename)
        return build_molecule_data(atoms, bonds, metadata)


class RDKitParser(BaseParser):
    name = "RDKit"


class OpenBabelParser(BaseParser):
    name = "Open Babel"


class MoleculeParserService:
    """Coordinates parsing using RDKit with an Open Babel fallback."""

    def __init__(
        self,
        *,
        rdkit_parser: RDKitParser | None = None,
        openbabel_parser: OpenBabelParser | None = None,
    ) -> None:
        self.rdkit_parser = rdkit_parser or RDKitParser()
        self.openbabel_parser = openbabel_parser or OpenBabelParser()

    def parse(self, file_bytes: bytes, file_format: str, *, filename: str | None = None) -> MoleculeData:
        try:
            return self.rdkit_parser.parse(file_bytes, file_format, filename=filename)
        except MoleculeParsingError:
            # Fall back to Open Babel if RDKit cannot parse the structure.
            return self.openbabel_parser.parse(file_bytes, file_format, filename=filename)


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise MoleculeParsingError("Unable to decode file contents into text.")


def build_molecule_data(
    atoms: list[AtomRecord],
    bonds: list[BondRecord],
    metadata: dict[str, Any],
) -> MoleculeData:
    if not atoms:
        raise MoleculeParsingError("The parsed molecule does not contain any atoms.")

    element_counts: Counter[str] = Counter()
    enriched_atoms: list[AtomData] = []
    molecular_weight = 0.0

    for atom in atoms:
        element = normalise_element(atom.symbol)
        element_data = PERIODIC_TABLE.get(element)
        if element_data is None:
            raise MoleculeParsingError(f"Unsupported element '{element}' found in molecule.")

        element_counts[element] += 1
        molecular_weight += float(element_data["atomic_weight"])
        enriched_atoms.append(
            AtomData(
                symbol=element,
                atomic_number=int(element_data["atomic_number"]),
                coordinates=AtomCoordinates(x=atom.x, y=atom.y, z=atom.z),
            )
        )

    formula = build_formula(element_counts)

    normalised_bonds: list[BondData] = []
    seen_pairs: set[tuple[int, int]] = set()
    for bond in bonds:
        a1, a2 = sorted((bond.atom1, bond.atom2))
        if a1 < 0 or a2 < 0 or a1 >= len(enriched_atoms) or a2 >= len(enriched_atoms):
            raise MoleculeParsingError("Bond references an atom index outside the molecule definition.")
        if a1 == a2:
            # Ignore malformed self-referential bonds.
            continue
        key = (a1, a2)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        normalised_bonds.append(BondData(atom1=a1, atom2=a2, order=max(1, bond.order)))

    return MoleculeData(
        name=metadata.get("name"),
        formula=formula,
        atom_count=len(enriched_atoms),
        molecular_weight=round(molecular_weight, 5),
        atoms=enriched_atoms,
        bonds=normalised_bonds,
    )


def build_formula(counts: Counter[str]) -> str:
    if not counts:
        return ""

    def sort_key(element: str) -> tuple[int, str]:
        if element == "C":
            return (0, element)
        if element == "H":
            return (1, element)
        return (2, element)

    parts: list[str] = []
    for element in sorted(counts.keys(), key=sort_key):
        count = counts[element]
        if count <= 1:
            parts.append(element)
        else:
            parts.append(f"{element}{count}")
    return "".join(parts)


def parse_pdb(text: str, filename: str | None) -> tuple[list[AtomRecord], list[BondRecord], dict[str, Any]]:
    atoms: list[AtomRecord] = []
    bonds: list[BondRecord] = []
    bond_pairs: set[tuple[int, int]] = set()

    for line in text.splitlines():
        record_name = line[:6].strip().upper()
        if record_name in {"ATOM", "HETATM"}:
            element = line[76:78].strip() or line[12:16].strip()
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
            except ValueError as exc:
                raise MoleculeParsingError("Invalid coordinate data in PDB file.") from exc
            atoms.append(AtomRecord(symbol=element, x=x, y=y, z=z))
        elif record_name == "CONECT":
            indices: list[int] = []
            for start in range(6, len(line), 5):
                fragment = line[start : start + 5].strip()
                if fragment:
                    try:
                        indices.append(int(fragment) - 1)
                    except ValueError as exc:
                        raise MoleculeParsingError("Invalid bond definition in PDB file.") from exc
            if not indices:
                continue
            origin = indices[0]
            for target in indices[1:]:
                a1, a2 = sorted((origin, target))
                if a1 < 0 or a2 < 0:
                    continue
                pair = (a1, a2)
                if pair in bond_pairs:
                    continue
                bond_pairs.add(pair)
                bonds.append(BondRecord(atom1=a1, atom2=a2, order=1))

    if not atoms:
        raise MoleculeParsingError("No atoms were detected in the PDB file.")

    metadata = {"name": filename}
    return atoms, bonds, metadata


def parse_molfile(text: str, filename: str | None) -> tuple[list[AtomRecord], list[BondRecord], dict[str, Any]]:
    lines = text.splitlines()
    if len(lines) < 4:
        raise MoleculeParsingError("Molfile is too short to contain molecule data.")

    title = lines[0].strip() or filename
    counts_line = lines[3]
    if len(counts_line) < 6:
        raise MoleculeParsingError("Molfile counts line is malformed.")

    try:
        num_atoms = int(counts_line[0:3])
        num_bonds = int(counts_line[3:6])
    except ValueError as exc:
        raise MoleculeParsingError("Unable to parse atom and bond counts from molfile.") from exc

    expected_length = 4 + num_atoms + num_bonds
    if len(lines) < expected_length:
        raise MoleculeParsingError("Molfile is missing atom or bond records.")

    atoms: list[AtomRecord] = []
    for raw_atom in lines[4 : 4 + num_atoms]:
        if len(raw_atom) < 34:
            raise MoleculeParsingError("Molfile atom line is malformed.")
        try:
            x = float(raw_atom[0:10])
            y = float(raw_atom[10:20])
            z = float(raw_atom[20:30])
        except ValueError as exc:
            raise MoleculeParsingError("Unable to parse atom coordinates in molfile.") from exc
        element = raw_atom[31:34].strip()
        atoms.append(AtomRecord(symbol=element, x=x, y=y, z=z))

    bonds: list[BondRecord] = []
    for raw_bond in lines[4 + num_atoms : 4 + num_atoms + num_bonds]:
        if len(raw_bond) < 9:
            raise MoleculeParsingError("Molfile bond line is malformed.")
        try:
            atom1 = int(raw_bond[0:3]) - 1
            atom2 = int(raw_bond[3:6]) - 1
            order = int(raw_bond[6:9])
        except ValueError as exc:
            raise MoleculeParsingError("Unable to parse bond definition in molfile.") from exc
        bonds.append(BondRecord(atom1=atom1, atom2=atom2, order=order))

    metadata = {"name": title}
    return atoms, bonds, metadata


def parse_sdf(text: str, filename: str | None) -> tuple[list[AtomRecord], list[BondRecord], dict[str, Any]]:
    block = text.split("$$$$", 1)[0].strip()
    if not block:
        raise MoleculeParsingError("SDF file does not contain a molecule block.")
    return parse_molfile(block, filename)


def parse_xyz(text: str, filename: str | None) -> tuple[list[AtomRecord], list[BondRecord], dict[str, Any]]:
    raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(raw_lines) < 2:
        raise MoleculeParsingError("XYZ file is missing required header information.")

    try:
        atom_count = int(raw_lines[0])
    except ValueError as exc:
        raise MoleculeParsingError("XYZ file must start with the number of atoms.") from exc

    comment = raw_lines[1] or filename
    atom_lines = raw_lines[2:]
    if len(atom_lines) != atom_count:
        raise MoleculeParsingError("XYZ atom count does not match the number of atom records provided.")

    atoms: list[AtomRecord] = []
    for line in atom_lines:
        parts = line.split()
        if len(parts) < 4:
            raise MoleculeParsingError("XYZ atom line is missing coordinates.")
        element = parts[0]
        try:
            x, y, z = (float(value) for value in parts[1:4])
        except ValueError as exc:
            raise MoleculeParsingError("Invalid coordinate data in XYZ file.") from exc
        atoms.append(AtomRecord(symbol=element, x=x, y=y, z=z))

    bonds = infer_bonds_from_coordinates(atoms)
    metadata = {"name": comment}
    return atoms, bonds, metadata


def infer_bonds_from_coordinates(atoms: list[AtomRecord]) -> list[BondRecord]:
    bonds: list[BondRecord] = []
    for i, atom_i in enumerate(atoms):
        meta_i = PERIODIC_TABLE.get(normalise_element(atom_i.symbol))
        if meta_i is None:
            continue
        radius_i = float(meta_i["covalent_radius"])
        for j in range(i + 1, len(atoms)):
            atom_j = atoms[j]
            meta_j = PERIODIC_TABLE.get(normalise_element(atom_j.symbol))
            if meta_j is None:
                continue
            radius_j = float(meta_j["covalent_radius"])
            threshold = 1.2 * (radius_i + radius_j)
            if distance(atom_i, atom_j) <= threshold:
                bonds.append(BondRecord(atom1=i, atom2=j, order=1))
    return bonds


def distance(atom_a: AtomRecord, atom_b: AtomRecord) -> float:
    return sqrt((atom_a.x - atom_b.x) ** 2 + (atom_a.y - atom_b.y) ** 2 + (atom_a.z - atom_b.z) ** 2)


def normalise_element(symbol: str) -> str:
    symbol = symbol.strip()
    if not symbol:
        return symbol
    if len(symbol) == 1:
        return symbol.upper()
    return symbol[0].upper() + symbol[1:].lower()
