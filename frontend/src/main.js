import './style.css';
import * as THREE from 'three';

const app = document.querySelector('#app');
const fallbackBaseUrl = `${window.location.protocol}//${window.location.hostname}:8000`;
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? fallbackBaseUrl;

app.innerHTML = `
  <main>
    <canvas id="scene-canvas" width="480" height="480"></canvas>
    <section>
      <h1>Molecule Visualizer</h1>
      <p>
        This prototype connects to a RDKit-powered backend. Enter a SMILES string to
        see how many atoms, bonds, and rings RDKit detects.
      </p>
      <form id="smiles-form">
        <input
          id="smiles-input"
          type="text"
          placeholder="Enter SMILES (e.g. C1=CC=CC=C1)"
          value="C1=CC=CC=C1"
        />
        <button type="submit">Analyze with RDKit</button>
      </form>
      <pre id="response-panel">Awaiting analysis...</pre>
    </section>
  </main>
`;

const canvas = document.getElementById('scene-canvas');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);

const scene = new THREE.Scene();
scene.background = new THREE.Color('#020617');

const camera = new THREE.PerspectiveCamera(
  45,
  canvas.clientWidth / canvas.clientHeight,
  0.1,
  100
);
camera.position.set(4, 4, 6);

const ambientLight = new THREE.AmbientLight('#f8fafc', 0.6);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight('#60a5fa', 1.2);
directionalLight.position.set(5, 5, 5);
scene.add(directionalLight);

const nucleus = new THREE.Mesh(
  new THREE.IcosahedronGeometry(1.6, 1),
  new THREE.MeshStandardMaterial({
    color: '#38bdf8',
    metalness: 0.35,
    roughness: 0.2,
  })
);
scene.add(nucleus);

const electronMaterial = new THREE.MeshStandardMaterial({ color: '#a855f7' });
const ringGeometry = new THREE.TorusGeometry(2.5, 0.08, 16, 100);
const orbit = new THREE.Mesh(ringGeometry, electronMaterial);
scene.add(orbit);

const electron = new THREE.Mesh(
  new THREE.SphereGeometry(0.2, 32, 32),
  new THREE.MeshStandardMaterial({ color: '#facc15' })
);
electron.position.x = 2.5;
scene.add(electron);

function animate() {
  requestAnimationFrame(animate);
  nucleus.rotation.x += 0.0025;
  nucleus.rotation.y += 0.0035;
  orbit.rotation.z += 0.0015;
  electron.position.applyAxisAngle(new THREE.Vector3(0, 0, 1), 0.005);
  renderer.render(scene, camera);
}

animate();

window.addEventListener('resize', () => {
  const { clientWidth, clientHeight } = canvas;
  renderer.setSize(clientWidth, clientHeight, false);
  camera.aspect = clientWidth / clientHeight;
  camera.updateProjectionMatrix();
});

document.getElementById('smiles-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = document.getElementById('smiles-input');
  const panel = document.getElementById('response-panel');
  panel.textContent = 'Contacting backend...';

  try {
    const response = await fetch(
      `${apiBaseUrl}/molecule/summary?smiles=${encodeURIComponent(input.value.trim())}`
    );

    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.detail ?? 'Unexpected error');
    }

    const summary = await response.json();
    panel.textContent = JSON.stringify(summary, null, 2);
  } catch (error) {
    panel.textContent = `Unable to analyze molecule: ${error.message}`;
  }
});
