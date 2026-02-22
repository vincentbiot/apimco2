# =============================================================================
# app/routers/dmi_med.py — Endpoint GET /dmi_med
#
# L'endpoint le plus complexe de l'API. Retourne un mélange de lignes :
#   - Médicaments onéreux (UCD — Unités Communes de Dispensation)
#   - Dispositifs Médicaux Implantables (DMI — codifiés via LPP)
#
# La colonne 'datasource' distingue les deux types :
#   - "med" : médicament UCD, avec hiérarchie ATC (Anatomical Therapeutic Chemical)
#   - "dmi" : dispositif médical LPP, avec hiérarchie LPP
#
# Structure asymétrique :
#   Les colonnes code_ucd, lib_ucd, atc1..atc5 sont null pour les DMI.
#   Les colonnes code_lpp, hiera, hiera_libelle sont null pour les médicaments.
#
# Côté client, ce datasource permet de séparer les onglets Médicaments et DMI
# et d'afficher des drill-down hiérarchiques différents (ATC vs LPP).
#
# Hiérarchie ATC (5 niveaux) :
#   atc1 : Système anatomique principal (ex : "L" = Antinéoplasiques)
#   atc2 : Sous-groupe thérapeutique    (ex : "L01")
#   atc3 : Sous-groupe pharmacologique  (ex : "L01F")
#   atc4 : Sous-groupe chimique         (ex : "L01FG")
#   atc5 : Substance chimique           (ex : "L01FG01" = Bevacizumab)
#
# Hiérarchie LPP (1 niveau dans le mock) :
#   hiera : code de la catégorie LPP (ex : "04" = Implants articulaires)
# =============================================================================

from fastapi import APIRouter, Depends

from app.generators.mock_data import generate_dmi_med_rows
from app.models.params import CommonQueryParams
from app.models.responses import DmiMedRow

router = APIRouter(tags=["Endpoints MCO"])


@router.get(
    "/dmi_med",
    response_model=list[DmiMedRow],
    # response_model_exclude_none=True : les champs null (code_ucd pour les DMI,
    # code_lpp pour les médicaments) sont exclus de la sérialisation JSON.
    # Cela allège la réponse et reflète le comportement réel de l'API.
    response_model_exclude_none=True,
    summary="Médicaments onéreux (UCD) et dispositifs médicaux implantables (DMI/LPP)",
)
def get_dmi_med(
    params: CommonQueryParams = Depends(),
) -> list[dict]:
    """
    Retourne les données de valorisation des médicaments onéreux (UCD) et
    des dispositifs médicaux implantables (DMI/LPP). Utilisé par le module
    Valorisation médicaments/DMI.

    ### Structure asymétrique de la réponse

    La colonne `datasource` distingue deux types de lignes :

    **Lignes médicaments (`datasource = "med"`)** :

    | Colonne | Description |
    |---|---|
    | `code` | Code UCD |
    | `code_ucd` | Code UCD (identique à `code`) |
    | `lib_ucd` | Libellé du médicament |
    | `atc1`..`atc5` | Hiérarchie ATC (5 niveaux) |
    | `code_lpp`, `hiera`, `hiera_libelle` | `null` |

    **Lignes DMI (`datasource = "dmi"`)** :

    | Colonne | Description |
    |---|---|
    | `code` | Code LPP |
    | `code_lpp` | Code LPP (identique à `code`) |
    | `hiera` | Code hiérarchie LPP |
    | `hiera_libelle` | Libellé de la hiérarchie LPP |
    | `code_ucd`, `lib_ucd`, `atc1`..`atc5` | `null` |

    **Colonnes communes** :
    `nb`, `nb_sej`, `nb_pat`, `mnt_remb`, `duree_moy_sej`, `age_moy`

    ### Règles côté client

    - Pas d'appel à `verif_data()` (code commenté dans la source R).
    - `datasource` est utilisé pour séparer les onglets Médicaments et DMI.
    - `atc1`..`atc5` permettent la navigation drill-down dans le module.
    """
    return generate_dmi_med_rows(var=params.var)
