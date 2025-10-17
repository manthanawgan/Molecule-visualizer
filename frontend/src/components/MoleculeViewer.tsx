import React, { useCallback, useEffect, useRef, useState } from 'react';
import type { MoleculeResponse } from '../lib/types';

// Load 3Dmol.js dynamically
const load3DMol = (): Promise<any> => {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('3Dmol.js loader must run in a browser environment.'));
  }

  if (window.$3Dmol) {
    return Promise.resolve(window.$3Dmol);
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.async = true;
    script.src = 'https://www.3dmol.org/build/3Dmol-min.js';
    script.crossOrigin = 'anonymous';

    script.onload = () => {
      if (window.$3Dmol) {
        resolve(window.$3Dmol);
      } else {
        reject(new Error('3Dmol.js loaded but did not expose the global $3Dmol object.'));
      }
    };

    script.onerror = () => {
      reject(new Error('Failed to load 3Dmol.js from CDN'));
    };

    document.head.appendChild(script);
  });
};

// Extend window type for 3Dmol
declare global {
  interface Window {
    $3Dmol: any;
  }
}

const ZOOM_STEP = 1.2;

function build3DMolAtoms(molecule: MoleculeResponse) {
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

interface MoleculeViewerProps {
  molecule: MoleculeResponse | null;
  title?: string;
}

export function MoleculeViewer({ molecule, title }: MoleculeViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const defaultViewRef = useRef<any>(null);
  const toastTimerRef = useRef<NodeJS.Timeout | null>(null);

  const [status, setStatus] = useState({ loading: true, error: null as string | null });
  const [toast, setToast] = useState<string | null>(null);

  const showToast = useCallback((message: string) => {
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
          setStatus({ loading: false, error: error.message });
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

  return (
    <div className="viewer-container">
      <div
        ref={containerRef}
        className="viewer-canvas"
        role="presentation"
        aria-label={title ? `3D structure viewer for ${title}` : '3D structure viewer'}
      />

      {status.loading && (
        <div className="viewer-overlay">
          Loading 3D viewer…
        </div>
      )}

      {status.error && (
        <div className="viewer-overlay viewer-overlay--error">
          {status.error}
        </div>
      )}

      <div className="viewer-controls" aria-label="Viewer controls">
        <button
          type="button"
          onClick={zoomIn}
          disabled={status.loading || Boolean(status.error)}
        >
          Zoom In
        </button>
        <button
          type="button"
          onClick={zoomOut}
          disabled={status.loading || Boolean(status.error)}
        >
          Zoom Out
        </button>
        <button
          type="button"
          onClick={resetView}
          disabled={status.loading || Boolean(status.error)}
        >
          Reset View
        </button>
      </div>

      {toast && (
        <div className="viewer-toast">
          {toast}
        </div>
      )}
    </div>
  );
}
