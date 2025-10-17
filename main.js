const SAMPLE_PDB = `HEADER    BENZENE
HETATM    1  C1  BEN A   1       1.396   0.000   0.000  1.00  0.00           C
HETATM    2  C2  BEN A   1       0.698   1.209   0.000  1.00  0.00           C
HETATM    3  C3  BEN A   1      -0.698   1.209   0.000  1.00  0.00           C
HETATM    4  C4  BEN A   1      -1.396   0.000   0.000  1.00  0.00           C
HETATM    5  C5  BEN A   1      -0.698  -1.209   0.000  1.00  0.00           C
HETATM    6  C6  BEN A   1       0.698  -1.209   0.000  1.00  0.00           C
HETATM    7  H1  BEN A   1       2.479   0.000   0.000  1.00  0.00           H
HETATM    8  H2  BEN A   1       1.240   2.154   0.000  1.00  0.00           H
HETATM    9  H3  BEN A   1      -1.240   2.154   0.000  1.00  0.00           H
HETATM   10  H4  BEN A   1      -2.479   0.000   0.000  1.00  0.00           H
HETATM   11  H5  BEN A   1      -1.240  -2.154   0.000  1.00  0.00           H
HETATM   12  H6  BEN A   1       1.240  -2.154   0.000  1.00  0.00           H
CONECT    1    2    6    7
CONECT    2    1    3    8
CONECT    3    2    4    9
CONECT    4    3    5   10
CONECT    5    4    6   11
CONECT    6    1    5   12
CONECT    7    1
CONECT    8    2
CONECT    9    3
CONECT   10    4
CONECT   11    5
CONECT   12    6
END
`;

const BASE_STYLE = {
  stick: {
    colorscheme: 'Jmol',
    radius: 0.18,
  },
};

const HIGHLIGHT_COLORS = ['#fb7185', '#38bdf8'];

const HIGHLIGHT_STYLES = HIGHLIGHT_COLORS.map((color) => ({
  stick: { color, radius: 0.26 },
  sphere: { radius: 0.55, color, opacity: 0.85 },
}));

