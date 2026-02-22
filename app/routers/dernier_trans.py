# =============================================================================
# app/routers/dernier_trans.py — Endpoint GET /dernier_trans
#
# Cet endpoint est le plus simple de l'API :
#   - Pas de paramètre `var` (pas de ventilation)
#   - Pas de logique petit_effectif (données administratives)
#   - Structure de réponse fixe : une ligne par établissement FINESS
#
# Concept FastAPI rappelé : Tags
#   Les tags regroupent visuellement les endpoints dans la doc Swagger (/docs).
#   Tous les endpoints MCO partagent le tag "Endpoints MCO", ce qui les
#   affiche dans la même section dépliable.
#
#   Doc : https://fastapi.tiangolo.com/tutorial/path-operation-configuration/#tags
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException

from app.generators.mock_data import generate_dernier_trans_rows
from app.models.params import CommonQueryParams
from app.models.responses import DernierTransRow

# Création du router — même tag que les autres endpoints pour les grouper dans Swagger
router = APIRouter(tags=["Endpoints MCO"])


@router.get(
    "/dernier_trans",
    response_model=list[DernierTransRow],
    summary="Date de dernière transmission PMSI par établissement",
)
def get_dernier_trans(
    params: CommonQueryParams = Depends(),
) -> list[dict]:
    """
    Retourne la date de dernière transmission PMSI pour chaque établissement
    du périmètre. Une ligne par établissement FINESS.

    ### Particularités de cet endpoint

    - **Pas de paramètre `var`** : la structure de réponse est toujours la même.
    - **Exempt du secret statistique** : les données de transmission sont
      administratives (pas de séjours patients), donc le contrôle `petit_effectif`
      ne s'applique pas (spec §3.8).
    - **Colonne `annee` supprimée côté client** : le module R appelle
      `dplyr::select(-annee)` avant affichage.

    ### Colonnes de la réponse

    | Colonne | Description |
    |---|---|
    | `annee` | Année PMSI (4 chiffres) |
    | `finess` | Code FINESS PMSI (9 chiffres) |
    | `rs` | Raison sociale de l'établissement |
    | `secteur` | Secteur : `"PU"` (public) ou `"PR"` (privé) |
    | `categ` | Catégorie : `"CH"`, `"CL"`, etc. |
    | `derniere_transmission` | Date au format `"YYYY-MM-DD"` |
    """
    # Simulation 404 — périmètre vide (spec §5.1)
    # Note : /dernier_trans est EXEMPT du petit_effectif (données administratives,
    # spec §3.8). Seul le 404 est géré ici.
    if params.simulate_vide is not None and params.simulate_vide.upper() == "TRUE":
        raise HTTPException(
            status_code=404,
            detail="Aucun établissement ne correspond aux critères de filtrage.",
        )

    # Appel direct au générateur — pas de var, pas de logique petit_effectif
    return generate_dernier_trans_rows(annee_param=params.annee)
