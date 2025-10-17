import { ChangeEvent, FormEvent, useMemo, useRef, useState } from "react";
import { useTheme } from "./hooks/useTheme";
import { apiBaseUrl, moleculeApi } from "./lib/api";
import type { MoleculeResponse } from "./lib/types";

type AsyncStatus = "idle" | "loading" | "uploading";

const supportedFileTypes = [".mol", ".sdf", ".pdb", ".xyz"];

function App() {
  const { isDark, toggleTheme } = useTheme();
  const [smiles, setSmiles] = useState("");
  const [molecule, setMolecule] = useState<MoleculeResponse | null>(null);
  const [status, setStatus] = useState<AsyncStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleSmilesChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSmiles(event.target.value);
    if (error) {
      setError(null);
    }
  };

  const handleReset = () => {
    setSmiles("");
    setMolecule(null);
    setError(null);
    setSelectedFileName("");
    setStatus("idle");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = smiles.trim();
    if (!value) {
      setError("Please enter a SMILES string to continue.");
      return;
    }

    setStatus("loading");
    setError(null);

    try {
      const data = await moleculeApi.fetchBySmiles(value, molecule?.minimized ?? false);
      setMolecule(data);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to fetch molecule data. Ensure the backend service is running."
      );
    } finally {
      setStatus("idle");
    }
  };

  const handleUploadChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setSelectedFileName(file.name);
    setStatus("uploading");
    setError(null);

    try {
      const { id } = await moleculeApi.uploadMolecule(file);
      const data = await moleculeApi.fetchById(id);
      setSmiles(data.smiles);
      setMolecule(data);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Uploading failed. Please verify the file and retry."
      );
    } finally {
      setStatus("idle");
    }
  };

  const moleculeStats = useMemo(() => {
    if (!molecule) {
      return null;
    }

    return [
      { label: "Identifier", value: molecule.id },
      { label: "SMILES", value: molecule.smiles },
      { label: "Atoms", value: molecule.atoms.length.toString() },
      { label: "Bonds", value: molecule.bonds.length.toString() },
      { label: "Minimized", value: molecule.minimized ? "Yes" : "No" },
    ];
  }, [molecule]);

  const bondDistances = useMemo(() => {
    if (!molecule) {
      return [] as Array<[string, number]>;
    }
    return Object.entries(molecule.bond_distances).sort(([a], [b]) => a.localeCompare(b));
  }, [molecule]);

  const isBusy = status !== "idle";

  return (
    <div className="flex min-h-screen flex-col bg-slate-100/90 text-slate-900 transition-colors duration-200 dark:bg-slate-950/95 dark:text-slate-100">
      <header className="border-b border-slate-200/80 bg-white/75 backdrop-blur-md dark:border-slate-800/70 dark:bg-slate-900/70">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-6 py-5">
          <form
            className="flex flex-col gap-4 md:flex-row md:items-center"
            onSubmit={handleSubmit}
          >
            <div className="flex items-center gap-3">
              <label className="btn-secondary cursor-pointer whitespace-nowrap">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={supportedFileTypes.join(",")}
                  className="hidden"
                  onChange={handleUploadChange}
                  disabled={isBusy}
                />
                <span>{status === "uploading" ? "Uploading…" : "Upload file"}</span>
              </label>
              {selectedFileName ? (
                <span className="truncate text-sm text-slate-500 dark:text-slate-400">
                  {selectedFileName}
                </span>
              ) : (
                <span className="text-sm text-slate-400 dark:text-slate-500">
                  Supported: {supportedFileTypes.join(", ")}
                </span>
              )}
            </div>

            <div className="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center">
              <input
                className="input"
                placeholder="Enter SMILES string, e.g. CCO"
                value={smiles}
                onChange={handleSmilesChange}
                disabled={isBusy}
                aria-label="SMILES input"
              />
              <button
                type="submit"
                className="btn-primary whitespace-nowrap"
                disabled={isBusy}
              >
                {status === "loading" ? "Generating…" : "Visualize"}
              </button>
            </div>

            <div className="flex items-center gap-2 self-start md:self-auto">
              <button
                type="button"
                className="btn-muted"
                onClick={handleReset}
                disabled={isBusy}
              >
                Reset
              </button>
              <button
                type="button"
                className="btn-ghost"
                onClick={toggleTheme}
                aria-label="Toggle color mode"
              >
                <span aria-hidden="true" className="text-lg">
                  {isDark ? "🌙" : "☀️"}
                </span>
                <span className="hidden text-sm md:inline">{isDark ? "Dark" : "Light"} mode</span>
              </button>
            </div>
          </form>

          {error && (
            <div className="rounded-lg border border-red-300 bg-red-50/80 px-4 py-3 text-sm text-red-700 shadow-sm dark:border-red-500/40 dark:bg-red-900/20 dark:text-red-200">
              {error}
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-8 lg:flex-row">
        <aside className="surface w-full max-w-md space-y-6 p-6">
          <div>
            <h2 className="text-lg font-semibold">Molecule overview</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Upload a supported file or generate a molecule from a SMILES string to
              populate the viewer.
            </p>
          </div>

          <dl className="space-y-3 text-sm">
            {moleculeStats ? (
              moleculeStats.map((entry) => (
                <div key={entry.label}>
                  <dt className="uppercase tracking-wide text-xs text-slate-400 dark:text-slate-500">
                    {entry.label}
                  </dt>
                  <dd className="mt-1 font-medium text-slate-900 dark:text-slate-100">
                    {entry.value}
                  </dd>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500 dark:text-slate-400">
                No molecule loaded yet.
              </p>
            )}
          </dl>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Bond distances
            </h3>
            {bondDistances.length > 0 ? (
              <ul className="mt-3 space-y-2 text-sm">
                {bondDistances.map(([bond, distance]) => (
                  <li
                    key={bond}
                    className="flex items-center justify-between rounded-md border border-slate-200/80 bg-white/60 px-3 py-2 text-slate-600 dark:border-slate-800/60 dark:bg-slate-900/40 dark:text-slate-300"
                  >
                    <span className="font-medium">{bond}</span>
                    <span className="tabular-nums">{distance.toFixed(3)} Å</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Bond metrics will appear once a molecule is loaded.
              </p>
            )}
          </div>

          <div className="rounded-md border border-slate-200/60 bg-slate-100/60 px-3 py-2 text-xs text-slate-500 dark:border-slate-800/60 dark:bg-slate-900/30 dark:text-slate-400">
            Base API URL: <span className="font-mono">{apiBaseUrl}</span>
          </div>
        </aside>

        <section className="flex flex-1 flex-col overflow-hidden">
          <div className="surface flex h-full min-h-[420px] flex-1 items-center justify-center border-2 border-dashed border-slate-300 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
            <div className="mx-auto max-w-md space-y-2">
              <h2 className="text-xl font-semibold">Canvas placeholder</h2>
              <p>
                The interactive 3D viewer will mount here. Hook this container into
                your preferred rendering library (e.g. Three.js) and feed it with the
                molecule data surface, atoms, and bond distances.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
