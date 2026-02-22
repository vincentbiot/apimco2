# =============================================================================
# tests/test_tx_recours.py — Tests de l'endpoint GET /tx_recours
# =============================================================================

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Tests — structure de base
# ---------------------------------------------------------------------------

def test_tx_recours_retourne_200(client: TestClient):
    """Un appel valide avec annee retourne le code HTTP 200."""
    response = client.get("/tx_recours", params={"annee": "23"})
    assert response.status_code == 200


def test_tx_recours_retourne_liste(client: TestClient):
    """La réponse est une liste non vide."""
    response = client.get("/tx_recours", params={"annee": "23"})
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_tx_recours_colonnes_obligatoires(client: TestClient):
    """Chaque ligne contient les 9 colonnes attendues (spec §3.7)."""
    response = client.get("/tx_recours", params={"annee": "23"})
    data = response.json()
    colonnes_attendues = {
        "typ_geo", "code", "nb_sej", "nb_pat", "nb_pop",
        "tx_recours_brut_sej", "tx_recours_brut_pat",
        "tx_recours_standard_sej", "tx_recours_standard_pat",
    }
    for row in data:
        assert colonnes_attendues.issubset(row.keys()), (
            f"Colonnes manquantes : {colonnes_attendues - row.keys()}"
        )


# ---------------------------------------------------------------------------
# Tests — paramètre type_geo_tx_recours
# ---------------------------------------------------------------------------

def test_tx_recours_defaut_est_dep(client: TestClient):
    """Sans type_geo_tx_recours, le type par défaut est 'dep' (département)."""
    response = client.get("/tx_recours", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["typ_geo"] == "dep", (
            f"Attendu 'dep', obtenu '{row['typ_geo']}'"
        )


def test_tx_recours_type_geo_dep(client: TestClient):
    """Avec type_geo_tx_recours=dep, les codes sont des départements."""
    response = client.get("/tx_recours", params={
        "annee": "23",
        "type_geo_tx_recours": "dep",
    })
    assert response.status_code == 200
    data = response.json()
    for row in data:
        assert row["typ_geo"] == "dep"


def test_tx_recours_type_geo_reg(client: TestClient):
    """Avec type_geo_tx_recours=reg, typ_geo vaut 'reg' dans la réponse."""
    response = client.get("/tx_recours", params={
        "annee": "23",
        "type_geo_tx_recours": "reg",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert row["typ_geo"] == "reg"


def test_tx_recours_type_geo_zon(client: TestClient):
    """Avec type_geo_tx_recours=zon, typ_geo vaut 'zon' dans la réponse."""
    response = client.get("/tx_recours", params={
        "annee": "23",
        "type_geo_tx_recours": "zon",
    })
    assert response.status_code == 200
    data = response.json()
    for row in data:
        assert row["typ_geo"] == "zon"


def test_tx_recours_type_geo_ts(client: TestClient):
    """Avec type_geo_tx_recours=ts, typ_geo vaut 'ts' dans la réponse."""
    response = client.get("/tx_recours", params={
        "annee": "23",
        "type_geo_tx_recours": "ts",
    })
    assert response.status_code == 200
    data = response.json()
    for row in data:
        assert row["typ_geo"] == "ts"


# ---------------------------------------------------------------------------
# Tests — cohérence des taux
# ---------------------------------------------------------------------------

def test_tx_recours_nb_pat_inferieur_nb_sej(client: TestClient):
    """nb_pat <= nb_sej : un patient peut avoir plusieurs séjours."""
    response = client.get("/tx_recours", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["nb_pat"] <= row["nb_sej"], (
            f"nb_pat ({row['nb_pat']}) > nb_sej ({row['nb_sej']})"
        )


def test_tx_recours_nb_pop_positif(client: TestClient):
    """La population de chaque zone est strictement positive."""
    response = client.get("/tx_recours", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["nb_pop"] > 0, f"nb_pop <= 0 pour le code {row['code']}"


def test_tx_recours_taux_positifs(client: TestClient):
    """Les taux de recours sont tous positifs."""
    response = client.get("/tx_recours", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["tx_recours_brut_sej"] > 0
        assert row["tx_recours_brut_pat"] > 0
        assert row["tx_recours_standard_sej"] > 0
        assert row["tx_recours_standard_pat"] > 0


# ---------------------------------------------------------------------------
# Tests — paramètre `annee` obligatoire
# ---------------------------------------------------------------------------

def test_tx_recours_sans_annee_retourne_422(client: TestClient):
    """Sans le paramètre `annee` obligatoire, l'API retourne 422."""
    response = client.get("/tx_recours")
    assert response.status_code == 422
