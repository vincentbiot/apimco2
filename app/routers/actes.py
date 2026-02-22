# =============================================================================
# app/routers/actes.py — Endpoint GET /actes
#
# Retourne les actes classants CCAM des séjours du périmètre.
# L'identifiant primaire `code_ccam` est toujours présent.
#
# Différences par rapport à /resume et autres endpoints :
#   - Pas de `tx_dc` dans la réponse (schéma spécifique, spec §3.6)
#   - Pas de `nb_pat` (schéma spécifique)
#   - Colonnes supplémentaires : nb_acte, extension_pmsi, acte_activ, is_classant
#
# Codes CCAM (Classification Commune des Actes Médicaux) :
#   Format 7 caractères : 4 lettres + 3 chiffres (ex : DZQM006)
#   L'extension PMSI est un chiffre supplémentaire (ex : "0", "1")
#   acte_activ représente le niveau d'activité de l'acte (1 = acte principal)
#   is_classant : 1 si l'acte est classant (détermine le GHM), 0 sinon
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.generators.mock_data import build_petit_effectif_row_b, generate_actes_rows
from app.models.params import CommonQueryParams
from app.models.responses import ActesRow

router = APIRouter(tags=["Endpoints MCO"])


@router.get(
    "/actes",
    response_model=list[ActesRow],
    response_model_exclude_none=True,
    summary="Actes classants CCAM des séjours MCO",
)
def get_actes(
    params: CommonQueryParams = Depends(),
) -> list[dict]:
    """
    Retourne les actes CCAM (Classification Commune des Actes Médicaux) des
    séjours du périmètre. Utilisé par le module Actes classants.

    ### Structure de la réponse

    Toujours présentes :
    - `code_ccam` : code CCAM de l'acte (7 caractères, ex : `"DZQM006"`)
    - `extension_pmsi` : extension PMSI de l'acte (`"0"` ou `"1"`)
    - `nb_acte` : nombre d'actes réalisés (≥ `nb_sej`)
    - `nb_sej` : nombre de séjours ayant cet acte
    - `duree_moy_sej` : durée moyenne de séjour
    - `tx_male` : taux de patients masculins
    - `age_moy` : âge moyen
    - `acte_activ` : niveau d'activité (`"1"` à `"5"`)
    - `is_classant` : `1` (acte classant) ou `0` (acte non classant)

    Conditionnelle :
    - Colonnes de `var` si `var` est fourni

    ### Différences avec `/resume`

    Cet endpoint **n'inclut pas** `tx_dc` ni `nb_pat` dans la réponse.
    Les colonnes `nb_acte`, `extension_pmsi`, `acte_activ` et `is_classant`
    sont **spécifiques** à cet endpoint.

    ### Règles côté client

    - `verif_data(result, "duree_moy_sej")` est appelé après réception.
    - Si `"dr"` est dans `flex_param`, `verif_data(result, "dr")` est aussi appelé.
    - Le module enrichit `code_ccam` avec le libellé depuis `df_ccam`.
    """
    # Simulation 404 — périmètre vide (spec §5.1)
    if params.simulate_vide is not None and params.simulate_vide.upper() == "TRUE":
        raise HTTPException(
            status_code=404,
            detail="Aucun séjour ne correspond aux critères de filtrage.",
        )

    # Simulation petit effectif — Méthode B (spec §5.2)
    if (
        params.simulate_petit_effectif is not None
        and params.simulate_petit_effectif.upper() == "TRUE"
    ):
        return JSONResponse(content=build_petit_effectif_row_b("code_ccam", "DZQM006"))

    return generate_actes_rows(var=params.var)
