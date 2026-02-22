# =============================================================================
# app/routers/resume.py — Endpoint GET /resume
#
# Concepts FastAPI introduits dans cette étape :
#
#   1. APIRouter
#      Permet de déclarer des routes dans un fichier séparé de main.py.
#      Le router fonctionne exactement comme l'objet FastAPI() pour les
#      décorateurs (@router.get, @router.post...), mais il doit être
#      "enregistré" dans l'application principale via app.include_router().
#
#      Avantages :
#        - Code organisé par endpoint ou par domaine métier
#        - Possibilité d'ajouter un préfixe commun (ex : "/api/v1")
#        - Partage de tags, dependencies, responses entre plusieurs routes
#
#      Doc : https://fastapi.tiangolo.com/tutorial/bigger-applications/
#
#   2. app.include_router() (dans main.py)
#      Après avoir créé un router, il faut l'enregistrer dans l'application.
#      C'est fait dans app/main.py avec : app.include_router(resume.router)
#      On peut passer un prefix="/api" ou des tags=["Groupe"] au moment de
#      l'include pour éviter de les répéter dans chaque décorateur.
#
#      Doc : https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-the-apirouter
#
#   3. Depends() avec CommonQueryParams (rappel de l'étape 2)
#      L'injection de dépendances fonctionne identiquement dans un router.
#      params: CommonQueryParams = Depends() injecte une instance construite
#      automatiquement à partir des query params de la requête HTTP.
#
#      Doc : https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/
#
#   4. response_model (rappel de l'étape 2)
#      Déclarer response_model=list[ResumeRow] a plusieurs effets :
#        - Validation sortante : FastAPI vérifie que la réponse correspond
#        - Filtrage : les champs non déclarés dans ResumeRow sont retirés
#          (sauf ceux tolérés par extra='allow' dans BaseRow)
#        - Documentation : le schéma de réponse apparaît dans /docs
#
# Architecture de l'endpoint :
#   1. FastAPI parse les query params et injecte CommonQueryParams + params spécifiques
#   2. Le bool_nb_pat est converti de str ("TRUE"/"FALSE") en bool Python
#   3. generate_resume_rows() est appelé avec les paramètres pertinents
#   4. FastAPI sérialise la liste de dicts en JSON et retourne HTTP 200
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.generators.mock_data import generate_resume_rows, parse_var
from app.models.params import CommonQueryParams
from app.models.responses import ResumeRow

# -----------------------------------------------------------------------------
# Concept FastAPI — HTTPException (étape 6)
#
# HTTPException est l'outil standard pour retourner une erreur HTTP depuis
# un endpoint. On l'importe depuis fastapi et on l'utilise avec raise.
#
# Syntaxe :
#   raise HTTPException(status_code=404, detail="Aucun séjour trouvé")
#
# FastAPI intercepte l'exception et retourne automatiquement :
#   HTTP 404  {"detail": "Aucun séjour trouvé"}
#
# Le paramètre detail peut être une chaîne, un dict ou n'importe quel objet
# JSON-sérialisable. Il apparaît dans le corps de la réponse.
#
# Doc : https://fastapi.tiangolo.com/tutorial/handling-errors/
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Création du router
#
# APIRouter() crée un objet routeur. Les paramètres passés ici s'appliquent
# à toutes les routes déclarées dans ce module :
#   - tags=["Endpoints MCO"] : groupe toutes ces routes sous le label "Endpoints MCO"
#     dans la doc Swagger (/docs). Le groupe apparaît comme une section dépliable.
#   - On pourrait aussi passer prefix="/v1" pour préfixer toutes les routes.
#
# Doc : https://fastapi.tiangolo.com/tutorial/bigger-applications/#apirouter
# -----------------------------------------------------------------------------
router = APIRouter(tags=["Endpoints MCO"])


