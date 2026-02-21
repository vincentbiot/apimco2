# =============================================================================
# tests/test_resume.py — Tests de l'endpoint GET /resume
#
# Concepts pytest + FastAPI testclient utilisés :
#
#   1. Paramètres de requête avec params={}
#      client.get("/resume", params={"annee": "23"}) construit automatiquement
#      l'URL /resume?annee=23. Le dict params est encodé en query string.
#
#   2. response.json()
#      Désérialise le corps de la réponse JSON en dict/list Python.
#      Équivalent de json.loads(response.text).
#
#   3. Assertions pytest
#      pytest utilise le mot-clé assert standard de Python.
#      En cas d'échec, pytest affiche les valeurs réelles pour faciliter
#      le débogage (contrairement à unittest qui nécessite self.assertEqual).
#
#   4. Fixture client
#      La fixture "client" est définie dans tests/conftest.py.
#      pytest la détecte automatiquement — pas besoin de l'importer.
#
# Organisation des tests :
#   - test_health()                         → GET / retourne {"status": "ok"}
#   - test_resume_annee_obligatoire()       → sans annee → 422
#   - test_resume_sans_var()               → 1 ligne agrégée
#   - test_resume_bool_nb_pat()            → nb_pat inclus si bool_nb_pat=TRUE
#   - test_resume_var_ghm()                → plusieurs lignes avec colonne ghm
#   - test_resume_var_mois()               → 12 lignes avec colonne mois
#   - test_resume_var_finess()             → lignes avec colonne finess
#   - test_resume_var_dp()                 → lignes avec colonne dp
#   - test_resume_var_duree()              → format distribution DMS (duree + nb_sej)
#   - test_resume_var_sexe_trancheage()    → colonnes sexe + trancheage
#   - test_resume_var_trancheage_custom()  → bornes personnalisées
#   - test_resume_var_modentprov_modsordest() → colonnes modentprov + modsordest
#   - test_resume_var_combine()            → plusieurs var combinés
#   - test_resume_colonnes_base()          → présence de toutes les colonnes de base
# =============================================================================

from fastapi.testclient import TestClient


# =============================================================================
# Test de l'endpoint de santé (vérifie que l'app démarre correctement)
# =============================================================================


