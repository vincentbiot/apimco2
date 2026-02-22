# =============================================================================
# tests/test_actes.py — Tests de l'endpoint GET /actes
# =============================================================================

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Tests — structure de base (sans var)
# ---------------------------------------------------------------------------

def test_actes_retourne_200(client: TestClient):
    """Un appel valide avec annee retourne le code HTTP 200."""
    response = client.get("/actes", params={"annee": "23"})
    assert response.status_code == 200


def test_actes_retourne_liste_non_vide(client: TestClient):
    """La réponse est une liste non vide."""
    response = client.get("/actes", params={"annee": "23"})
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_actes_colonnes_de_base(client: TestClient):
    """Chaque ligne contient toutes les colonnes attendues (spec §3.6)."""
    response = client.get("/actes", params={"annee": "23"})
    data = response.json()
    colonnes_attendues = {
        "code_ccam", "extension_pmsi", "nb_acte", "nb_sej",
        "duree_moy_sej", "tx_male", "age_moy", "acte_activ", "is_classant",
    }
    for row in data:
        assert colonnes_attendues.issubset(row.keys()), (
            f"Colonnes manquantes : {colonnes_attendues - row.keys()}"
        )


def test_actes_pas_de_tx_dc(client: TestClient):
    """tx_dc n'est pas présent dans /actes (schéma spécifique, spec §3.6)."""
    response = client.get("/actes", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert "tx_dc" not in row, "tx_dc ne devrait pas être présent dans /actes"


def test_actes_pas_de_nb_pat(client: TestClient):
    """nb_pat n'est pas présent dans /actes."""
    response = client.get("/actes", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert "nb_pat" not in row, "nb_pat ne devrait pas être présent dans /actes"


def test_actes_codes_ccam_valides(client: TestClient):
    """Les codes CCAM de la réponse sont dans la nomenclature."""
    response = client.get("/actes", params={"annee": "23"})
    data = response.json()
    codes_ccam_connus = {"DZQM006", "YYYY600", "EQQP004", "HFMA009", "ZCQM002", "ABLB001", "BFGA004"}
    codes_reponse = {row["code_ccam"] for row in data}
    assert codes_reponse.issubset(codes_ccam_connus), (
        f"Codes CCAM inconnus : {codes_reponse - codes_ccam_connus}"
    )


def test_actes_sept_lignes_sans_var(client: TestClient):
    """Sans var, 7 lignes (une par code CCAM dans la nomenclature)."""
    response = client.get("/actes", params={"annee": "23"})
    data = response.json()
    assert len(data) == 7, f"Attendu 7 lignes, obtenu {len(data)}"


def test_actes_nb_acte_superieur_nb_sej(client: TestClient):
    """nb_acte >= nb_sej (un séjour peut avoir plusieurs actes du même code)."""
    response = client.get("/actes", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["nb_acte"] >= row["nb_sej"], (
            f"nb_acte ({row['nb_acte']}) < nb_sej ({row['nb_sej']})"
        )


def test_actes_extension_pmsi_valide(client: TestClient):
    """extension_pmsi vaut '0' ou '1'."""
    response = client.get("/actes", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["extension_pmsi"] in ("0", "1"), (
            f"extension_pmsi invalide : {row['extension_pmsi']}"
        )


def test_actes_is_classant_est_entier(client: TestClient):
    """is_classant est 0 ou 1 (entier, pas booléen)."""
    response = client.get("/actes", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["is_classant"] in (0, 1), (
            f"is_classant invalide : {row['is_classant']}"
        )


# ---------------------------------------------------------------------------
# Tests — avec le paramètre var
# ---------------------------------------------------------------------------

def test_actes_avec_var_finess(client: TestClient):
    """Avec var=finess, les lignes ont code_ccam et finess."""
    response = client.get("/actes", params={
        "annee": "23",
        "var": "finess",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert "code_ccam" in row
        assert "finess" in row


def test_actes_avec_var_plus_de_lignes(client: TestClient):
    """Avec var=finess, plus de lignes qu'en cas de base."""
    response_base = client.get("/actes", params={"annee": "23"})
    response_var = client.get("/actes", params={"annee": "23", "var": "finess"})
    assert len(response_var.json()) > len(response_base.json())


# ---------------------------------------------------------------------------
# Tests — paramètre `annee` obligatoire
# ---------------------------------------------------------------------------

def test_actes_sans_annee_retourne_422(client: TestClient):
    """Sans le paramètre `annee` obligatoire, l'API retourne 422."""
    response = client.get("/actes")
    assert response.status_code == 422
