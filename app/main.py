# =============================================================================
# app/main.py — Point d'entrée de l'application FastAPI
#
# Concepts FastAPI introduits dans cette étape :
#
#   1. FastAPI()
#      L'objet application principal. C'est l'équivalent de Flask() en Flask
#      ou de express() en Node.js. Il gère le routage, la validation, la
#      génération automatique de la doc Swagger, etc.
#      Doc : https://fastapi.tiangolo.com/tutorial/first-steps/
#
#   2. @app.get("/")
#      Un "décorateur de path operation". Il dit à FastAPI :
#        - écoute les requêtes HTTP GET
#        - sur le chemin "/"
#        - et appelle la fonction décorée pour les traiter
#      Doc : https://fastapi.tiangolo.com/tutorial/first-steps/#define-a-path-operation-decorator
#
#   3. Retour JSON automatique
#      FastAPI sérialise automatiquement les dict et les list Python en JSON.
#      Pas besoin de jsonify() comme en Flask.
#      Doc : https://fastapi.tiangolo.com/tutorial/first-steps/#return-the-content
#
#   4. app.include_router() — NOUVEAU (étape 4)
#      Enregistre un APIRouter dans l'application principale.
#      Le router est défini dans app/routers/resume.py et contient l'endpoint
#      GET /resume. Cette approche permet de garder main.py simple et d'organiser
#      les endpoints en modules séparés.
#
#      Paramètres possibles :
#        - router          : l'objet APIRouter à inclure (obligatoire)
#        - prefix          : préfixe de chemin (ex : "/api/v1") — optionnel
#        - tags            : liste de tags Swagger — optionnel (on peut aussi les
#                           déclarer dans le router lui-même, comme ici)
#        - dependencies    : dépendances FastAPI communes à toutes les routes du router
#
#      Doc : https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-the-apirouter
#
# Pour lancer le serveur :
#   uvicorn app.main:app --reload --port 8000
#
#   - "app.main"  : module Python (fichier app/main.py)
#   - "app"       : variable dans ce fichier (l'objet FastAPI())
#   - "--reload"  : redémarre le serveur à chaque modification de fichier (dev uniquement)
#
# Doc Swagger générée automatiquement : http://localhost:8000/docs
# =============================================================================

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

# Import des routers — un module par endpoint.
# Étape 4 : /resume (endpoint principal polyvalent)
# Étape 5 : les 7 endpoints restants de la spec
from app.routers import (
    actes,
    dernier_trans,
    diag_assoc,
    dmi_med,
    resume,
    resume_prec_annee,
    tx_recours,
    um,
)

# =============================================================================
# Concepts FastAPI introduits à l'étape 6 — Gestion des erreurs
#
#   5. HTTPException
#      Permet de lever manuellement une réponse d'erreur HTTP depuis n'importe
#      quelle fonction d'endpoint ou de dépendance.
#
#      Exemple :
#        from fastapi import HTTPException
#        raise HTTPException(status_code=404, detail="Aucun séjour trouvé")
#
#      FastAPI intercepte l'exception et retourne une réponse JSON :
#        {"detail": "Aucun séjour trouvé"} avec le code HTTP 404.
#
#      Doc : https://fastapi.tiangolo.com/tutorial/handling-errors/
#
#   6. @app.exception_handler() — Exception handlers personnalisés
#      Permet de remplacer le comportement par défaut de FastAPI pour certaines
#      exceptions. La fonction décorée reçoit la requête et l'exception, et
#      doit retourner une Response.
#
#      Cas d'usage ici : RequestValidationError (levée par FastAPI quand un
#      paramètre obligatoire est absent ou invalide) retourne 422 par défaut.
#      La spec MCO attend un 400 (Bad Request). On surcharge ce comportement
#      avec un handler personnalisé.
#
#      La fonction handler DOIT être async (coroutine) car FastAPI l'appelle
#      dans son boucle d'événements asyncio.
#
#      Doc : https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers
#
#   7. RequestValidationError
#      Exception Pydantic/Starlette levée quand la validation des paramètres
#      d'entrée échoue (paramètre manquant, type incorrect, pattern non respecté).
#      Par défaut FastAPI la convertit en HTTP 422. Ici on la convertit en 400.
#
#      Doc : https://fastapi.tiangolo.com/tutorial/handling-errors/#requestvalidationerror-vs-validationerror
# =============================================================================

# Instanciation de l'application FastAPI.
# Les paramètres title, description et version alimentent la doc Swagger (/docs).
app = FastAPI(
    title="API Mock Activité MCO",
    description=(
        "API de simulation des données d'activité MCO (Médecine, Chirurgie, Obstétrique). "
        "Permet de développer et tester des clients R sans connexion à la base PMSI réelle."
    ),
    version="0.1.0",
)


# =============================================================================
# Exception handler — Conversion 422 → 400 pour les erreurs de validation
#
# FastAPI retourne HTTP 422 (Unprocessable Entity) par défaut quand un paramètre
# obligatoire est absent ou invalide (RequestValidationError).
#
# La spec MCO §5.1 attend HTTP 400 (Bad Request) pour ces cas.
# On installe un handler personnalisé qui intercepte RequestValidationError
# et retourne 400 avec le même corps JSON que le 422 natif.
#
# Note : ce handler s'applique à TOUS les endpoints de l'application.
# Les clients qui lisent uniquement le status_code recevront 400.
# =============================================================================


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Transforme les erreurs de validation Pydantic (paramètres manquants ou invalides)
    en réponse HTTP 400 au lieu du 422 par défaut de FastAPI.

    Le corps de la réponse conserve le format natif FastAPI :
        {"detail": [{"loc": [...], "msg": "...", "type": "..."}]}
    """
    # exc.errors() retourne la liste des erreurs de validation Pydantic.
    # Elle contient pour chaque erreur : loc (localisation), msg (message), type.
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


# =============================================================================
# Enregistrement des routers
#
# app.include_router() connecte le router à l'application principale.
# Après cet appel, toutes les routes déclarées dans resume.router sont
# disponibles dans l'application (ici : GET /resume).
#
# On n'utilise pas de prefix ici car les routes déclarent leur chemin complet
# directement dans le router (ex : @router.get("/resume")).
# =============================================================================

# Étape 4 — endpoint principal
app.include_router(resume.router)

# Étape 5 — les 7 endpoints restants (dans l'ordre croissant de complexité)
app.include_router(dernier_trans.router)        # le plus simple : pas de var
app.include_router(tx_recours.router)           # type_geo_tx_recours, pas de var
app.include_router(resume_prec_annee.router)    # multi-année, similaire à /resume
app.include_router(diag_assoc.router)           # code_diag (CIM-10) + var optionnel
app.include_router(um.router)                   # code_rum + duree_moy_rum + var
app.include_router(actes.router)                # code_ccam + colonnes CCAM spécifiques
app.include_router(dmi_med.router)              # le plus complexe : mix med/dmi


# =============================================================================
# GET / — Endpoint de santé (health check)
#
# Le décorateur @app.get("/") déclare un endpoint HTTP GET sur la route racine.
# La fonction health_check est appelée à chaque requête GET sur "/".
# =============================================================================
@app.get(
    "/",
    summary="Vérification de l'état de l'API",
    tags=["Santé"],
)
def health_check() -> dict:
    """
    Endpoint de santé (*health check*).

    Retourne un statut `ok` pour confirmer que le serveur est opérationnel.
    Utile pour les scripts de démarrage ou les sondes de liveness en production.
    """
    # FastAPI convertit automatiquement ce dict Python en JSON : {"status": "ok"}
    return {"status": "ok"}