function initializeMoleculeViewer() {
  const viewerContainer = document.getElementById('viewer-canvas');
  const selectionSlots = [
    document.querySelector('[data-slot="first"]'),
    document.querySelector('[data-slot="second"]'),
  ];
  const selectionValues = [
    document.getElementById('selection-first'),
    document.getElementById('selection-second'),
  ];
  const distanceEl = document.getElementById('distance-readout');
  const statusEl = document.getElementById('selection-status');
  const clearButton = document.getElementById('clear-selection');

  if (!viewerContainer) {
    console.error('Molecule viewer container was not found in the document.');
    return;
  }

  if (typeof window.$3Dmol === 'undefined') {
    const message = '3Dmol.js could not be loaded. Please check your network connection.';
    console.error(message);
    if (statusEl) {
      statusEl.textContent = message;
    }
    return;
  }

  const viewer = $3Dmol.createViewer(viewerContainer, {
    backgroundColor: '#020617',
    antialias: true,
  });

  const model = viewer.addModel(SAMPLE_PDB, 'pdb');
  const selectedAtoms = [];
  let measurementShape = null;

  function copyAtom(atom) {
    return {
      serial: atom.serial,
      atom: atom.atom,
      elem: atom.elem,
      resn: atom.resn,
      resi: atom.resi,
      chain: atom.chain,
      x: atom.x,
      y: atom.y,
      z: atom.z,
    };
  }

  function computeDistance(left, right) {
    const dx = left.x - right.x;
    const dy = left.y - right.y;
    const dz = left.z - right.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  function formatAtom(atom) {
    const name = atom.atom ? atom.atom.trim() : atom.elem || 'Atom';
    const location = [atom.resn, atom.resi, atom.chain]
      .filter((part) => part !== undefined && part !== null && String(part).trim() !== '')
      .map((part) => String(part).trim())
      .join(' ');

    const coordinates = [atom.x, atom.y, atom.z]
      .map((value) => (typeof value === 'number' ? value.toFixed(2) : '0.00'))
      .join(', ');

    const locationText = location ? ` • ${location}` : '';
    return `${name} (serial ${atom.serial})${locationText} • [${coordinates}]`;
  }

  function applyStyles() {
    model.setStyle({}, BASE_STYLE);
    selectedAtoms.forEach((atom, index) => {
      model.setStyle({ serial: atom.serial }, HIGHLIGHT_STYLES[index]);
    });
  }

  function updateMeasurementVisual() {
    if (measurementShape) {
      viewer.removeShape(measurementShape);
      measurementShape = null;
    }

    if (selectedAtoms.length === 2) {
      const [first, second] = selectedAtoms;
      measurementShape = viewer.addCylinder({
        start: { x: first.x, y: first.y, z: first.z },
        end: { x: second.x, y: second.y, z: second.z },
        radius: 0.05,
        color: '#fde047',
        opacity: 0.95,
      });
    }
  }

  function refreshScene() {
    applyStyles();
    updateMeasurementVisual();
    viewer.render();
  }

  function emitSelectionChange(distance) {
    const detail = {
      atoms: selectedAtoms.map((atom, index) => ({
        index,
        serial: atom.serial,
        element: atom.elem,
        name: atom.atom,
        residue: atom.resn,
        residueIndex: atom.resi,
        chain: atom.chain,
        coordinates: { x: atom.x, y: atom.y, z: atom.z },
      })),
      distance,
    };

    const event = new CustomEvent('atomselectionchange', {
      detail,
      bubbles: true,
    });

    viewerContainer.dispatchEvent(event);
  }

  function updateUI() {
    let currentDistance = null;

    selectionValues.forEach((node, index) => {
      const slot = selectionSlots[index];
      const atom = selectedAtoms[index];
      if (atom) {
        node.textContent = formatAtom(atom);
        slot?.classList.add('is-selected');
      } else {
        node.textContent = 'None selected';
        slot?.classList.remove('is-selected');
      }
    });

    if (selectedAtoms.length === 2) {
      currentDistance = computeDistance(selectedAtoms[0], selectedAtoms[1]);
      if (distanceEl) {
        distanceEl.textContent = `Distance: ${currentDistance.toFixed(2)} Å`;
      }
    } else if (distanceEl) {
      distanceEl.textContent = 'Distance: --';
    }

    if (statusEl) {
      if (selectedAtoms.length === 0) {
        statusEl.textContent = 'Click atoms in the molecule to select up to two at a time.';
      } else if (selectedAtoms.length === 1) {
        statusEl.textContent = 'First atom selected. Select another atom to measure the distance between them.';
      } else {
        statusEl.textContent = 'Two atoms selected. Distance measurement is shown below.';
      }
    }

    if (clearButton) {
      clearButton.disabled = selectedAtoms.length === 0;
    }

    emitSelectionChange(currentDistance);
  }

  function handleSelection(atom) {
    if (!atom || typeof atom.serial === 'undefined') {
      return;
    }

    const existingIndex = selectedAtoms.findIndex((entry) => entry.serial === atom.serial);
    if (existingIndex !== -1) {
      selectedAtoms.splice(existingIndex, 1);
    } else {
      if (selectedAtoms.length === 2) {
        selectedAtoms.shift();
      }
      selectedAtoms.push(copyAtom(atom));
    }

    refreshScene();
    updateUI();
  }

  function clearSelection() {
    if (selectedAtoms.length === 0) {
      return;
    }

    selectedAtoms.length = 0;
    refreshScene();
    updateUI();
  }

  if (typeof viewer.setClickable === 'function') {
    viewer.setClickable({}, true, (atom) => {
      handleSelection(atom);
    });
  } else if (typeof viewer.setClick === 'function') {
    viewer.setClick((atom) => {
      handleSelection(atom);
    });
  } else {
    console.warn('Clickable atom support is unavailable in this version of 3Dmol.js.');
  }

  refreshScene();
  viewer.zoomTo();
  viewer.render();
  updateUI();

  if (clearButton) {
    clearButton.addEventListener('click', () => {
      clearSelection();
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeMoleculeViewer);
} else {
  initializeMoleculeViewer();
}
