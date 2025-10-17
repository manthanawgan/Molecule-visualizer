from fastapi import FastAPI

app = FastAPI(title="Molecule Visualizer Backend", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Simple liveness probe used by local development tooling."""
    return {"status": "ok"}
