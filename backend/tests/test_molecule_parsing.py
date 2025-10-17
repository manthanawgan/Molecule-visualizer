from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import app, parser_service
from backend.services.molecule_parser import MoleculeParsingError

client = TestClient(app)


def read_sample(name: str) -> bytes:
    sample_path = Path(__file__).parent / "data" / name
    return sample_path.read_bytes()


def test_parse_xyz_generates_bonds() -> None:
    payload = read_sample("water.xyz")
    response = client.post(
        "/molecules/parse",
        files={"file": ("water.xyz", io.BytesIO(payload), "chemical/x-xyz")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["formula"] == "H2O"
    assert data["atom_count"] == 3
    assert len(data["bonds"]) == 2
    # O-H bond lengths ~0.96 Å which should stay within inferred threshold.
    bond_atoms = {tuple(sorted((bond["atom1"], bond["atom2"]))) for bond in data["bonds"]}
    assert bond_atoms == {(0, 1), (0, 2)}


def test_parse_molfile_uses_bond_information() -> None:
    payload = read_sample("water.mol")
    response = client.post(
        "/molecules/parse",
        files={"file": ("water.mol", io.BytesIO(payload), "chemical/x-mdl-molfile")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "water"
    assert data["formula"] == "H2O"
    assert data["atom_count"] == 3
    assert len(data["bonds"]) == 2
    assert {tuple(sorted((bond["atom1"], bond["atom2"]))) for bond in data["bonds"]} == {(0, 1), (0, 2)}


def test_parse_pdb_respects_connect_records() -> None:
    payload = read_sample("methane.pdb")
    response = client.post(
        "/molecules/parse",
        files={"file": ("methane.pdb", io.BytesIO(payload), "chemical/x-pdb")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["formula"] == "CH4"
    assert data["atom_count"] == 5
    assert len(data["bonds"]) == 4
    central_bonds = {tuple(sorted((bond["atom1"], bond["atom2"]))) for bond in data["bonds"]}
    assert central_bonds == {(0, 1), (0, 2), (0, 3), (0, 4)}


def test_rdkit_failure_uses_openbabel_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    original_openbabel = parser_service.openbabel_parser.parse

    def fail_rdkit(*args, **kwargs):
        raise MoleculeParsingError("RDKit failure for testing")

    calls: dict[str, int] = {"openbabel": 0}

    def fallback_parse(file_bytes: bytes, file_format: str, *, filename: str | None = None):
        calls["openbabel"] += 1
        return original_openbabel(file_bytes, file_format, filename=filename)

    monkeypatch.setattr(parser_service.rdkit_parser, "parse", fail_rdkit)
    monkeypatch.setattr(parser_service.openbabel_parser, "parse", fallback_parse)

    payload = read_sample("water.xyz")
    response = client.post(
        "/molecules/parse",
        files={"file": ("water.xyz", io.BytesIO(payload), "chemical/x-xyz")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["formula"] == "H2O"
    assert calls["openbabel"] == 1


def test_rejects_unsupported_extension() -> None:
    response = client.post(
        "/molecules/parse",
        files={"file": ("molecule.txt", io.BytesIO(b"fake"), "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_invalid_xyz_file_returns_400() -> None:
    broken_xyz = b"2\nOops\nH 0 0 0\n"
    response = client.post(
        "/molecules/parse",
        files={"file": ("broken.xyz", io.BytesIO(broken_xyz), "chemical/x-xyz")},
    )
    assert response.status_code == 400
    assert "XYZ atom count" in response.json()["detail"]
