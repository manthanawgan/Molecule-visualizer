import './style.css';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const canvas = document.getElementById('molecule-canvas');
const statusEl = document.getElementById('loading-indicator');
const viewerContainer = document.getElementById('viewer');
const viewerStatusEl = document.getElementById('viewer-status');

let moleculeViewer = null;
let viewerResizeObserver = null;
let hasBoundViewerResizeListener = false;

if (!(canvas instanceof HTMLCanvasElement)) {
  throw new Error('Unable to find target canvas element.');
}

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color('#020617');
scene.fog = new THREE.Fog('#020617', 16, 42);

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
camera.position.set(6.5, 5.5, 7.5);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.autoRotate = false;
controls.target.set(0, 0, 0);
controls.maxDistance = 20;
controls.minDistance = 2.5;
controls.update();

const hemisphereLight = new THREE.HemisphereLight('#f8fafc', '#0f172a', 0.95);
scene.add(hemisphereLight);

const keyLight = new THREE.SpotLight('#60a5fa', 2.2, 45, Math.PI / 8, 0.2, 0.8);
keyLight.position.set(9, 12, 7);
keyLight.castShadow = true;
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight('#facc15', 0.75);
fillLight.position.set(-8, 4, -6);
scene.add(fillLight);

const rimLight = new THREE.PointLight('#a855f7', 0.9, 30, 2);
rimLight.position.set(0, 6, 0);
scene.add(rimLight);

const nucleus = new THREE.Mesh(
  new THREE.IcosahedronGeometry(1.8, 1),
  new THREE.MeshStandardMaterial({
    color: '#38bdf8',
    metalness: 0.45,
    roughness: 0.18,
    emissive: '#0ea5e9',
    emissiveIntensity: 0.25,
    flatShading: true,
  })
);
nucleus.castShadow = true;
scene.add(nucleus);

const orbitGroup = new THREE.Group();
scene.add(orbitGroup);

const orbitTrail = new THREE.Mesh(
  new THREE.TorusGeometry(3.2, 0.06, 32, 256),
  new THREE.MeshStandardMaterial({
    color: '#a855f7',
    emissive: '#9333ea',
    emissiveIntensity: 0.75,
    metalness: 0.35,
    roughness: 0.12,
  })
);
orbitTrail.receiveShadow = true;
orbitGroup.add(orbitTrail);

const electron = new THREE.Mesh(
  new THREE.SphereGeometry(0.28, 32, 32),
  new THREE.MeshStandardMaterial({
    color: '#facc15',
    emissive: '#facc15',
    emissiveIntensity: 0.45,
    roughness: 0.35,
  })
);
electron.position.x = 3.2;
electron.castShadow = true;
orbitGroup.add(electron);

const lattice = new THREE.Mesh(
  new THREE.RingGeometry(4.2, 6.5, 64, 1),
  new THREE.MeshStandardMaterial({
    color: '#0f172a',
    transparent: true,
    opacity: 0.22,
    side: THREE.DoubleSide,
  })
);
lattice.rotation.x = -Math.PI / 2;
lattice.position.y = -2.1;
scene.add(lattice);

const groundHelper = new THREE.GridHelper(18, 18, '#1e293b', '#1e293b');
groundHelper.material.opacity = 0.1;
groundHelper.material.transparent = true;
groundHelper.position.y = -2.1;
scene.add(groundHelper);

const clock = new THREE.Clock();

