export interface AtomData {
  index: number;
  element: string;
  x: number;
  y: number;
  z: number;
}

export interface BondData {
  atom1: number;
  atom2: number;
  order: number;
}

export interface MoleculeData {
  id: string;
  smiles: string;
  atoms: AtomData[];
  bonds: BondData[];
  minimized: boolean;
}

export type BondDistances = Record<string, number>;

export interface MoleculeResponse extends MoleculeData {
  bond_distances: BondDistances;
}

export interface MoleculeRequest {
  smiles: string;
  minimize?: boolean;
  molecule_id?: string;
}

export interface UploadResponse {
  id: string;
}

export interface DistanceResponse {
  molecule_id: string;
  atom1: number;
  atom2: number;
  distance: number;
  units: string;
}