@router.get(
    "/resume",
    response_model=list[ResumeRow],
    # response_model_exclude_none=True : exclut les champs None de la réponse JSON.
    # Sans ce flag, FastAPI inclut tous les champs déclarés dans ResumeRow même
    # quand leur valeur est None (ex : nb_pat=None quand bool_nb_pat n'est pas TRUE).
    # Avec ce flag, seuls les champs avec une valeur non-None sont sérialisés.
    # Doc : https://fastapi.tiangolo.com/tutorial/response-model/#response_model_exclude_none
    response_model_exclude_none=True,
    summary="Agrégats de séjours MCO ventilés selon `var`",
)
def get_resume(
    # --- Paramètres communs injectés via Depends() ---
    # CommonQueryParams regroupe les ~35 paramètres de filtrage partagés
    # par tous les endpoints. Depends() construit l'instance automatiquement.
    params: CommonQueryParams = Depends(),
    # --- Paramètres spécifiques à /resume ---
    # Ces deux paramètres ne sont pas dans CommonQueryParams car ils ne
    # s'appliquent qu'à cet endpoint (spec §2.4).
    bool_nb_pat: str | None = Query(
        None,
        description=(
            "Si 'TRUE', retourne la colonne `nb_pat` même sans paramètre `var` "
            "(cas du résumé de périmètre). "
            "`nb_pat` peut contenir la chaîne `'petit_effectif'` "
            "si le périmètre contient moins de 10 séjours (spec §5.2 méthode A)."
        ),
    ),
    trancheage: str | None = Query(
        None,
        description=(
            "Points de coupure de la pyramide des âges, séparés par `_` "
            "(ex : `'10_20_30_40_50_60_70_80_90'`). "
            "Utilisé conjointement avec `var=sexe_trancheage`. "
            "Si absent, des bornes standard sont appliquées."
        ),
    ),
) -> list[dict]:
    """
    Endpoint principal et polyvalent de l'API MCO.

    Retourne des agrégats de séjours ventilés selon le paramètre `var`.
    Utilisé par 10 fonctions R différentes couvrant : résumé de périmètre,
    pyramide des âges, évolution mensuelle, répartition FINESS, casemix GHM,
    modes d'entrée/sortie, diagnostic principal, DMS, analyse flexible et cartographie.

    ### Logique de ventilation (paramètre `var`)

    | Valeur de `var` | Colonnes ajoutées | Description |
    |---|---|---|
    | *(absent)* | *(aucune)* | 1 ligne agrégée (résumé de périmètre) |
    | `ghm` | `ghm` | 1 ligne par code GHM |
    | `mois` | `mois` | 1 ligne par mois (1–12) |
    | `sexe_trancheage` | `sexe`, `trancheage` | Pyramide des âges |
    | `finess` | `finess` | Répartition par établissement |
    | `duree` | `duree` | Distribution de la DMS (seulement `duree` + `nb_sej`) |
    | `ghm_typhosp` | `ghm`, `typhosp` | Produit cartésien GHM × type hospit. |

    Voir la spec §4 pour la liste complète des 29 variables de ventilation.

    ### Paramètre `var` sans valeur

    Si `var` est absent et `bool_nb_pat=TRUE` : une seule ligne agrégée avec `nb_pat`.
    Si `var` est absent et `bool_nb_pat` non fourni : une seule ligne sans `nb_pat`.

    ### Secret statistique (`petit_effectif`)

    Si `bool_nb_pat=TRUE` et effectif < 10, `nb_pat` contient la chaîne
    `"petit_effectif"` au lieu d'un entier (spec §5.2 méthode A).
    """
    # -------------------------------------------------------------------------
    # Simulation 404 — périmètre vide (aucun séjour)
    #
    # Si simulate_vide="TRUE", on lève une HTTPException avec status_code=404.
    # Cela simule le cas réel où le filtre (GHM, FINESS, âge...) est trop
    # restrictif et ne correspond à aucun séjour dans la base.
    #
    # Le client R (`call_api_and_unwrap()`) lit le status_code et retourne
    # l'entier 404 au lieu d'un data.frame. Le module appelant affiche
    # alors un message "aucun résultat".
    # -------------------------------------------------------------------------
    if params.simulate_vide is not None and params.simulate_vide.upper() == "TRUE":
        raise HTTPException(
            status_code=404,
            detail="Aucun séjour ne correspond aux critères de filtrage.",
        )

    # Convertir bool_nb_pat de str en bool Python.
    # Le client R envoie la chaîne "TRUE" (et non True ou 1).
    # On considère que toute valeur absente ou différente de "TRUE" → False.
    include_nb_pat: bool = bool_nb_pat is not None and bool_nb_pat.upper() == "TRUE"

    # -------------------------------------------------------------------------
    # Simulation petit effectif — Méthode A (spec §5.2)
    #
    # La Méthode A s'applique uniquement à /resume avec bool_nb_pat=TRUE.
    # Quand l'effectif est < 10 séjours, nb_pat ne peut pas être divulgué :
    # la colonne contient la chaîne "petit_effectif" au lieu d'un entier.
    #
    # Le client R détecte ce cas via :
    #   if (is.character(data$nb_pat)) { ... # affiche avertissement }
    #
    # Dans le mock, on simule ce cas avec simulate_petit_effectif=TRUE.
    # On génère une ligne avec nb_sej < 10 et nb_pat = "petit_effectif".
    # -------------------------------------------------------------------------
    simulate_pe: bool = (
        params.simulate_petit_effectif is not None
        and params.simulate_petit_effectif.upper() == "TRUE"
    )
    if simulate_pe and include_nb_pat and params.var is None:
        # Retour Méthode A : nb_sej faible, nb_pat = chaîne "petit_effectif"
        return JSONResponse(
            content=[
                {
                    "nb_sej": 5,
                    "nb_pat": "petit_effectif",
                    "duree_moy_sej": 3.2,
                    "tx_dc": 0.0,
                    "tx_male": 0.6,
                    "age_moy": 45.3,
                }
            ]
        )

    # Déléguer la génération de données au module generators/mock_data.py.
    # On passe :
    #   - params.var    : la chaîne de ventilation (ex : "ghm", "sexe_trancheage")
    #   - trancheage    : les bornes de découpage pour les tranches d'âge
    #   - include_nb_pat : si True, inclure nb_pat dans la réponse sans var
    rows = generate_resume_rows(
        var=params.var,
        trancheage_param=trancheage,
        bool_nb_pat=include_nb_pat,
    )

    # -------------------------------------------------------------------------
    # CAS SPÉCIAL : var=duree — distribution de la durée de séjour
    #
    # La réponse DMS contient uniquement {"duree": N, "nb_sej": X} par ligne,
    # sans les colonnes statistiques habituelles (tx_dc, tx_male, age_moy).
    # Ce format ne satisfait pas la validation de ResumeRow (qui requiert ces
    # champs), donc on retourne une JSONResponse directement.
    #
    # Concept : JSONResponse
    #   Retourner une JSONResponse au lieu d'un dict/list Python permet de
    #   contourner la validation et la sérialisation de response_model.
    #   FastAPI détecte le type de retour et n'applique pas response_model
    #   quand la fonction retourne une Response (ou sous-classe comme JSONResponse).
    #
    #   Cas d'usage typiques :
    #     - Schéma de réponse variable selon les paramètres (notre cas)
    #     - Code HTTP personnalisé (ex : 201 Created, 204 No Content)
    #     - Headers HTTP personnalisés dans la réponse
    #
    #   Doc : https://fastapi.tiangolo.com/advanced/custom-response/
    # -------------------------------------------------------------------------
    var_tokens = parse_var(params.var)
    if var_tokens == ["duree"]:
        # content= doit être un objet JSON-sérialisable (dict, list, str, int...)
        return JSONResponse(content=rows)

    # Pour tous les autres cas, FastAPI sérialise la liste de dicts via
    # response_model=list[ResumeRow] et response_model_exclude_none=True.
    return rows
