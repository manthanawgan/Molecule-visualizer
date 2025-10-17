from __future__ import annotations

from fastapi import File, FastAPI, HTTPException, UploadFile, status

from backend.schemas import MoleculeData
from backend.services.molecule_parser import MoleculeParserService, MoleculeParsingError
from backend.utils.file_handling import extract_file_payload

app = FastAPI(title="Molecule Visualizer Backend", version="0.1.0")
parser_service = MoleculeParserService()


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple liveness probe used by local development tooling."""
    return {"status": "ok"}


@app.post("/molecules/parse", response_model=MoleculeData)
async def parse_molecule(file: UploadFile = File(...)) -> MoleculeData:
    """Parse an uploaded molecule file into a normalised schema."""
    file_format, payload = await extract_file_payload(file)
    try:
        return parser_service.parse(payload, file_format, filename=file.filename)
    except MoleculeParsingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
