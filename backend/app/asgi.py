"""Application factory and API configuration for the molecule backend."""

from __future__ import annotations

import os
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.app.storage import MoleculeStore, create_store
from backend.geometry import compute_atom_distance, compute_bond_distances
from backend.molecules import (
    AtomData,
    BondData,
    MoleculeData,
    create_molecule,
    update_molecule_geometry,
)
from backend.parsing import MoleculeParseError, UnsupportedFileTypeError, parse_uploaded_file

from pydantic import BaseModel, Field

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance."""

    app = FastAPI(title="Molecule Visualizer API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_ORIGIN],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    register_routes(app)

    app.state.molecule_store = create_store()

    return app


class SmilesRequest(BaseModel):
    smiles: str = Field(..., min_length=1)
    minimize: bool = Field(default=False)
    molecule_id: str | None = Field(default=None)


class MoleculeResponse(BaseModel):
    id: str
    smiles: str
    minimized: bool
    atoms: list[AtomData]
    bonds: list[BondData]
    bond_distances: dict[str, float]

    @classmethod
    def from_molecule(cls, molecule: MoleculeData) -> "MoleculeResponse":
        bond_distances = {f"{a}-{b}": d for (a, b), d in compute_bond_distances(molecule).items()}
        return cls(
            id=molecule.id,
            smiles=molecule.smiles,
            minimized=molecule.minimized,
            atoms=molecule.atoms,
            bonds=molecule.bonds,
            bond_distances=bond_distances,
        )


def register_routes(app: FastAPI) -> None:
    """Attach API routes to the supplied application instance."""

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/upload")
    async def upload_molecule(file: UploadFile = File(...)) -> dict[str, str]:
        try:
            contents = await file.read()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Failed to read uploaded file.") from exc

        try:
            molecule = parse_uploaded_file(file.filename, contents)
        except UnsupportedFileTypeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except MoleculeParseError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        app.state.molecule_store[molecule.id] = molecule
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
        molecule = app.state.molecule_store.get(molecule_id)
        if molecule is None:
            raise HTTPException(status_code=404, detail="Molecule not found.")
        return MoleculeResponse.from_molecule(molecule)

    @app.post("/smiles", response_model=MoleculeResponse)
    async def smiles_to_molecule(payload: SmilesRequest) -> MoleculeResponse:
        smiles = payload.smiles.strip()
        if not smiles:
            raise HTTPException(status_code=422, detail="SMILES string cannot be empty.")

        if payload.molecule_id:
            existing = app.state.molecule_store.get(payload.molecule_id)
            if existing is None:
                raise HTTPException(status_code=404, detail="Molecule not found.")
            if existing.smiles != smiles:
                raise HTTPException(status_code=400, detail="SMILES string does not match the stored molecule.")
            try:
                molecule = update_molecule_geometry(existing, minimize=payload.minimize)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        else:
            try:
                molecule = create_molecule(smiles, minimize=payload.minimize)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        app.state.molecule_store[molecule.id] = molecule
        return MoleculeResponse.from_molecule(molecule)

    @app.get("/distance")
    async def get_distance(
        molecule_id: str = Query(..., description="Identifier returned by the /smiles endpoint."),
        atom1: int = Query(..., ge=0, description="Index of the first atom."),
        atom2: int = Query(..., ge=0, description="Index of the second atom."),
    ) -> dict[str, float | int | str]:
        molecule = app.state.molecule_store.get(molecule_id)
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


app = create_app()

__all__ = ["MoleculeStore", "create_app", "app", "FRONTEND_ORIGIN"]
