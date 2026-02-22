# =============================================================================
# tests/test_resume_prec_annee.py — Tests de l'endpoint GET /resume_prec_annee
# =============================================================================

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Tests — structure de base (sans var)
# ---------------------------------------------------------------------------

def test_resume_prec_annee_retourne_200(client: TestClient):
    """Un appel valide avec annee retourne le code HTTP 200."""
    response = client.get("/resume_prec_annee", params={"annee": "23"})
    assert response.status_code == 200


def test_resume_prec_annee_cinq_lignes_sans_var(client: TestClient):
    """Sans var, la réponse contient exactement 5 lignes (5 années)."""
    response = client.get("/resume_prec_annee", params={"annee": "23"})
    data = response.json()
    assert len(data) == 5, f"Attendu 5 lignes, obtenu {len(data)}"


def test_resume_prec_annee_annee_4_chiffres(client: TestClient):
    """La colonne `annee` est en format 4 chiffres."""
    response = client.get("/resume_prec_annee", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["annee"] >= 2000, f"Année invalide : {row['annee']}"


def test_resume_prec_annee_serie_temporelle_correcte(client: TestClient):
    """Les 5 années couvrent bien annee-4 à annee (ex: 2019 à 2023)."""
    response = client.get("/resume_prec_annee", params={"annee": "23"})
    data = response.json()
    annees = sorted(row["annee"] for row in data)
    assert annees == [2019, 2020, 2021, 2022, 2023], (
        f"Série temporelle incorrecte : {annees}"
    )


def test_resume_prec_annee_colonnes_de_base(client: TestClient):
    """Chaque ligne contient les colonnes statistiques de base + annee + nb_pat."""
    response = client.get("/resume_prec_annee", params={"annee": "23"})
    data = response.json()
    colonnes_attendues = {"annee", "nb_sej", "nb_pat", "tx_dc", "tx_male", "age_moy"}
    for row in data:
        assert colonnes_attendues.issubset(row.keys()), (
            f"Colonnes manquantes : {colonnes_attendues - row.keys()}"
        )


def test_resume_prec_annee_nb_pat_toujours_present(client: TestClient):
    """nb_pat est toujours présent (pas besoin de bool_nb_pat)."""
    response = client.get("/resume_prec_annee", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert "nb_pat" in row
        assert isinstance(row["nb_pat"], int)


# ---------------------------------------------------------------------------
# Tests — avec le paramètre var
# ---------------------------------------------------------------------------

def test_resume_prec_annee_avec_var_ghm(client: TestClient):
    """Avec var=ghm, les lignes ont à la fois 'annee' et 'ghm'."""
    response = client.get("/resume_prec_annee", params={
        "annee": "23",
        "var": "ghm",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert "annee" in row
        assert "ghm" in row


def test_resume_prec_annee_avec_var_plus_de_lignes(client: TestClient):
    """Avec var=ghm, on a plus de 5 lignes (5 années × N codes GHM)."""
    response = client.get("/resume_prec_annee", params={
        "annee": "23",
        "var": "ghm",
    })
    data = response.json()
    # 5 années × 8 codes GHM = 40 lignes
    assert len(data) > 5, f"Attendu > 5 lignes, obtenu {len(data)}"


def test_resume_prec_annee_annee_valide_dans_var(client: TestClient):
    """Avec var=mois, les annees dans la réponse sont toutes valides."""
    response = client.get("/resume_prec_annee", params={
        "annee": "23",
        "var": "mois",
    })
    data = response.json()
    for row in data:
        assert 2019 <= row["annee"] <= 2023, f"Année hors plage : {row['annee']}"


# ---------------------------------------------------------------------------
# Tests — paramètre `annee` obligatoire
# ---------------------------------------------------------------------------

def test_resume_prec_annee_sans_annee_retourne_400(client: TestClient) -> None:
    """Sans le paramètre `annee` obligatoire, l'API retourne 400 (étape 6 : handler 422→400)."""
    response = client.get("/resume_prec_annee")
    assert response.status_code == 400


# =============================================================================
# Tests étape 6 — Gestion des erreurs et secret statistique
# =============================================================================


def test_resume_prec_annee_404_perimetre_vide(client: TestClient) -> None:
    """simulate_vide=TRUE doit retourner HTTP 404 (spec §5.1)."""
    response = client.get(
        "/resume_prec_annee",
        params={"annee": "23", "simulate_vide": "TRUE"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_resume_prec_annee_petit_effectif_methode_b(client: TestClient) -> None:
    """
    simulate_petit_effectif=TRUE retourne la Méthode B (spec §5.2).

    Une seule ligne avec uniquement des colonnes string (pas de colonnes numériques).
    Le client R détecte ce cas via : all(sapply(data, function(col) !any(is.numeric(col))))
    """
    response = client.get(
        "/resume_prec_annee",
        params={"annee": "23", "simulate_petit_effectif": "TRUE"},
    )
    assert response.status_code == 200

    data = response.json()
    # Une seule ligne
    assert len(data) == 1

    # La ligne ne doit contenir que des colonnes string (aucune numérique)
    row = data[0]
    for value in row.values():
        assert isinstance(value, str), f"Valeur non-string trouvée : {value!r}"
