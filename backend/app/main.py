import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from rdkit import Chem


def _parse_origins(value: str) -> List[str]:
    """Return normalized list of CORS origins."""
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    return origins or ["*"]


app = FastAPI(title="Molecule Visualizer Backend")

allowed_origins = _parse_origins(os.getenv("CORS_ALLOW_ORIGINS", "*"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in allowed_origins else allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/molecule/summary")
def get_molecule_summary(smiles: str) -> dict[str, int]:
    """Return simple RDKit-derived metrics for a SMILES string."""
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise HTTPException(status_code=400, detail="Invalid SMILES string")

    return {
        "atoms": molecule.GetNumAtoms(),
        "bonds": molecule.GetNumBonds(),
        "rings": Chem.GetSSSR(molecule),
    }
