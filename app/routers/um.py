# =============================================================================
# app/routers/um.py — Endpoint GET /um
#
# Retourne les données par type d'unité médicale (UM/RUM).
# L'identifiant primaire `code_rum` est toujours présent.
#
# Particularité principale :
#   La colonne `duree_moy_rum` est spécifique à cet endpoint.
#   Elle représente la durée moyenne au niveau RUM (sous-séjour dans une unité
#   médicale), distincte de `duree_moy_sej` (durée du séjour complet).
#   Un séjour peut couvrir plusieurs RUM successifs (ex : réa puis médecine).
#
# Dans un MCO multi-RUM : duree_moy_rum < duree_moy_sej
# La colonne code_rum est renommée en 'um' côté client R.
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.generators.mock_data import build_petit_effectif_row_b, generate_um_rows
from app.models.params import CommonQueryParams
from app.models.responses import UmRow

router = APIRouter(tags=["Endpoints MCO"])


@router.get(
    "/um",
    response_model=list[UmRow],
    response_model_exclude_none=True,
    summary="Données par unité médicale (UM/RUM) avec durée moyenne de séjour au niveau RUM",
)
def get_um(
    params: CommonQueryParams = Depends(),
) -> list[dict]:
    """
    Retourne les données d'activité par type d'unité médicale (UM).
    Utilisé par le module UM.

    ### Structure de la réponse

    Toujours présentes :
    - `code_rum` : code du type d'unité médicale (ex : `"01"` médecine, `"04"` réa)
      *(renommé en `um` côté client R dans `call_api_and_unwrap()`)*
    - `duree_moy_rum` : durée moyenne de séjour au niveau RUM (**spécifique à /um**)
    - Colonnes statistiques : `nb_sej`, `duree_moy_sej`, `tx_dc`, `tx_male`, `age_moy`

    Conditionnelle :
    - Colonnes de `var` si `var` est fourni

    ### Différence duree_moy_sej vs duree_moy_rum

    | Colonne | Niveau | Description |
    |---|---|---|
    | `duree_moy_sej` | Séjour complet | Durée totale du séjour |
    | `duree_moy_rum` | RUM (sous-séjour) | Durée dans cette unité médicale uniquement |

    En pratique, `duree_moy_rum ≤ duree_moy_sej` pour les séjours multi-RUM.

    ### Types d'unités médicales (code_rum)

    | Code | Libellé |
    |---|---|
    | `01` | Médecine |
    | `02` | Chirurgie |
    | `03` | Obstétrique |
    | `04` | Réanimation |
    | `13` | Soins intensifs |
    | `18` | Ambulatoire |

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
        return JSONResponse(content=build_petit_effectif_row_b("code_rum", "01"))

    return generate_um_rows(var=params.var)
