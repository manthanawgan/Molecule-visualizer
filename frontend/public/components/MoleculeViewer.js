import * as React from 'https://esm.sh/react@18?dev';
import { load3DMol } from '../utils/load3dmol.js';

const { useState, useEffect, useRef, useCallback } = React;
const ZOOM_STEP = 1.2;

function build3DMolAtoms(molecule) {
  if (!molecule) {
    return [];
  }

  const adjacency = new Map();
  for (const atom of molecule.atoms) {
    adjacency.set(atom.index, { indices: [], orders: [] });
  }

  for (const bond of molecule.bonds || []) {
    const { atom1, atom2 } = bond;
    if (!adjacency.has(atom1) || !adjacency.has(atom2)) {
      continue;
    }

    const order = Math.max(1, bond.order || 1);
    const first = adjacency.get(atom1);
    const second = adjacency.get(atom2);

    first.indices.push(atom2);
    first.orders.push(order);
    second.indices.push(atom1);
    second.orders.push(order);
  }

  return molecule.atoms.map((atom) => {
    const meta = adjacency.get(atom.index) || { indices: [], orders: [] };
    return {
      elem: atom.element,
      x: atom.x,
      y: atom.y,
      z: atom.z,
      serial: atom.index + 1,
      index: atom.index,
      bonds: [...meta.indices],
      bondOrder: [...meta.orders]
    };
  });
}

export function MoleculeViewer({ molecule, title }) {
  const containerRef = useRef(null);
  const viewerRef = useRef(null);
  const defaultViewRef = useRef(null);
  const toastTimerRef = useRef(null);

  const [status, setStatus] = useState({ loading: true, error: null });
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message) => {
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
    }

    setToast(message);
    toastTimerRef.current = setTimeout(() => {
      setToast(null);
      toastTimerRef.current = null;
    }, 2400);
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    let cancelled = false;

    load3DMol()
      .then(($3Dmol) => {
        if (cancelled) {
          return;
        }

        if (!containerRef.current) {
          throw new Error('3Dmol target container is missing.');
        }

        const viewer = new $3Dmol.GlViewer(containerRef.current, {
          backgroundColor: '#0f172a',
          antialias: true,
        });

        viewerRef.current = viewer;
        viewer.render();
        setStatus({ loading: false, error: null });
      })
      .catch((error) => {
        if (!cancelled) {
          console.error('Failed to initialise 3Dmol.js viewer', error);
          setStatus({ loading: false, error });
        }
      });

    return () => {
      cancelled = true;

      if (toastTimerRef.current) {
        clearTimeout(toastTimerRef.current);
        toastTimerRef.current = null;
      }

      if (viewerRef.current) {
        try {
          viewerRef.current.clear();
        } catch (_) {
          // noop — clear can fail if the viewer never initialised fully.
        }
        viewerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    const handleResize = () => {
      if (viewerRef.current) {
        viewerRef.current.resize();
        viewerRef.current.render();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !molecule) {
      return;
    }

    const atoms = build3DMolAtoms(molecule);
    viewer.removeAllModels();
    viewer.addAtoms(atoms);
    viewer.setStyle({}, {
      stick: {
        radius: 0.18,
        colorscheme: 'Jmol',
        opacity: 0.92,
      },
      sphere: {
        scale: 0.28,
        colorscheme: 'Jmol',
        opacity: 1.0,
      },
    });
    viewer.zoomTo();
    viewer.render();
    defaultViewRef.current = viewer.getView();

    if (molecule) {
      showToast(`Loaded ${title || molecule.smiles}`);
    }
  }, [molecule, title, showToast]);

  const resetView = useCallback(() => {
    const viewer = viewerRef.current;
    if (!viewer || !defaultViewRef.current) {
      return;
    }

    viewer.setView(defaultViewRef.current);
    viewer.render();
    showToast('View reset');
  }, [showToast]);

  const zoomIn = useCallback(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }

    viewer.zoom(1 / ZOOM_STEP, 250);
    viewer.render();
    showToast('Zoomed in');
  }, [showToast]);

  const zoomOut = useCallback(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      return;
    }

    viewer.zoom(ZOOM_STEP, 250);
    viewer.render();
    showToast('Zoomed out');
  }, [showToast]);

  const children = [
    React.createElement('div', {
      key: 'canvas',
      ref: containerRef,
      className: 'viewer-canvas',
      role: 'presentation',
      'aria-label': title ? `3D structure viewer for ${title}` : '3D structure viewer',
    }),
  ];

  if (status.loading) {
    children.push(
      React.createElement(
        'div',
        {
          key: 'loading',
          className: 'viewer-overlay',
        },
        'Loading 3D viewer…',
      ),
    );
  }

  if (status.error) {
    children.push(
      React.createElement(
        'div',
        {
          key: 'error',
          className: 'viewer-overlay viewer-overlay--error',
        },
        status.error.message,
      ),
    );
  }

  children.push(
    React.createElement(
      'div',
      {
        key: 'controls',
        className: 'viewer-controls',
        'aria-label': 'Viewer controls',
      },
      [
        React.createElement(
          'button',
          {
            key: 'zoom-in',
            type: 'button',
            onClick: zoomIn,
            disabled: status.loading || Boolean(status.error),
          },
          'Zoom In',
        ),
        React.createElement(
          'button',
          {
            key: 'zoom-out',
            type: 'button',
            onClick: zoomOut,
            disabled: status.loading || Boolean(status.error),
          },
          'Zoom Out',
        ),
        React.createElement(
          'button',
          {
            key: 'reset',
            type: 'button',
            onClick: resetView,
            disabled: status.loading || Boolean(status.error),
          },
          'Reset View',
        ),
      ],
    ),
  );

  if (toast) {
    children.push(
      React.createElement(
        'div',
        {
          key: 'toast',
          className: 'viewer-toast',
        },
        toast,
      ),
    );
  }

  return React.createElement(
    'div',
    {
      className: 'viewer-container',
    },
    children,
  );
}
