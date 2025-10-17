const CDN_URL = '/3Dmol-min.js';
const SCRIPT_ID = 'three-dmol-script';

let loaderPromise = null;

export function load3DMol() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('3Dmol.js loader must run in a browser environment.'));
  }

  if (window["3Dmol"]) {
    return Promise.resolve(window["3Dmol"]);
  }

  // Also check for the $3Dmol global (some versions use this)
  if (window.$3Dmol) {
    return Promise.resolve(window.$3Dmol);
  }

  if (!loaderPromise) {
    loaderPromise = new Promise((resolve, reject) => {
      const existingScript = document.getElementById(SCRIPT_ID);

      const handleLoad = () => {
        if (window["3Dmol"]) {
          resolve(window["3Dmol"]);
        } else if (window.$3Dmol) {
          resolve(window.$3Dmol);
        } else {
          loaderPromise = null;
          reject(new Error('3Dmol.js loaded but did not expose the global 3Dmol object.'));
        }
      };

      const handleError = () => {
        loaderPromise = null;
        reject(new Error(`Failed to load 3Dmol.js from ${CDN_URL}`));
      };

      if (existingScript) {
      if (existingScript.dataset.loaded === 'true' && (window["3Dmol"] || window.$3Dmol)) {
        resolve(window["3Dmol"] || window.$3Dmol);
        return;
      }

        existingScript.addEventListener('load', handleLoad, { once: true });
        existingScript.addEventListener('error', handleError, { once: true });
        return;
      }

      const script = document.createElement('script');
      script.id = SCRIPT_ID;
      script.type = 'text/javascript';
      script.async = true;
      script.src = CDN_URL;
      script.crossOrigin = 'anonymous';

      script.onload = () => {
        script.dataset.loaded = 'true';
        handleLoad();
      };

      script.onerror = handleError;

      document.head.appendChild(script);
    });
  }

  return loaderPromise;
}
