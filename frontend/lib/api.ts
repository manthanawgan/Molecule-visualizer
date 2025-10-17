import axios from "axios";
import type {
  DistanceResponse,
  MoleculeRequest,
  MoleculeResponse,
  UploadResponse,
} from "./types";

const DEFAULT_BASE_URL = "http://localhost:8000";

const normalizeBaseUrl = (value: string | undefined): string => {
  if (!value) {
    return DEFAULT_BASE_URL;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return DEFAULT_BASE_URL;
  }

  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
};

const baseURL = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL as string | undefined);

export const apiClient = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const apiBaseUrl = baseURL;

export const moleculeApi = {
  async submitSmiles(payload: MoleculeRequest) {
    const response = await apiClient.post<MoleculeResponse>("/smiles", payload);
    return response.data;
  },

  async fetchBySmiles(smiles: string, minimize = false) {
    const response = await apiClient.get<MoleculeResponse>("/molecule/by-smiles", {
      params: { smiles, minimize },
    });
    return response.data;
  },

  async fetchById(moleculeId: string) {
    const response = await apiClient.get<MoleculeResponse>(`/molecule/${moleculeId}`);
    return response.data;
  },

  async uploadMolecule(file: File) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post<UploadResponse>("/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  },

  async fetchDistance(moleculeId: string, atom1: number, atom2: number) {
    const response = await apiClient.get<DistanceResponse>("/distance", {
      params: { molecule_id: moleculeId, atom1, atom2 },
    });
    return response.data;
  },
};

export type MoleculeApi = typeof moleculeApi;
