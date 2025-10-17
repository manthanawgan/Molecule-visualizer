import pytest
from fastapi.testclient import TestClient

from backend.app import MOLECULE_STORE, app
from backend.molecules import MINIMIZED_BOND_LENGTH

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_store() -> None:
    """Ensure the in-memory store is pristine for each test."""

    MOLECULE_STORE.clear()


def _extract_coordinates(payload: dict) -> list[tuple[float, float, float]]:
    return [(atom["x"], atom["y"], atom["z"]) for atom in payload["atoms"]]


def test_upload_and_retrieve_molecule() -> None:
    xyz_content = (
        "3\n"
        "water molecule\n"
        "O 0.000 0.000 0.000\n"
        "H 0.758 0.000 0.504\n"
        "H -0.758 0.000 0.504\n"
    ).encode()

    response = client.post(
        "/upload",
        files={"file": ("water.xyz", xyz_content, "text/plain")},
    )
    assert response.status_code == 200
    payload = response.json()
    molecule_id = payload["id"]

    assert molecule_id in MOLECULE_STORE

    stored = MOLECULE_STORE[molecule_id]
    assert len(stored.atoms) == 3
    assert stored.atoms[0].element == "O"

    retrieved = client.get(f"/molecule/{molecule_id}")
    assert retrieved.status_code == 200
    retrieved_payload = retrieved.json()
    assert retrieved_payload["id"] == molecule_id
    assert retrieved_payload["atoms"][0]["element"] == "O"
    assert retrieved_payload["bond_distances"] == {}


def test_upload_rejects_unsupported_extension() -> None:
    response = client.post(
        "/upload",
        files={"file": ("notes.txt", b"not a molecule", "text/plain")},
    )
    assert response.status_code == 400


def test_get_molecule_missing_returns_404() -> None:
    response = client.get("/molecule/does-not-exist")
    assert response.status_code == 404


def test_molecule_by_smiles_generates_without_storing() -> None:
    response = client.get(
        "/molecule/by-smiles",
        params={"smiles": "CCO", "minimize": True},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["smiles"] == "CCO"
    assert payload["minimized"] is True
    assert payload["bond_distances"]["0-1"] == pytest.approx(MINIMIZED_BOND_LENGTH)
    assert payload["id"] not in MOLECULE_STORE


def test_minimisation_updates_coordinates_and_store() -> None:
    initial = client.post("/smiles", json={"smiles": "CCO"})
    assert initial.status_code == 200
    molecule = initial.json()
    molecule_id = molecule["id"]
    original_coords = _extract_coordinates(molecule)

    minimised = client.post(
        "/smiles",
        json={"smiles": "CCO", "minimize": True, "molecule_id": molecule_id},
    )
    assert minimised.status_code == 200
    minimised_payload = minimised.json()

    assert minimised_payload["id"] == molecule_id
    assert minimised_payload["minimized"] is True

    minimised_coords = _extract_coordinates(minimised_payload)
    assert minimised_coords != original_coords

    stored = MOLECULE_STORE[molecule_id]
    assert stored.minimized is True
    assert stored.atoms[0].x == pytest.approx(minimised_coords[0][0])


def test_distance_endpoint_matches_bond_distance_summary() -> None:
    created = client.post("/smiles", json={"smiles": "CCC", "minimize": True})
    assert created.status_code == 200
    payload = created.json()

    molecule_id = payload["id"]
    bond_distance = payload["bond_distances"]["0-1"]
    assert bond_distance == pytest.approx(MINIMIZED_BOND_LENGTH)

    response = client.get(
        "/distance",
        params={"molecule_id": molecule_id, "atom1": 0, "atom2": 1},
    )
    assert response.status_code == 200
    distance_payload = response.json()

    assert distance_payload["distance"] == pytest.approx(bond_distance)
    assert distance_payload["units"] == "angstrom"


def test_distance_endpoint_handles_missing_molecules() -> None:
    response = client.get(
        "/distance",
        params={"molecule_id": "missing", "atom1": 0, "atom2": 1},
    )
    assert response.status_code == 404


def test_distance_endpoint_validates_atom_indices() -> None:
    created = client.post("/smiles", json={"smiles": "CC"})
    assert created.status_code == 200
    molecule_id = created.json()["id"]

    response = client.get(
        "/distance",
        params={"molecule_id": molecule_id, "atom1": 0, "atom2": 99},
    )
    assert response.status_code == 400


def test_molecule_update_rejects_mismatched_smiles() -> None:
    created = client.post("/smiles", json={"smiles": "CC"})
    assert created.status_code == 200
    molecule_id = created.json()["id"]

    response = client.post(
        "/smiles",
        json={"smiles": "O", "minimize": True, "molecule_id": molecule_id},
    )
    assert response.status_code == 400


def test_invalid_smiles_returns_error() -> None:
    response = client.post("/smiles", json={"smiles": "12345"})
    assert response.status_code == 400
