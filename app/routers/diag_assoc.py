# =============================================================================
# app/routers/diag_assoc.py — Endpoint GET /diag_assoc
#
# Retourne les diagnostics associés significatifs (DAS) des séjours.
# L'identifiant primaire `code_diag` (code CIM-10) est toujours présent.
#
# Particularités :
#   - Pas de `nb_pat` dans la réponse de base (contrairement à /resume)
#   - La colonne `code_diag` est renommée en `diag` côté client R
#   - Le paramètre `var=dr` ajoute une colonne DR (diagnostic relié)
#     comme n'importe quelle autre ventilation
#
# Concept FastAPI rappelé : Tags pour la documentation Swagger
#   Tous les endpoints MCO partagent le même tag pour être regroupés
#   dans la même section de la doc Swagger (/docs).
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.generators.mock_data import build_petit_effectif_row_b, generate_diag_assoc_rows
from app.models.params import CommonQueryParams
from app.models.responses import DiagAssocRow

router = APIRouter(tags=["Endpoints MCO"])


@router.get(
    "/diag_assoc",
    response_model=list[DiagAssocRow],
    response_model_exclude_none=True,
    summary="Diagnostics associés significatifs (DAS) des séjours MCO",
)
def get_diag_assoc(
    params: CommonQueryParams = Depends(),
) -> list[dict]:
    """
    Retourne les diagnostics associés significatifs (DAS) des séjours
    du périmètre. Utilisé par le module DAS.

    ### Structure de la réponse

    Toujours présente :
    - `code_diag` : code CIM-10 du diagnostic associé
      *(renommé en `diag` côté client R dans `call_api_and_unwrap()`)*
    - Colonnes statistiques : `nb_sej`, `duree_moy_sej`, `tx_dc`, `tx_male`, `age_moy`

    Conditionnelle :
    - Colonnes de `var` si `var` est fourni

    ### Logique de ventilation

    Sans `var` : 1 ligne par code CIM-10 de la nomenclature.

    Avec `var=finess` : 1 ligne par (code_diag × finess).

    Avec `var=dr` : 1 ligne par (code_diag × code_DR), le DR étant un code
    CIM-10 du diagnostic relié — traité comme n'importe quelle dimension
    de ventilation.

    ### Règles côté client

    - `verif_data(result, "duree_moy_sej")` est appelé après réception.
    - Si `"dr"` est dans `flex_param`, `verif_data(result, "dr")` est aussi appelé.
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
        return JSONResponse(content=build_petit_effectif_row_b("code_diag", "I10"))

    return generate_diag_assoc_rows(var=params.var)