def test_health(client: TestClient) -> None:
    """GET / doit retourner HTTP 200 avec {"status": "ok"}."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# =============================================================================
# Tests des paramètres obligatoires / validation
# =============================================================================


def test_resume_annee_obligatoire(client: TestClient) -> None:
    """
    Sans le paramètre annee, l'API doit retourner HTTP 422 (Unprocessable Entity).

    422 est le code standard de FastAPI quand un paramètre obligatoire est absent
    ou invalide. Le corps de la réponse contient un tableau "detail" qui décrit
    les erreurs de validation.
    """
    response = client.get("/resume")
    assert response.status_code == 422

    # Vérifier que le message d'erreur mentionne le paramètre "annee"
    detail = response.json()["detail"]
    champs_erreur = [err["loc"] for err in detail]
    # Le champ manquant doit être signalé dans la localisation de l'erreur
    assert any("annee" in loc for loc in champs_erreur)


def test_resume_annee_format_invalide(client: TestClient) -> None:
    """
    annee doit être exactement 2 chiffres. Un format invalide doit retourner 422.
    """
    # 4 chiffres → invalide (pattern ^\d{2}$ ne matche pas)
    response = client.get("/resume", params={"annee": "2023"})
    assert response.status_code == 422

    # Lettre → invalide
    response = client.get("/resume", params={"annee": "ab"})
    assert response.status_code == 422


# =============================================================================
# Tests du comportement sans paramètre var (ligne agrégée)
# =============================================================================


def test_resume_sans_var(client: TestClient) -> None:
    """
    Sans paramètre var, GET /resume retourne exactement 1 ligne agrégée.

    C'est le cas "résumé de périmètre" — toute l'activité MCO de l'année
    résumée en une seule ligne.
    """
    response = client.get("/resume", params={"annee": "23"})
    assert response.status_code == 200

    data = response.json()
    # Une seule ligne agrégée
    assert isinstance(data, list)
    assert len(data) == 1

    row = data[0]
    # Colonnes de base obligatoires (spec §3.1)
    assert "nb_sej" in row
    assert "duree_moy_sej" in row
    assert "tx_dc" in row
    assert "tx_male" in row
    assert "age_moy" in row
    # Sans bool_nb_pat, nb_pat ne doit pas être présent
    assert "nb_pat" not in row


def test_resume_bool_nb_pat(client: TestClient) -> None:
    """
    Avec bool_nb_pat=TRUE, la colonne nb_pat doit être présente.

    nb_pat peut être un entier ou la chaîne "petit_effectif" (spec §5.2).
    """
    response = client.get(
        "/resume",
        params={"annee": "23", "bool_nb_pat": "TRUE"},
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    row = data[0]

    # nb_pat doit être présent
    assert "nb_pat" in row
    # nb_pat doit être un entier ou la chaîne "petit_effectif"
    assert isinstance(row["nb_pat"], int) or row["nb_pat"] == "petit_effectif"


def test_resume_bool_nb_pat_false(client: TestClient) -> None:
    """
    Avec bool_nb_pat=FALSE (ou absent), nb_pat ne doit pas être dans la réponse.
    """
    response = client.get(
        "/resume",
        params={"annee": "23", "bool_nb_pat": "FALSE"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "nb_pat" not in data[0]


# =============================================================================
# Tests de la ventilation par var (colonnes dynamiques)
# =============================================================================


def test_resume_var_ghm(client: TestClient) -> None:
    """
    var=ghm retourne plusieurs lignes, chacune avec une colonne 'ghm'.

    La colonne 'ghm' contient des codes GHM de 6 caractères (ex : '05M09T').
    """
    response = client.get("/resume", params={"annee": "23", "var": "ghm"})
    assert response.status_code == 200

    data = response.json()
    # Plusieurs lignes (au moins 2)
    assert len(data) > 1

    # Chaque ligne doit avoir la colonne de ventilation
    for row in data:
        assert "ghm" in row
        assert isinstance(row["ghm"], str)
        # nb_pat est toujours inclus quand var est fourni (spec §3.1)
        assert "nb_pat" in row


def test_resume_var_mois(client: TestClient) -> None:
    """
    var=mois retourne 12 lignes (une par mois), avec une colonne 'mois' entière.
    """
    response = client.get("/resume", params={"annee": "23", "var": "mois"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 12

    mois_values = [row["mois"] for row in data]
    # Les 12 mois doivent être présents (1 à 12)
    assert sorted(mois_values) == list(range(1, 13))


def test_resume_var_finess(client: TestClient) -> None:
    """
    var=finess retourne des lignes avec une colonne 'finess' (code 9 chiffres).
    """
    response = client.get("/resume", params={"annee": "23", "var": "finess"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0
    for row in data:
        assert "finess" in row
        # Les codes FINESS ont 9 chiffres
        assert len(row["finess"]) == 9


def test_resume_var_dp(client: TestClient) -> None:
    """
    var=dp retourne des lignes avec une colonne 'dp' (code CIM-10).
    """
    response = client.get("/resume", params={"annee": "23", "var": "dp"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0
    for row in data:
        assert "dp" in row


def test_resume_var_duree(client: TestClient) -> None:
    """
    var=duree retourne une distribution DMS : colonnes 'duree' et 'nb_sej' uniquement.

    Cas spécial de la spec §3.1 : la réponse ne contient PAS les colonnes statistiques
    habituelles (tx_dc, tx_male, age_moy, duree_moy_sej), uniquement la distribution
    du nombre de séjours par durée.
    """
    response = client.get("/resume", params={"annee": "23", "var": "duree"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0

    for row in data:
        # Colonnes attendues pour la distribution DMS
        assert "duree" in row
        assert "nb_sej" in row
        # Les colonnes habituelles ne doivent PAS être présentes
        assert "tx_dc" not in row
        assert "tx_male" not in row
        assert "age_moy" not in row


def test_resume_var_sexe_trancheage(client: TestClient) -> None:
    """
    var=sexe_trancheage retourne le produit cartésien sexe × tranches d'âge.

    Chaque ligne a 2 colonnes de ventilation : 'sexe' (str) et 'trancheage' (str).
    Avec 2 sexes et 10 tranches standard → au moins 20 lignes.
    """
    response = client.get(
        "/resume",
        params={"annee": "23", "var": "sexe_trancheage"},
    )
    assert response.status_code == 200

    data = response.json()
    # 2 sexes × 10 tranches d'âge standard = 20 lignes minimum
    assert len(data) >= 20

    for row in data:
        # Deux colonnes de ventilation pour le var composé
        assert "sexe" in row
        assert "trancheage" in row
        assert row["sexe"] in ("1", "2")
        # Format attendu : "[0-10 ans]", "[11-20 ans]", etc.
        assert row["trancheage"].startswith("[")


def test_resume_var_trancheage_custom(client: TestClient) -> None:
    """
    Le paramètre trancheage permet des bornes personnalisées.

    Avec trancheage=10_20_30 → 4 tranches : [0-10], [11-20], [21-30], [31+]
    Et 2 sexes → 8 lignes au total.
    """
    response = client.get(
        "/resume",
        params={
            "annee": "23",
            "var": "sexe_trancheage",
            "trancheage": "10_20_30",
        },
    )
    assert response.status_code == 200

    data = response.json()
    # 2 sexes × 4 tranches = 8 lignes
    assert len(data) == 8

    tranche_values = list({row["trancheage"] for row in data})
    assert len(tranche_values) == 4


def test_resume_var_modentprov_modsordest(client: TestClient) -> None:
    """
    var=modentprov_modsordest retourne le produit cartésien modes d'entrée × sortie.

    Chaque ligne a 2 colonnes : 'modentprov' et 'modsordest'.
    """
    response = client.get(
        "/resume",
        params={"annee": "23", "var": "modentprov_modsordest"},
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0

    for row in data:
        assert "modentprov" in row
        assert "modsordest" in row


def test_resume_var_combine(client: TestClient) -> None:
    """
    Plusieurs variables peuvent être combinées : var=ghm_typhosp.

    Chaque ligne doit avoir les colonnes de toutes les variables combinées.
    """
    response = client.get(
        "/resume",
        params={"annee": "23", "var": "ghm_typhosp"},
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0

    for row in data:
        assert "ghm" in row
        assert "typhosp" in row


# =============================================================================
# Tests des colonnes de base et des plages de valeurs
# =============================================================================


def test_resume_colonnes_base(client: TestClient) -> None:
    """
    Vérifie que les colonnes de base sont dans des plages réalistes (spec §3).

    Plages attendues pour des données MCO :
      - nb_sej      : entier positif
      - duree_moy_sej : 1.0 à 15.0 jours
      - tx_dc       : 0.0 à 0.10 (taux de décès < 10%)
      - tx_male     : 0.0 à 1.0
      - age_moy     : 0.0 à 120.0 ans
    """
    response = client.get(
        "/resume",
        params={"annee": "23", "var": "ghm"},
    )
    assert response.status_code == 200
    data = response.json()

    for row in data:
        assert row["nb_sej"] > 0
        assert 1.0 <= row["duree_moy_sej"] <= 15.0
        assert 0.0 <= row["tx_dc"] <= 0.10
        assert 0.0 <= row["tx_male"] <= 1.0
        assert 0.0 <= row["age_moy"] <= 120.0
        # nb_pat toujours présent avec var, et cohérent avec nb_sej
        assert row["nb_pat"] <= row["nb_sej"]


def test_resume_parametres_filtrage_ignores(client: TestClient) -> None:
    """
    Les paramètres de filtrage (sexe, typhosp, etc.) sont acceptés sans erreur.

    Le mock ne filtre pas réellement les données (c'est du mock), mais il doit
    accepter tous les paramètres communs définis dans CommonQueryParams sans
    retourner d'erreur de validation.
    """
    response = client.get(
        "/resume",
        params={
            "annee": "23",
            "var": "ghm",
            "sexe": "1",
            "typhosp": "M_C",
            "moissortie": "1_6",
        },
    )
    # Les paramètres de filtrage sont acceptés (pas d'erreur 422)
    assert response.status_code == 200
    assert len(response.json()) > 0
