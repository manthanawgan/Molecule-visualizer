# Molecule Visualizer Monorepo

This repository bundles a FastAPI backend powered by RDKit with a Three.js + Vite frontend. The entire stack is containerised so that the only local dependency required is Docker (with Compose v2).

## Repository layout

```
.
├── backend/
│   ├── app/
│   │   └── main.py          # FastAPI entry point exposing RDKit utilities
│   ├── Dockerfile           # Micromamba-based image with RDKit preinstalled
│   └── environment.yml      # Conda specification for the RDKit environment
├── frontend/
│   ├── Dockerfile           # Multi-stage build that serves Vite preview
│   ├── index.html           # Vite HTML shell
│   ├── package.json         # Vite + Three.js project manifest
│   └── src/
│       ├── main.js          # Three.js scene + REST integration
│       └── style.css
├── docker-compose.yml       # Orchestrates the frontend and backend services
├── .env.example             # Optional overrides for compose configuration
└── README.md
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/) v2 (bundled with Docker Desktop)

> No local Python or Node.js runtimes are required when using Docker Compose.

## Quick start with Docker Compose

1. (Optional) Override defaults by copying the environment template:
   ```bash
   cp .env.example .env
   ```
2. Build and start both services:
   ```bash
   docker compose up --build
   ```
3. Visit the running stack:
   - Frontend UI: [http://localhost:4173](http://localhost:4173)
   - Backend health check: [http://localhost:8000/health](http://localhost:8000/health)

`docker compose up` will install Node dependencies for the frontend and create a micromamba environment containing RDKit for the backend on the first run. Subsequent runs reuse the cached layers.

## Service overview

### Backend (`backend` service)
- **Runtime:** FastAPI served by Uvicorn.
- **Image base:** `mambaorg/micromamba` (RDKit provided via `environment.yml`).
- **Expose:** `GET /health` and `GET /molecule/summary?smiles=<SMILES>`.
- **Hot reload:** The `./backend/app` directory is bind mounted into the container so code edits are picked up after a container restart without rebuilding the image.
- **CORS:** Controlled by the `CORS_ALLOW_ORIGINS` environment variable (comma-separated origins). Defaults allow requests from the frontend service and localhost.

### Frontend (`frontend` service)
- **Tooling:** Vite + Three.js.
- **Serving:** The production-ready bundle is served via `vite preview` on port `4173`.
- **API endpoint discovery:** The build argument and environment variable `VITE_API_BASE_URL` point to the backend (defaults to `http://localhost:8000`).
- **Caching:** Node installation caches are stored in the `node-modules-cache` volume for faster rebuilds.

## Smoke testing the stack

Use the default SMILES value (`C1=CC=CC=C1`) in the UI form to verify end-to-end functionality. A successful round-trip should display the RDKit-derived summary (atom, bond, and ring counts) returned from the backend.

To rebuild the images without starting containers, run `docker compose build`. To stop and remove the stack, run:

```bash
docker compose down
```

## Development notes

- The project still supports local development without Docker if preferred. Install the dependencies under `backend/` and `frontend/` and run the services manually.
- When running inside Docker, update the `.env` file to customise ports or override the backend URL exposed to the frontend.
