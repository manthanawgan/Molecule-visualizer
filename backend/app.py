from __future__ import annotations

from typing import Dict

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from .geometry import compute_atom_distance, compute_bond_distances
from .molecules import (
    AtomData,
    BondData,
    MoleculeData,
    create_molecule,
    update_molecule_geometry,
)
from .parsing import (
    MoleculeParseError,
    UnsupportedFileTypeError,
    parse_uploaded_file,
)

app = FastAPI(title="Molecule Visualizer Backend", version="0.2.0")

# In-memory store used by the prototype. The data is ephemeral and will be
# recreated whenever the service restarts which keeps the implementation
# dependency-free and simple to reason about during development.
MOLECULE_STORE: Dict[str, MoleculeData] = {}


class SmilesRequest(BaseModel):
    smiles: str = Field(..., min_length=1, description="SMILES string to build a molecule from.")
    minimize: bool = Field(
        default=False,
        description=(
            "When set to true, perform a lightweight UFF-inspired minimisation "
            "step that recentres atoms and shortens the default bond length."
        ),
    )
    molecule_id: str | None = Field(
        default=None,
        description="Optional identifier of an existing molecule to update.",
    )


class MoleculeResponse(BaseModel):
    id: str
    smiles: str
    minimized: bool
    atoms: list[AtomData]
    bonds: list[BondData]
    bond_distances: dict[str, float]

    @classmethod
    def from_molecule(cls, molecule: MoleculeData) -> "MoleculeResponse":
        bond_distances = {
            f"{a}-{b}": distance
            for (a, b), distance in compute_bond_distances(molecule).items()
        }
        return cls(
            id=molecule.id,
            smiles=molecule.smiles,
            minimized=molecule.minimized,
            atoms=molecule.atoms,
            bonds=molecule.bonds,
            bond_distances=bond_distances,
        )


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple liveness probe used by local development tooling."""
    return {"status": "ok"}


@app.post("/upload")
async def upload_molecule(file: UploadFile = File(...)) -> dict[str, str]:
    try:
        contents = await file.read()
    except Exception as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.") from exc

    try:
        molecule = parse_uploaded_file(file.filename, contents)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MoleculeParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    MOLECULE_STORE[molecule.id] = molecule
    return {"id": molecule.id}


@app.get("/molecule/by-smiles", response_model=MoleculeResponse)
async def molecule_by_smiles(
    smiles: str = Query(..., min_length=1),
    minimize: bool = Query(False),
) -> MoleculeResponse:
    value = smiles.strip()
    if not value:
        raise HTTPException(status_code=422, detail="SMILES string cannot be empty.")

    try:
        molecule = create_molecule(value, minimize=minimize)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MoleculeResponse.from_molecule(molecule)


@app.get("/molecule/{molecule_id}", response_model=MoleculeResponse)
async def get_molecule(molecule_id: str) -> MoleculeResponse:
    molecule = MOLECULE_STORE.get(molecule_id)
    if molecule is None:
        raise HTTPException(status_code=404, detail="Molecule not found.")
    return MoleculeResponse.from_molecule(molecule)


@app.post("/smiles", response_model=MoleculeResponse)
async def smiles_to_molecule(payload: SmilesRequest) -> MoleculeResponse:
    """Create or update a molecule derived from SMILES input."""

    smiles = payload.smiles.strip()
    if not smiles:
        raise HTTPException(status_code=422, detail="SMILES string cannot be empty.")

    if payload.molecule_id:
        existing = MOLECULE_STORE.get(payload.molecule_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Molecule not found.")
        if existing.smiles != smiles:
            raise HTTPException(
                status_code=400,
                detail="SMILES string does not match the stored molecule.",
            )
        try:
            molecule = update_molecule_geometry(existing, minimize=payload.minimize)
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        try:
            molecule = create_molecule(smiles, minimize=payload.minimize)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    MOLECULE_STORE[molecule.id] = molecule
    return MoleculeResponse.from_molecule(molecule)


@app.get("/distance")
async def get_distance(
    molecule_id: str = Query(..., description="Identifier returned by the /smiles endpoint."),
    atom1: int = Query(..., ge=0, description="Index of the first atom."),
    atom2: int = Query(..., ge=0, description="Index of the second atom."),
) -> dict[str, float | int | str]:
    """Return the Euclidean distance between two atoms of a stored molecule."""

    molecule = MOLECULE_STORE.get(molecule_id)
    if molecule is None:
        raise HTTPException(status_code=404, detail="Molecule not found.")

    try:
        distance = compute_atom_distance(molecule, atom1, atom2)
    except IndexError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "molecule_id": molecule_id,
        "atom1": atom1,
        "atom2": atom2,
        "distance": distance,
        "units": "angstrom",
    }
