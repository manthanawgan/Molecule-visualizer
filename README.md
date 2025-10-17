# Molecule Visualizer Monorepo

A lightweight mono-repository that hosts the static Three.js prototype for the molecule visualizer alongside a FastAPI backend scaffold. The project ships with Docker tooling so new contributors can spin everything up with a single command.

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
├── frontend/                # Static assets served by a Node dev server
│   ├── package.json
│   ├── package-lock.json
│   └── public/
│       ├── index.html
│       ├── main.js
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
| `FRONTEND_PORT` | `5173` | Host port that proxies to the Node static server inside the `frontend` container. |
| `BACKEND_PORT` | `8000` | Host port that proxies to the FastAPI server. |
| `API_BASE_URL` | `http://backend:8000` | Injected into the frontend container so it knows how to reach the backend service. |

Update `.env` to customise the values. Docker Compose will automatically read the file.

## Working on the frontend locally

If you prefer to run the frontend without Docker:

```bash
cd frontend
npm install
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173). The dev server streams the static files from `frontend/public/`. Update `main.js` to mount your Three.js scene and use the molecules under `frontend/public/samples/` during development.

## Working on the backend locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend currently exposes a `/health` route and initial Pydantic models that describe atoms, bonds, metadata, and molecule payloads. Molecules are stored in-memory in a dictionary keyed by `UUID` until persistence is introduced.

Run the automated backend tests with:

```bash
cd backend
pytest
```

## License

Released under the [MIT License](./LICENSE).
