# =============================================================================
# tests/test_um.py — Tests de l'endpoint GET /um
# =============================================================================

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Tests — structure de base (sans var)
# ---------------------------------------------------------------------------

def test_um_retourne_200(client: TestClient):
    """Un appel valide avec annee retourne le code HTTP 200."""
    response = client.get("/um", params={"annee": "23"})
    assert response.status_code == 200


def test_um_retourne_liste_non_vide(client: TestClient):
    """La réponse est une liste non vide."""
    response = client.get("/um", params={"annee": "23"})
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_um_colonnes_de_base(client: TestClient):
    """Chaque ligne contient code_rum, duree_moy_rum + colonnes statistiques."""
    response = client.get("/um", params={"annee": "23"})
    data = response.json()
    colonnes_attendues = {
        "code_rum", "nb_sej", "duree_moy_sej", "duree_moy_rum",
        "tx_dc", "tx_male", "age_moy",
    }
    for row in data:
        assert colonnes_attendues.issubset(row.keys()), (
            f"Colonnes manquantes : {colonnes_attendues - row.keys()}"
        )


def test_um_duree_moy_rum_presente(client: TestClient):
    """La colonne duree_moy_rum est toujours présente (spécifique à /um)."""
    response = client.get("/um", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert "duree_moy_rum" in row
        assert row["duree_moy_rum"] is not None


def test_um_duree_moy_rum_inferieure_sej(client: TestClient):
    """duree_moy_rum <= duree_moy_sej (le RUM est un sous-séjour)."""
    response = client.get("/um", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["duree_moy_rum"] <= row["duree_moy_sej"], (
            f"duree_moy_rum ({row['duree_moy_rum']}) > duree_moy_sej ({row['duree_moy_sej']})"
        )


def test_um_codes_rum_valides(client: TestClient):
    """Les codes UM (code_rum) sont dans la nomenclature TYPE_UM."""
    response = client.get("/um", params={"annee": "23"})
    data = response.json()
    codes_type_um = {"01", "02", "03", "04", "13", "18"}
    for row in data:
        assert row["code_rum"] in codes_type_um, (
            f"Code UM invalide : {row['code_rum']}"
        )


def test_um_six_lignes_sans_var(client: TestClient):
    """Sans var, 6 lignes (une par type d'UM dans la nomenclature)."""
    response = client.get("/um", params={"annee": "23"})
    data = response.json()
    assert len(data) == 6, f"Attendu 6 lignes, obtenu {len(data)}"


# ---------------------------------------------------------------------------
# Tests — avec le paramètre var
# ---------------------------------------------------------------------------

def test_um_avec_var_finess(client: TestClient):
    """Avec var=finess, les lignes ont code_rum et finess."""
    response = client.get("/um", params={
        "annee": "23",
        "var": "finess",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert "code_rum" in row
        assert "finess" in row
        # duree_moy_rum toujours présente même avec var
        assert "duree_moy_rum" in row


def test_um_avec_var_plus_de_lignes(client: TestClient):
    """Avec var=finess, plus de lignes qu'en cas de base."""
    response_base = client.get("/um", params={"annee": "23"})
    response_var = client.get("/um", params={"annee": "23", "var": "finess"})
    assert len(response_var.json()) > len(response_base.json())


# ---------------------------------------------------------------------------
# Tests — paramètre `annee` obligatoire
# ---------------------------------------------------------------------------

def test_um_sans_annee_retourne_422(client: TestClient):
    """Sans le paramètre `annee` obligatoire, l'API retourne 422."""
    response = client.get("/um")
    assert response.status_code == 422
