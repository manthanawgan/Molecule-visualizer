# Molecule Visualizer Monorepo

This repository bundles a FastAPI backend powered by RDKit with a Three.js + Vite frontend. The entire stack is containerised so that the only local dependency required is Docker (with Compose v2).
A lightweight mono-repository that hosts a Vite-powered React prototype for the molecule visualizer alongside a FastAPI backend scaffold. The project ships with Docker tooling so new contributors can spin everything up with a single command.

## Repository layout

```
.
├── backend/                 # FastAPI application and Python dependencies
│   ├── app/
│   │   ├── __init__.py      # FastAPI app factory and health route
│   │   ├── asgi.py          # ASGI entrypoint for deployment
│   │   ├── main.py          # Local development entrypoint
│   │   └── models.py        # Pydantic models shared across the API
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/                # Vite + React + Tailwind frontend
│   ├── index.html
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── styles/
│   │   └── lib/
│   └── public/
│       └── samples/
├── docker-compose.yml       # Development services for the monorepo
├── .editorconfig
├── .env.example
├── .gitignore
├── .vscode/settings.json
└── LICENSE
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
> The repository no longer requires local Node.js or Python installations when you rely on Docker Compose.

## Quick start with Docker Compose

1. Copy the environment template if you want to override ports or URLs:

   ```bash
   cp .env.example .env
   ```

2. Start the development stack:

   ```bash
   docker compose up
   ```

   The first boot installs JavaScript and Python dependencies inside the containers. Subsequent runs will reuse the cached modules.

3. Visit the services:

   - Frontend: [http://localhost:5173](http://localhost:5173)
   - Backend health probe: [http://localhost:8000/health](http://localhost:8000/health)

   Any code changes under `frontend/` or `backend/` are hot-reloaded thanks to the bind mounts.

4. Stop the stack with <kbd>Ctrl</kbd>+<kbd>C</kbd> or by running:

   ```bash
   docker compose down
   ```

### Environment variables

The Compose file respects a few shared variables so that both services agree on ports and URLs.

| Variable | Default | Description |
| --- | --- | --- |
| `FRONTEND_PORT` | `5173` | Host port that proxies to the Vite dev server inside the `frontend` container. |
| `BACKEND_PORT` | `8000` | Host port that proxies to the FastAPI server. |
| `API_BASE_URL` | `http://backend:8000` | Injected into the frontend container for backwards compatibility and used to derive the Vite configuration. |
| `VITE_API_BASE_URL` | `http://backend:8000` | Base URL the frontend reads at runtime when issuing API calls. |

Update `.env` to customise the values. Docker Compose will automatically read the file.

## Working on the frontend locally

If you prefer to run the frontend without Docker:

```bash
cd frontend
npm install
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173). The Vite dev server hot-reloads React components from `frontend/src`. Global styles live in `src/styles/index.css`, and the example molecule files remain under `frontend/public/samples/`.

Create a `.env` file inside `frontend/` and set `VITE_API_BASE_URL` if you need to point the app at a backend running on a different host.

## Working on the backend locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000uvicorn backend.app:app --reload --port 8000
```

The backend currently exposes a `/health` route and initial Pydantic models that describe atoms, bonds, metadata, and molecule payloads. Molecules are stored in-memory in a dictionary keyed by `UUID` until persistence is introduced.

Run the automated backend tests with:

```bash
cd backend
pytest
```

## License

Released under the [MIT License](./LICENSE).
