# =============================================================================
# app/routers/tx_recours.py — Endpoint GET /tx_recours
#
# Cet endpoint retourne les taux de recours géographiques.
# Particularités :
#   - Pas de paramètre `var` (pas de ventilation multi-dimensionnelle)
#   - Un paramètre spécifique `type_geo_tx_recours` contrôle le niveau géo
#   - Les taux sont exprimés pour 1000 habitants
#
# Concept FastAPI rappelé : Query() avec valeur par défaut
#   Un paramètre avec une valeur par défaut est optionnel dans la query string.
#   Query("dep", ...) signifie que si type_geo_tx_recours est absent, "dep" est utilisé.
#
#   Doc : https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
# =============================================================================

from fastapi import APIRouter, Depends, Query

from app.generators.mock_data import generate_tx_recours_rows
from app.models.params import CommonQueryParams
from app.models.responses import TxRecoursRow

router = APIRouter(tags=["Endpoints MCO"])


@router.get(
    "/tx_recours",
    response_model=list[TxRecoursRow],
    summary="Taux de recours géographiques (séjours et patients / 1000 habitants)",
)
def get_tx_recours(
    params: CommonQueryParams = Depends(),
    # Paramètre spécifique à cet endpoint (spec §2.4)
    # Valeur par défaut "dep" : si absent, on retourne les taux par département
    type_geo_tx_recours: str = Query(
        "dep",
        description=(
            "Niveau géographique pour les taux de recours. "
            "Valeurs possibles : 'dep' (département, défaut), 'reg' (région), "
            "'zon' (zone ARS), 'ts' (territoire de santé), 'geo' (communes/IRIS)."
        ),
    ),
) -> list[dict]:
    """
    Retourne les taux de recours géographiques : nombre de séjours et de
    patients rapporté à 1000 habitants, par zone géographique.

    Utilisé par le module Taux de recours pour la cartographie Leaflet.

    ### Paramètre spécifique

    `type_geo_tx_recours` contrôle le niveau géographique :
    - `dep` : par département (défaut)
    - `reg` : par région
    - `zon` : par zone ARS
    - `ts` : par territoire de santé
    - `geo` : par commune/IRIS (niveau fin)

    ### Colonnes de la réponse

    | Colonne | Description |
    |---|---|
    | `typ_geo` | Type géographique demandé |
    | `code` | Code de la zone géographique |
    | `nb_sej` | Nombre de séjours |
    | `nb_pat` | Nombre de patients |
    | `nb_pop` | Population de la zone (habitants) |
    | `tx_recours_brut_sej` | Taux brut en séjours (/ 1000 hab) |
    | `tx_recours_brut_pat` | Taux brut en patients (/ 1000 hab) |
    | `tx_recours_standard_sej` | Taux standardisé en séjours (/ 1000 hab) |
    | `tx_recours_standard_pat` | Taux standardisé en patients (/ 1000 hab) |

    ### Règles côté client

    Le module filtre `!is.na(code)` et effectue une jointure avec la carte
    géographique (`cartes[[type_rgp]]`) via le champ `codgeo`.
    """
    return generate_tx_recours_rows(type_geo=type_geo_tx_recours)
