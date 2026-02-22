# =============================================================================
# tests/test_diag_assoc.py — Tests de l'endpoint GET /diag_assoc
# =============================================================================

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Tests — structure de base (sans var)
# ---------------------------------------------------------------------------

def test_diag_assoc_retourne_200(client: TestClient):
    """Un appel valide avec annee retourne le code HTTP 200."""
    response = client.get("/diag_assoc", params={"annee": "23"})
    assert response.status_code == 200


def test_diag_assoc_retourne_liste_non_vide(client: TestClient):
    """La réponse est une liste non vide."""
    response = client.get("/diag_assoc", params={"annee": "23"})
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_diag_assoc_colonnes_de_base(client: TestClient):
    """Chaque ligne contient code_diag + les colonnes statistiques."""
    response = client.get("/diag_assoc", params={"annee": "23"})
    data = response.json()
    colonnes_attendues = {"code_diag", "nb_sej", "tx_dc", "tx_male", "age_moy"}
    for row in data:
        assert colonnes_attendues.issubset(row.keys()), (
            f"Colonnes manquantes : {colonnes_attendues - row.keys()}"
        )


def test_diag_assoc_pas_de_nb_pat_sans_var(client: TestClient):
    """Sans var, la réponse ne contient pas nb_pat (différence avec /resume)."""
    response = client.get("/diag_assoc", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert "nb_pat" not in row, "nb_pat ne devrait pas être présent sans var"


def test_diag_assoc_code_diag_est_cim10(client: TestClient):
    """code_diag contient des codes CIM-10 de la nomenclature."""
    response = client.get("/diag_assoc", params={"annee": "23"})
    data = response.json()
    # Codes CIM-10 attendus dans la nomenclature
    codes_cim10_connus = {"C34", "I50", "J44", "K80", "S72", "I10", "E11", "N18"}
    codes_reponse = {row["code_diag"] for row in data}
    # La réponse doit contenir au moins quelques codes connus
    assert codes_reponse.intersection(codes_cim10_connus), (
        f"Aucun code CIM-10 connu dans la réponse : {codes_reponse}"
    )


def test_diag_assoc_une_ligne_par_code(client: TestClient):
    """Sans var, il y a une ligne par code CIM-10 de la nomenclature (12 codes)."""
    response = client.get("/diag_assoc", params={"annee": "23"})
    data = response.json()
    assert len(data) == 12, f"Attendu 12 codes CIM-10, obtenu {len(data)}"


# ---------------------------------------------------------------------------
# Tests — avec le paramètre var
# ---------------------------------------------------------------------------

def test_diag_assoc_avec_var_ghm(client: TestClient):
    """Avec var=ghm, les lignes ont code_diag et ghm."""
    response = client.get("/diag_assoc", params={
        "annee": "23",
        "var": "ghm",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert "code_diag" in row
        assert "ghm" in row


def test_diag_assoc_avec_var_plus_de_lignes(client: TestClient):
    """Avec var=ghm, plus de lignes qu'en cas de base."""
    response_base = client.get("/diag_assoc", params={"annee": "23"})
    response_var = client.get("/diag_assoc", params={"annee": "23", "var": "ghm"})
    assert len(response_var.json()) > len(response_base.json())


def test_diag_assoc_avec_var_dr(client: TestClient):
    """Avec var=dr, les lignes ont une colonne dr."""
    response = client.get("/diag_assoc", params={
        "annee": "23",
        "var": "dr",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert "dr" in row


# ---------------------------------------------------------------------------
# Tests — paramètre `annee` obligatoire
# ---------------------------------------------------------------------------

def test_diag_assoc_sans_annee_retourne_400(client: TestClient) -> None:
    """Sans le paramètre `annee` obligatoire, l'API retourne 400 (étape 6 : handler 422→400)."""
    response = client.get("/diag_assoc")
    assert response.status_code == 400


# =============================================================================
# Tests étape 6 — Gestion des erreurs et secret statistique
# =============================================================================


def test_diag_assoc_404_perimetre_vide(client: TestClient) -> None:
    """simulate_vide=TRUE doit retourner HTTP 404 (spec §5.1)."""
    response = client.get(
        "/diag_assoc",
        params={"annee": "23", "simulate_vide": "TRUE"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_diag_assoc_petit_effectif_methode_b(client: TestClient) -> None:
    """
    simulate_petit_effectif=TRUE retourne la Méthode B (spec §5.2).

    Une seule ligne avec uniquement des colonnes string (pas de colonnes numériques).
    """
    response = client.get(
        "/diag_assoc",
        params={"annee": "23", "simulate_petit_effectif": "TRUE"},
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1

    row = data[0]
    # La ligne identifiant doit être "code_diag"
    assert "code_diag" in row
    for value in row.values():
        assert isinstance(value, str), f"Valeur non-string trouvée : {value!r}"
