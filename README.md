# Molecule Visualizer

Minimal scaffolding for an in-browser molecule visualizer that combines a WebGL front-end with an RDKit-powered analysis backend. The current repository contains the static HTML entry point, an ES module placeholder, and a curated set of sample molecule files that you can use while iterating on the renderer and API surface.

---

## Prerequisites

| Tooling | Recommended version | Notes |
| --- | --- | --- |
| **Python** | 3.10+ | Required for tooling scripts and any RDKit-backed API experiments. |
| **Node.js** | 18+ (LTS) | Used for front-end tooling (bundlers, dev servers, linting). Install via [nodejs.org](https://nodejs.org) or a version manager such as [fnm](https://github.com/Schniz/fnm) / [nvm](https://github.com/nvm-sh/nvm). |
| **RDKit** | 2022.09+ | Needed for generating conformers, measurements, and format conversions. Best installed through Conda / Mamba. |
| **Docker** | 24+ | Optional, but recommended for reproducible development environments. |

### Installing RDKit locally

<details>
<summary><strong>Conda / Mamba (recommended)</strong></summary>

```bash
# Create an isolated environment with Python and RDKit
mamba create -n molecule-viz python=3.11 rdkit -c conda-forge
mamba activate molecule-viz
```

If you prefer Conda, replace `mamba` with `conda`.
</details>

<details>
<summary><strong>Pip wheels</strong></summary>

Unofficial wheels are published for macOS (x86/ARM) and Linux. After ensuring you have the system dependencies (Boost, Eigen, Cairo), install via:

```bash
python -m pip install rdkit-pypi
```

Refer to the [rdkit-pypi project](https://github.com/rdkit/rdkit-pypi) for platform caveats.
</details>

<details>
<summary><strong>Using the official RDKit Docker image</strong></summary>

```bash
docker pull rdkit/rdkit:latest
```

This base image contains a Conda environment with RDKit pre-installed and is the foundation for the workflow documented below.
</details>

---

## Repository structure

```
.
├── 3dmodels.html        # Static entry page that bootstraps the viewer
├── main.js              # ES module stub that will load the viewer logic
├── samples/             # Curated molecule files in multiple industry formats
│   ├── co2.xyz
│   ├── methane.mol
│   ├── water.pdb
│   └── water.sdf
└── README.md
```

The codebase is intentionally lean. When you start adding a renderer, data loader, or backend, prefer colocating source under `src/` or `backend/` directories to keep the root tidy.

---

## Environment setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-org>/molecule-visualizer.git
   cd molecule-visualizer
   ```

2. **Set up a Python environment (optional, but required for RDKit workflows)**
   ```bash
   mamba activate molecule-viz  # or: conda activate molecule-viz
   # Alternatively, use venv
   python -m venv .venv
   source .venv/bin/activate
   pip install rdkit-pypi  # if you are not using the Conda environment
   ```

3. **Bootstrap front-end tooling**
   ```bash
   npm init -y                      # creates package.json if it does not exist yet
   npm install three                # required by main.js
   npm install --save-dev vite      # simple dev server that resolves bare imports
   ```

   Once a Vite configuration is in place, the `three` dependency will be bundled automatically. Until then, you can temporarily reference the Skypack CDN in `main.js` while prototyping.

4. **Download or generate molecule assets** – sample files are already checked into `samples/`. Add your own RDKit-generated structures in the same directory to rapidly iterate without additional I/O setup.

---

## Running the front-end

Because the repo currently ships only static assets, use a dev server that supports ES module bare import rewriting (for the `three` dependency):

```bash
npx vite --config ./vite.config.js --root .
```

If you do not have a Vite config yet, launch Vite in middleware mode and provide a minimal config:

```bash
# vite.config.js
import { defineConfig } from "vite";

export default defineConfig({
  root: '.',
  server: {
    port: 5173,
    open: '/3dmodels.html'
  }
});
```

Once the dev server is running, visit [http://localhost:5173/3dmodels.html](http://localhost:5173/3dmodels.html). Replace the placeholder logic in `main.js` with a `THREE.Scene`, loader, and controls. The sample molecules can be fetched with standard `fetch` APIs.

To serve the static assets without module rewriting (for quick demos), fall back to Python’s HTTP server:

```bash
python -m http.server 8000
# Visit http://localhost:8000/3dmodels.html
```

> **Note:** The bare `import 'three'` statement requires bundler support. Without Vite (or a similar tool like Snowpack, Parcel, or webpack), swap it for `import * as THREE from 'https://cdn.skypack.dev/three';` during rapid prototyping.

---

## Running (or prototyping) the backend

A production-grade backend is not yet committed. Until that lands, you have two options:

1. **Prototype locally with RDKit scripts**
   ```bash
   python
   >>> from rdkit import Chem
   >>> mol = Chem.MolFromMolFile('samples/methane.mol', removeHs=False)
   >>> mol.GetNumAtoms()
   5
   ```

2. **Spin up a FastAPI stub** (recommended when designing contracts)
   ```bash
   pip install fastapi uvicorn rdkit-pypi
   uvicorn backend.api:app --reload --port 8001
   ```

   Where `backend/api.py` contains:
   ```python
   from fastapi import FastAPI
   from rdkit import Chem

   app = FastAPI()

   @app.get("/health")
   async def health():
       return {"status": "ok"}

   @app.post("/api/molecules")
   async def load_molecule(file_path: str):
       mol = Chem.MolFromMolFile(file_path)
       if mol is None:
           return {"ok": False, "error": "Unable to parse molecule"}
       return {"ok": True, "atoms": mol.GetNumAtoms()}
   ```

   The stub demonstrates the expected RDKit workflow and is the reference implementation for the API contract outlined below.

---

## HTTP API reference (draft)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Liveness probe. Returns `{ "status": "ok" }`. |
| `POST` | `/api/molecules` | Accepts a molecule payload (file path or raw text) and returns parsed metadata needed by the viewer. |
| `POST` | `/api/molecules/measure` | Accepts atom indices and returns bond length / angle measurements computed via RDKit. |
| `POST` | `/api/molecules/conformers` | (Planned) Generates 3D conformers for a supplied molecule. |

### Sample request

```bash
curl -X POST http://localhost:8001/api/molecules \
     -H "Content-Type: application/json" \
     -d '{"file_path": "samples/methane.mol"}'
```

### Sample response

```json
{
  "ok": true,
  "atoms": 5,
  "formula": "CH4",
  "boundingBox": {
    "min": [-0.6291, -0.6291, -0.6291],
    "max": [0.6291, 0.6291, 0.6291]
  }
}
```

Treat the schema as a living document; update it alongside backend code as the project matures.

---

## Sample molecules

Four representative molecules are tracked under `samples/`:

| File | Format | Description |
| --- | --- | --- |
| `water.sdf` | SDF | Three-atom water molecule, ideal for measurement demos. |
| `methane.mol` | MOL V2000 | Methane with explicit hydrogens; showcases tetrahedral geometry. |
| `water.pdb` | PDB | Water molecule encoded as a protein databank record. |
| `co2.xyz` | XYZ | Carbon dioxide linear molecule for testing alignment tools. |

Drag these files into your viewer or load them via `fetch('/samples/water.sdf')`. They also double as fixtures for backend parsing tests.

---

## Docker workflow

The recommended approach leverages the official RDKit image as a base while layering Node.js for the front-end toolchain.

```Dockerfile
# docker/Dockerfile.dev
FROM rdkit/rdkit:latest

# Install Node via nvm
ENV NODE_VERSION=18.19.0
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \
 && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash \
 && . "$HOME/.nvm/nvm.sh" && nvm install ${NODE_VERSION} && nvm alias default ${NODE_VERSION}

WORKDIR /opt/molecule-visualizer
COPY . .

# Default command opens a shell; override in docker-compose
CMD ["/bin/bash"]
```

### Build & run

```bash
# Build the dev image (assumes the file above is saved as docker/Dockerfile.dev)
docker build -f docker/Dockerfile.dev -t molecule-viz-dev .

# Launch an interactive container with the repo mounted
docker run --rm -it \
  -p 5173:5173 \
  -p 8001:8001 \
  -v "$PWD":/opt/molecule-visualizer \
  molecule-viz-dev bash

# Inside the container
direnv allow  # if you rely on direnv for environment activation
npx vite --open
```

Using Compose:

```yaml
# docker-compose.dev.yml
services:
  app:
    image: molecule-viz-dev
    build:
      context: .
      dockerfile: docker/Dockerfile.dev
    volumes:
      - .:/opt/molecule-visualizer
    ports:
      - "5173:5173"
      - "8001:8001"
    command: ["npx", "vite", "--host", "0.0.0.0"]
```

> **Tip:** If you only need RDKit utilities, skip building a custom image and run `docker run --rm -it rdkit/rdkit:latest` directly, mounting your `samples/` directory for interactive use.

---

## Measurement tool usage

Once the Three.js viewer is wired up, the measurement overlay exposes quick bond/angle interrogation:

1. **Toggle measurement mode** – Press <kbd>M</kbd> or click the ruler icon in the UI toolbar.
2. **Pick atoms or atoms & bonds** – Left-click the first atom, then the second (for distances) or third (for angles). Selected atoms are highlighted in yellow.
3. **Readouts** – Measurements appear in the top-right HUD and persist in the console for copy/paste.
4. **Reset** – Press <kbd>Esc</kbd> or right-click to clear selections.

Behind the scenes, the viewer will call the `/api/molecules/measure` endpoint documented above. If you are experimenting without the backend, import RDKit directly in the browser (via WebAssembly builds) or proxy the call to a local FastAPI stub.

---

## Troubleshooting RDKit installation

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `ImportError: libRDKitChem.so: cannot open shared object file` | Missing runtime libraries on Linux | Install system deps: `apt-get install libboost-all-dev libeigen3-dev libcairo2` or use the Conda package. |
| `Unsatisfied dependency: GLIBCXX_3.4.29` | Old GCC / libstdc++ | Use the Conda forge toolchain or update your compiler (`sudo apt-get install g++-11`). |
| Wheels unavailable for platform | Apple Silicon / Windows | Prefer the Conda build, or run inside `rdkit/rdkit:latest` Docker image. |
| Vite cannot parse RDKit output | Large files streamed | Enable chunked streaming in your backend and keep JSON payloads under a few MB. |

If you are blocked on binary installs, plan to develop exclusively inside Docker to sidestep host compatibility issues.

---

## Linting & testing

Even though formal tooling has not been committed yet, the project expects the following workflows:

```bash
# Front-end linting (requires eslint)
npx eslint main.js

# Back-end unit tests (once API modules exist)
pytest

# Type checks for future TypeScript migration
npx tsc --noEmit
```

Add configuration files (`.eslintrc.cjs`, `pytest.ini`, `tsconfig.json`) as the codebase grows. Wire the commands into a pre-commit hook or CI pipeline to keep contributions standardized.

---

## Additional resources

- [RDKit Documentation](https://www.rdkit.org/docs/) – API reference and cookbook recipes.
- [Three.js Fundamentals](https://threejs.org/docs/index.html#manual/en/introduction/Creating-a-scene) – Primer for building scenes, cameras, and controls.
- [Awesome Molecule Visualization](https://github.com/appsforchemistry/awesome-molecule-visualization) – Survey of libraries and viewers for inspiration.

Contributions are welcome! Please file an issue outlining the feature or bug before submitting a pull request so we can keep the roadmap aligned.
