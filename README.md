# Molecule Visualizer

A lightweight Three.js playground that showcases a molecule-inspired scene with smooth orbit controls. The project is intentionally minimal and ships with a Vite-powered development server so you can iterate without any additional tooling.

## Prerequisites

- [Node.js **20**](https://nodejs.org/) (includes npm 10)
- A WebGL-capable browser such as the latest Chrome, Edge, or Firefox

> ℹ️ The project does not require a backend. Everything is rendered client side.

## Getting started

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
3. Open the app in your browser at [http://localhost:5173](http://localhost:5173). Vite will log the exact URL in the terminal. The scene hot-reloads as you edit the files inside `src/`.

## Available npm scripts

| Command | Description |
| ------- | ----------- |
| `npm run dev` | Starts the Vite development server on port **5173** with hot module replacement. |
| `npm run build` | Produces an optimized production bundle inside the `dist/` directory. |
| `npm run preview` | Serves the production bundle locally on port **4173** (useful smoke test before deploying). |

## Project structure

```
.
├── index.html          # Entry HTML file loaded by Vite
├── package.json        # Dependencies and npm scripts
├── src/
│   ├── main.js         # Three.js scene setup and animation loop
│   └── style.css       # Layout and visual styles for the demo
├── vite.config.js      # Vite dev/preview configuration
└── .gitignore          # Ignores node_modules, build output, etc.
```

The Three.js scene renders a glowing nucleus, an orbiting electron, and atmospheric lighting. Orbit controls are enabled by default:

- **Drag** with the left mouse button to orbit the camera.
- **Right-click + drag** to pan the view.
- **Scroll** to zoom in and out.

## Troubleshooting

- **"Cannot find module 'three'"** – Ensure `npm install` completed successfully. Delete `node_modules/` and retry if necessary.
- **Blank canvas or WebGL errors** – Verify that your browser supports WebGL and GPU acceleration is enabled. Visit [https://get.webgl.org/](https://get.webgl.org/) to confirm support.
- **Port already in use** – If port 5173 or 4173 is occupied, stop the conflicting process or pass a new port (`npm run dev -- --port 5174`).
- **Launched directly from the filesystem** – Opening `index.html` via the `file://` protocol will trigger CORS/ESM errors. Always run through the dev server or a static host.
- **Security tooling blocks local ESM imports** – Some corporate proxies may block `node_modules/.vite` assets. Add the project directory to your allow list or try using a different network.

## Deployment

Run `npm run build` and deploy the generated `dist/` directory to any static hosting service (Netlify, GitHub Pages, Vercel, S3, etc.). The app does not rely on server-side rendering or backend APIs.

---

Happy hacking! 🎉
