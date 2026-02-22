# =============================================================================
# tests/test_dernier_trans.py — Tests de l'endpoint GET /dernier_trans
# =============================================================================

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Tests — structure et contenu de la réponse
# ---------------------------------------------------------------------------

def test_dernier_trans_retourne_200(client: TestClient):
    """Un appel valide avec annee retourne le code HTTP 200."""
    response = client.get("/dernier_trans", params={"annee": "23"})
    assert response.status_code == 200


def test_dernier_trans_retourne_liste(client: TestClient):
    """La réponse est une liste non vide."""
    response = client.get("/dernier_trans", params={"annee": "23"})
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_dernier_trans_colonnes_obligatoires(client: TestClient):
    """Chaque ligne contient les 6 colonnes attendues (spec §3.8)."""
    response = client.get("/dernier_trans", params={"annee": "23"})
    data = response.json()
    colonnes_attendues = {"annee", "finess", "rs", "secteur", "categ", "derniere_transmission"}
    for row in data:
        assert colonnes_attendues.issubset(row.keys()), (
            f"Colonnes manquantes : {colonnes_attendues - row.keys()}"
        )


def test_dernier_trans_annee_4_chiffres(client: TestClient):
    """La colonne `annee` est en format 4 chiffres (ex: 2023, pas 23)."""
    response = client.get("/dernier_trans", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["annee"] == 2023, f"Attendu 2023, obtenu {row['annee']}"


def test_dernier_trans_format_date(client: TestClient):
    """La date de transmission est au format YYYY-MM-DD."""
    response = client.get("/dernier_trans", params={"annee": "23"})
    data = response.json()
    for row in data:
        date = row["derniere_transmission"]
        # Le format attendu est YYYY-MM-DD (10 caractères)
        assert len(date) == 10, f"Format de date invalide : {date}"
        assert date[4] == "-" and date[7] == "-", f"Séparateurs manquants : {date}"


def test_dernier_trans_secteur_valides(client: TestClient):
    """Les secteurs sont soit 'PU' (public) soit 'PR' (privé)."""
    response = client.get("/dernier_trans", params={"annee": "23"})
    data = response.json()
    secteurs_valides = {"PU", "PR"}
    for row in data:
        assert row["secteur"] in secteurs_valides, (
            f"Secteur invalide : {row['secteur']}"
        )


def test_dernier_trans_une_ligne_par_finess(client: TestClient):
    """Il y a exactement autant de lignes que d'établissements FINESS (7)."""
    response = client.get("/dernier_trans", params={"annee": "23"})
    data = response.json()
    # 7 établissements dans la nomenclature FINESS
    assert len(data) == 7


def test_dernier_trans_finess_uniques(client: TestClient):
    """Chaque code FINESS n'apparaît qu'une seule fois dans la réponse."""
    response = client.get("/dernier_trans", params={"annee": "23"})
    data = response.json()
    finess_codes = [row["finess"] for row in data]
    assert len(finess_codes) == len(set(finess_codes)), "Des codes FINESS sont dupliqués"


# ---------------------------------------------------------------------------
# Tests — paramètre `annee` obligatoire
# ---------------------------------------------------------------------------

def test_dernier_trans_sans_annee_retourne_400(client: TestClient) -> None:
    """Sans le paramètre `annee` obligatoire, l'API retourne 400 (étape 6 : handler 422→400)."""
    response = client.get("/dernier_trans")
    assert response.status_code == 400


def test_dernier_trans_annee_differente(client: TestClient) -> None:
    """Avec une année différente, l'annee 4 chiffres est correctement calculée."""
    response = client.get("/dernier_trans", params={"annee": "19"})
    assert response.status_code == 200
    data = response.json()
    for row in data:
        assert row["annee"] == 2019, f"Attendu 2019, obtenu {row['annee']}"


# =============================================================================
# Tests étape 6 — Gestion des erreurs
# =============================================================================


def test_dernier_trans_404_perimetre_vide(client: TestClient) -> None:
    """
    simulate_vide=TRUE doit retourner HTTP 404 (spec §5.1).

    Note : /dernier_trans est EXEMPT du petit_effectif (données administratives,
    spec §3.8). Seul le 404 est testé ici.
    """
    response = client.get(
        "/dernier_trans",
        params={"annee": "23", "simulate_vide": "TRUE"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_dernier_trans_exempt_petit_effectif(client: TestClient) -> None:
    """
    /dernier_trans ignore simulate_petit_effectif (exempt du secret statistique).

    La spec §3.8 dit explicitement que cet endpoint est exclu du contrôle
    petit_effectif car il s'agit de données administratives (dates de transmission).
    Avec simulate_petit_effectif=TRUE, la réponse est normale (pas de Méthode B).
    """
    response = client.get(
        "/dernier_trans",
        params={"annee": "23", "simulate_petit_effectif": "TRUE"},
    )
    # Doit retourner 200 avec des données normales (ignorer le paramètre)
    assert response.status_code == 200
    data = response.json()
    # La réponse complète avec les 7 établissements (pas une réponse petit_effectif)
    assert len(data) == 7
    # Les colonnes numériques doivent être présentes (annee est un entier)
    for row in data:
        assert isinstance(row["annee"], int)
