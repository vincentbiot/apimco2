# =============================================================================
# app/routers/resume_prec_annee.py — Endpoint GET /resume_prec_annee
#
# Variante multi-annuelle de /resume. Similaire dans sa structure mais avec
# deux différences importantes :
#   1. La colonne `annee` (4 chiffres) est toujours présente — même sans `var`
#   2. La colonne `nb_pat` est toujours incluse (sans condition bool_nb_pat)
#
# Cet endpoint est utilisé par le module multi-year pour afficher l'évolution
# des indicateurs sur les 5 dernières années.
#
# Concept FastAPI rappelé : Factorisation avec les routers
#   La logique commune (parsing de var, génération de données, injection de
#   CommonQueryParams) est réutilisée ici sans duplication grâce à l'injection
#   de dépendances et aux fonctions du module generators/.
#
#   Doc : https://fastapi.tiangolo.com/tutorial/bigger-applications/
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.generators.mock_data import build_petit_effectif_row_b, generate_resume_prec_annee_rows
from app.models.params import CommonQueryParams
from app.models.responses import ResumePrecAnneeRow

router = APIRouter(tags=["Endpoints MCO"])


@router.get(
    "/resume_prec_annee",
    response_model=list[ResumePrecAnneeRow],
    # response_model_exclude_none=True : exclut les champs None pour alléger la réponse.
    # Utile car les colonnes de ventilation var sont dynamiques et les champs
    # non fournis (ex : duree_moy_sej si absent) ne doivent pas apparaître.
    response_model_exclude_none=True,
    summary="Agrégats multi-annuels MCO (5 années consécutives)",
)
def get_resume_prec_annee(
    params: CommonQueryParams = Depends(),
    # Le paramètre trancheage est spécifique aux cas var=sexe_trancheage,
    # identique à /resume. Réutilisé ici pour la cohérence.
    trancheage: str | None = Query(
        None,
        description=(
            "Points de coupure de la pyramide des âges, séparés par `_` "
            "(ex : `'10_20_30_40_50_60_70_80_90'`). "
            "Utilisé conjointement avec `var=sexe_trancheage`."
        ),
    ),
) -> list[dict]:
    """
    Retourne les agrégats de séjours sur les 5 dernières années pour l'analyse
    multi-annuelle.

    ### Différences avec `/resume`

    | Aspect | `/resume` | `/resume_prec_annee` |
    |---|---|---|
    | Colonne `annee` | Absente | Toujours présente (4 chiffres) |
    | Colonne `nb_pat` | Conditionnelle (`bool_nb_pat`) | Toujours présente |
    | Nombre d'années | 1 | 5 (annee-4 à annee) |

    ### Logique de génération

    Sans `var` : 5 lignes (une par année de `annee-4` à `annee`).

    Avec `var=ghm` : 5 × N lignes (produit cartésien années × codes GHM),
    limité à 100 lignes.

    ### Règles côté client

    Le client appelle `verif_data(result, "duree_moy_sej")` après réception,
    et si `"dr"` est dans `flex_param`, appelle aussi `verif_data(result, "dr")`.
    """
    # Simulation 404 — périmètre vide (spec §5.1)
    if params.simulate_vide is not None and params.simulate_vide.upper() == "TRUE":
        raise HTTPException(
            status_code=404,
            detail="Aucun séjour ne correspond aux critères de filtrage.",
        )

    # Simulation petit effectif — Méthode B (spec §5.2)
    # Pour les endpoints autres que /resume, on retourne un tableau avec une
    # seule ligne ne contenant que des colonnes string (aucune valeur numérique).
    # Le client R détecte ce cas via : all(sapply(data, function(col) !any(is.numeric(col))))
    if (
        params.simulate_petit_effectif is not None
        and params.simulate_petit_effectif.upper() == "TRUE"
    ):
        return JSONResponse(content=build_petit_effectif_row_b("annee", "2023"))

    return generate_resume_prec_annee_rows(
        var=params.var,
        annee_param=params.annee,
        trancheage_param=trancheage,
    )
