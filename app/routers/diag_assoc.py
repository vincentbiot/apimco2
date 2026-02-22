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

from fastapi import APIRouter, Depends

from app.generators.mock_data import generate_diag_assoc_rows
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
    return generate_diag_assoc_rows(var=params.var)
