import * as React from 'https://esm.sh/react@18?dev';
import { createRoot } from 'https://esm.sh/react-dom@18/client?dev';
import { MoleculeViewer } from './components/MoleculeViewer.js';
import { sampleMolecules } from './data/sampleMolecules.js';

const { useState, useMemo } = React;

function App() {
  const [selectedId, setSelectedId] = useState(sampleMolecules[0]?.id ?? null);

  const selectedEntry = useMemo(() => {
    const fallback = sampleMolecules[0] ?? null;
    if (!selectedId) {
      return fallback;
    }
    return sampleMolecules.find((item) => item.id === selectedId) ?? fallback;
  }, [selectedId]);

  if (!selectedEntry) {
    return React.createElement(
      'div',
      { className: 'app-shell' },
      React.createElement(
        'p',
        null,
        'No sample molecules configured. Add entries to sampleMolecules.js to get started.',
      ),
    );
  }

  const header = React.createElement(
    'header',
    { className: 'app-header' },
    [
      React.createElement('h1', { key: 'title' }, 'Molecule Visualizer'),
      React.createElement(
        'p',
        { key: 'subtitle' },
        'Interact with sample molecules powered by the 3Dmol.js renderer.',
      ),
    ],
  );

  const selector = React.createElement(
    'div',
    { className: 'molecule-selector' },
    [
      React.createElement(
        'label',
        { key: 'label', htmlFor: 'molecule-select' },
        'Choose a molecule',
      ),
      React.createElement(
        'select',
        {
          key: 'select',
          id: 'molecule-select',
          value: selectedEntry.id,
          onChange: (event) => setSelectedId(event.target.value),
        },
        sampleMolecules.map((item) =>
          React.createElement('option', { key: item.id, value: item.id }, item.label),
        ),
      ),
    ],
  );

  const metadata = React.createElement(
    'div',
    { className: 'molecule-meta' },
    [
      React.createElement(
        'span',
        { key: 'formula' },
        `Formula: ${selectedEntry.formula}`,
      ),
      React.createElement(
        'span',
        { key: 'smiles' },
        `SMILES: ${selectedEntry.molecule.smiles}`,
      ),
      React.createElement(
        'span',
        { key: 'atoms' },
        `${selectedEntry.molecule.atoms.length} atoms`,
      ),
    ],
  );

  const viewerSection = React.createElement(
    'section',
    { className: 'viewer-section' },
    [
      React.createElement(
        'div',
        { key: 'details', className: 'viewer-details' },
        [
          React.createElement('h2', { key: 'name' }, selectedEntry.label),
          React.createElement('p', { key: 'description' }, selectedEntry.description),
          metadata,
          selector,
        ],
      ),
      React.createElement(MoleculeViewer, {
        key: 'viewer',
        molecule: selectedEntry.molecule,
        title: selectedEntry.label,
      }),
    ],
  );

  return React.createElement('div', { className: 'app-shell' }, [header, viewerSection]);
}

const rootElement = document.getElementById('root');

if (rootElement) {
  const root = createRoot(rootElement);
  root.render(React.createElement(App));
} else {
  console.error('Failed to find root element to mount the Molecule Visualizer app.');
}
