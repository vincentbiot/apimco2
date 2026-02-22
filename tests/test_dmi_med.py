# =============================================================================
# tests/test_dmi_med.py — Tests de l'endpoint GET /dmi_med
# =============================================================================

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Tests — structure de base (sans var)
# ---------------------------------------------------------------------------

def test_dmi_med_retourne_200(client: TestClient):
    """Un appel valide avec annee retourne le code HTTP 200."""
    response = client.get("/dmi_med", params={"annee": "23"})
    assert response.status_code == 200


def test_dmi_med_retourne_liste_non_vide(client: TestClient):
    """La réponse est une liste non vide."""
    response = client.get("/dmi_med", params={"annee": "23"})
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_dmi_med_colonnes_communes(client: TestClient):
    """Chaque ligne contient les colonnes communes (spec §3.5)."""
    response = client.get("/dmi_med", params={"annee": "23"})
    data = response.json()
    colonnes_communes = {
        "datasource", "code", "nb", "nb_sej", "nb_pat",
        "mnt_remb", "duree_moy_sej", "age_moy",
    }
    for row in data:
        assert colonnes_communes.issubset(row.keys()), (
            f"Colonnes manquantes : {colonnes_communes - row.keys()}"
        )


def test_dmi_med_datasource_valide(client: TestClient):
    """datasource vaut 'med' ou 'dmi' dans chaque ligne."""
    response = client.get("/dmi_med", params={"annee": "23"})
    data = response.json()
    for row in data:
        assert row["datasource"] in ("med", "dmi"), (
            f"datasource invalide : {row['datasource']}"
        )


def test_dmi_med_contient_med_et_dmi(client: TestClient):
    """La réponse contient à la fois des lignes med et des lignes dmi."""
    response = client.get("/dmi_med", params={"annee": "23"})
    data = response.json()
    datasources = {row["datasource"] for row in data}
    assert "med" in datasources, "Aucune ligne médicament dans la réponse"
    assert "dmi" in datasources, "Aucune ligne DMI dans la réponse"


def test_dmi_med_neuf_lignes_sans_var(client: TestClient):
    """Sans var, 9 lignes (5 UCD + 4 LPP dans la nomenclature)."""
    response = client.get("/dmi_med", params={"annee": "23"})
    data = response.json()
    assert len(data) == 9, f"Attendu 9 lignes, obtenu {len(data)}"


# ---------------------------------------------------------------------------
# Tests — structure des lignes médicaments (datasource='med')
# ---------------------------------------------------------------------------

def test_dmi_med_lignes_med_ont_colonnes_ucd(client: TestClient):
    """Les lignes med ont code_ucd, lib_ucd et les niveaux ATC."""
    response = client.get("/dmi_med", params={"annee": "23"})
    data = response.json()
    lignes_med = [row for row in data if row["datasource"] == "med"]
    assert len(lignes_med) > 0
    colonnes_ucd = {"code_ucd", "lib_ucd", "atc1", "atc2", "atc3", "atc4", "atc5"}
    for row in lignes_med:
        for col in colonnes_ucd:
            assert col in row, f"Colonne UCD manquante : {col}"
        # Les champs UCD ne doivent pas être null pour les médicaments
        assert row["code_ucd"] is not None
        assert row["lib_ucd"] is not None


def test_dmi_med_lignes_med_pas_de_lpp(client: TestClient):
    """Les lignes med n'ont pas de code_lpp renseigné (null)."""
    response = client.get("/dmi_med", params={"annee": "23"})
    data = response.json()
    lignes_med = [row for row in data if row["datasource"] == "med"]
    for row in lignes_med:
        # code_lpp peut être absent (exclude_none) ou null selon la sérialisation
        if "code_lpp" in row:
            assert row["code_lpp"] is None


# ---------------------------------------------------------------------------
# Tests — structure des lignes DMI (datasource='dmi')
# ---------------------------------------------------------------------------

def test_dmi_med_lignes_dmi_ont_colonnes_lpp(client: TestClient):
    """Les lignes dmi ont code_lpp, hiera et hiera_libelle."""
    response = client.get("/dmi_med", params={"annee": "23"})
    data = response.json()
    lignes_dmi = [row for row in data if row["datasource"] == "dmi"]
    assert len(lignes_dmi) > 0
    for row in lignes_dmi:
        assert "code_lpp" in row, "Colonne code_lpp manquante pour un DMI"
        assert row["code_lpp"] is not None
        assert "hiera" in row
        assert row["hiera"] is not None


def test_dmi_med_lignes_dmi_pas_de_ucd(client: TestClient):
    """Les lignes dmi n'ont pas de code_ucd renseigné (null)."""
    response = client.get("/dmi_med", params={"annee": "23"})
    data = response.json()
    lignes_dmi = [row for row in data if row["datasource"] == "dmi"]
    for row in lignes_dmi:
        if "code_ucd" in row:
            assert row["code_ucd"] is None


# ---------------------------------------------------------------------------
# Tests — avec le paramètre var
# ---------------------------------------------------------------------------

def test_dmi_med_avec_var_finess(client: TestClient):
    """Avec var=finess, les lignes ont datasource et finess."""
    response = client.get("/dmi_med", params={
        "annee": "23",
        "var": "finess",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for row in data:
        assert "datasource" in row
        assert "finess" in row


def test_dmi_med_avec_var_plus_de_lignes(client: TestClient):
    """Avec var=finess, plus de lignes qu'en cas de base."""
    response_base = client.get("/dmi_med", params={"annee": "23"})
    response_var = client.get("/dmi_med", params={"annee": "23", "var": "finess"})
    assert len(response_var.json()) > len(response_base.json())


# ---------------------------------------------------------------------------
# Tests — paramètre `annee` obligatoire
# ---------------------------------------------------------------------------

def test_dmi_med_sans_annee_retourne_400(client: TestClient) -> None:
    """Sans le paramètre `annee` obligatoire, l'API retourne 400 (étape 6 : handler 422→400)."""
    response = client.get("/dmi_med")
    assert response.status_code == 400


# =============================================================================
# Tests étape 6 — Gestion des erreurs et secret statistique
# =============================================================================


def test_dmi_med_404_perimetre_vide(client: TestClient) -> None:
    """simulate_vide=TRUE doit retourner HTTP 404 (spec §5.1)."""
    response = client.get(
        "/dmi_med",
        params={"annee": "23", "simulate_vide": "TRUE"},
    )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_dmi_med_petit_effectif_methode_b(client: TestClient) -> None:
    """
    simulate_petit_effectif=TRUE retourne la Méthode B (spec §5.2).

    Une seule ligne avec uniquement des colonnes string (pas de colonnes numériques).
    """
    response = client.get(
        "/dmi_med",
        params={"annee": "23", "simulate_petit_effectif": "TRUE"},
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1

    row = data[0]
    # La ligne identifiant doit être "datasource"
    assert "datasource" in row
    for value in row.values():
        assert isinstance(value, str), f"Valeur non-string trouvée : {value!r}"