function setRendererSize() {
  const parent = canvas.parentElement;
  const width = Math.max(16, parent?.clientWidth ?? canvas.clientWidth ?? window.innerWidth);
  const provisionalHeight = parent?.clientHeight ?? canvas.clientHeight ?? Math.floor(width * 0.75);
  const height = Math.max(16, provisionalHeight);

  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function animate() {
  const elapsed = clock.getElapsedTime();

  nucleus.rotation.x = 0.3 * elapsed;
  nucleus.rotation.y = 0.4 * elapsed;
  orbitGroup.rotation.y = 0.85 * elapsed;
  electron.position.y = Math.sin(elapsed * 2.2) * 0.18;

  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

function initialise() {
  setRendererSize();
  renderer.render(scene, camera);
  animate();

  if (statusEl) {
    statusEl.textContent = 'Scene ready';
    statusEl.setAttribute('aria-hidden', 'true');
    window.setTimeout(() => statusEl.classList.add('is-hidden'), 220);
  }
}

function handleViewerResize() {
  if (moleculeViewer) {
    moleculeViewer.resize();
    moleculeViewer.render();
  }
}

function initialiseMoleculeViewer() {
  if (!(viewerContainer instanceof HTMLElement)) {
    console.warn('Skipping 3Dmol viewer initialisation: target container not found.');
    return;
  }

  if (moleculeViewer) {
    handleViewerResize();
    return;
  }

  const mol = window.$3Dmol;

  if (!mol) {
    console.error('3Dmol.js failed to load. Ensure the CDN script tag is available.');
    if (viewerStatusEl) {
      viewerStatusEl.classList.remove('is-hidden');
      viewerStatusEl.setAttribute('aria-hidden', 'false');
      viewerStatusEl.textContent = '3Dmol.js library unavailable.';
    }
    return;
  }

  try {
    if (viewerStatusEl) {
      viewerStatusEl.classList.remove('is-hidden');
      viewerStatusEl.setAttribute('aria-hidden', 'false');
      viewerStatusEl.textContent = 'Loading sample molecule…';
    }

    moleculeViewer = mol.createViewer(viewerContainer, {
      backgroundColor: '#020617',
      defaultcolors: mol.rasmolElementColors,
    });

    if (!hasBoundViewerResizeListener) {
      window.addEventListener('resize', handleViewerResize);
      hasBoundViewerResizeListener = true;
    }

    if (viewerResizeObserver) {
      viewerResizeObserver.disconnect();
    }

    if (typeof ResizeObserver !== 'undefined') {
      viewerResizeObserver = new ResizeObserver(handleViewerResize);
      viewerResizeObserver.observe(viewerContainer);
    }

    handleViewerResize();

    mol.download(
      'pdb:1CRN',
      moleculeViewer,
      {},
      () => {
        moleculeViewer.setStyle({}, { cartoon: { color: 'spectrum' } });
        moleculeViewer.addStyle({ hetflag: true }, { stick: { radius: 0.25, colorscheme: 'greenCarbon' } });
        moleculeViewer.zoomTo();
        moleculeViewer.render();
        if (typeof moleculeViewer.zoom === 'function') {
          moleculeViewer.zoom(1.05, 500);
        }
        if (typeof moleculeViewer.spin === 'function') {
          moleculeViewer.spin(true);
        }

        if (viewerStatusEl) {
          viewerStatusEl.textContent = 'Sample molecule loaded';
          viewerStatusEl.setAttribute('aria-hidden', 'true');
          window.setTimeout(() => viewerStatusEl.classList.add('is-hidden'), 220);
        }
      },
      (error) => {
        console.error('Failed to load sample molecule (PDB 1CRN).', error);
        if (viewerStatusEl) {
          viewerStatusEl.classList.remove('is-hidden');
          viewerStatusEl.setAttribute('aria-hidden', 'false');
          viewerStatusEl.textContent = 'Unable to load sample molecule.';
        }
      }
    );
  } catch (error) {
    console.error('Failed to initialise 3Dmol viewer.', error);
    if (viewerStatusEl) {
      viewerStatusEl.classList.remove('is-hidden');
      viewerStatusEl.setAttribute('aria-hidden', 'false');
      viewerStatusEl.textContent = 'Unable to initialise molecule viewer.';
    }
  }
}

if (typeof ResizeObserver !== 'undefined') {
  const resizeObserver = new ResizeObserver(() => {
    setRendererSize();
  });
  resizeObserver.observe(canvas.parentElement ?? canvas);
}

window.addEventListener('resize', setRendererSize);

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialiseMoleculeViewer);
} else {
  initialiseMoleculeViewer();
}

initialise();
