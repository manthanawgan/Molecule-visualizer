# Molecule Visualizer

This prototype couples a Three.js powered Vite frontend with a FastAPI backend that exposes a small RDKit-enabled API for molecule analysis.

## Prerequisites

- Docker 20.10+
- Docker Compose v2

## Running the stack

```bash
docker compose up --build
```

Once the build completes you can browse the application at http://localhost:4173.

The frontend sends requests to the backend via the automatically provided `VITE_API_BASE_URL` environment variable. CORS is enabled for both the `frontend` service inside Docker and for localhost access, enabling frictionless cross-container calls.

### Backend

- **Image**: based on `mambaorg/micromamba` with RDKit installed inside a dedicated `rdkit-env` environment.
- **Service Name**: `backend`
- **Port**: `8000`
- **Health endpoint**: `GET /health`
- **Molecule summary endpoint**: `GET /molecule/summary?smiles=` – returns atom, bond, and ring counts via RDKit.

### Frontend

- **Image**: multi-stage build using `node:20-alpine`
- **Service Name**: `frontend`
- **Public Port**: `4173` (served with `vite preview`)
- Uses the `VITE_API_BASE_URL` build argument and runtime environment variable to discover the backend URL.

## Development Notes

- The backend service bind-mounts `./backend/app` so changes to Python files are picked up without rebuilding the image (restart the container to reload).
- Node and Vite caches are stored under a named Docker volume (`node-modules-cache`) to speed up subsequent installs.

## Smoke Testing

Run the following to confirm everything comes up cleanly:

```bash
docker compose up --build
```

Expected output:

1. `backend` image builds with micromamba installing RDKit, FastAPI, and Uvicorn.
2. `frontend` image builds via Vite and starts the preview server.
3. Visiting `http://localhost:4173` shows the visualizer. Submitting the default SMILES string returns RDKit-derived molecule metrics from the backend.

To tear everything down:

```bash
docker compose down
```
