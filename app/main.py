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

import logging
import random
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.config import settings

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

# Création d'un logger pour ce module.
# logging.getLogger(__name__) crée (ou récupère) un logger nommé d'après
# le module courant ("app.main"). C'est la convention Python recommandée.
logger = logging.getLogger(__name__)


# =============================================================================
# Concept FastAPI — Lifespan events (étape 7)
#
#   Le paramètre lifespan de FastAPI() permet d'enregistrer du code à exécuter
#   au DÉMARRAGE et à l'ARRÊT de l'application, via un gestionnaire de contexte
#   asynchrone (asynccontextmanager).
#
#   Structure :
#     @asynccontextmanager
#     async def lifespan(app: FastAPI) -> AsyncGenerator:
#         # Code de démarrage (startup) — exécuté avant d'accepter les requêtes
#         yield
#         # Code d'arrêt (shutdown) — exécuté après la fermeture du serveur
#
#   Avantage par rapport aux anciens @app.on_event("startup"/"shutdown") :
#   Cette approche est recommandée depuis FastAPI 0.93+ car elle est plus
#   propre et compatible avec les tests.
#
#   Cas d'usage typiques :
#     - Initialiser une connexion à la base de données au démarrage
#     - Libérer les ressources (connexions, fichiers) à l'arrêt
#     - Fixer un seed aléatoire global (notre cas ici)
#
#   Doc : https://fastapi.tiangolo.com/advanced/events/
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Gestionnaire de cycle de vie de l'application.

    Startup : configure le générateur aléatoire selon le RANDOM_SEED configuré.
    Shutdown : rien à faire pour ce projet (pas de connexion DB à fermer).
    """
    # --- Startup ---
    if settings.random_seed is not None:
        # Fixe le seed global du module random.
        # Conséquence : toutes les données mock générées seront identiques
        # d'un démarrage à l'autre, tant que le seed est le même.
        # Utile pour les démos reproductibles et les tests d'intégration.
        random.seed(settings.random_seed)
        logger.info(
            "Seed aléatoire fixé à %d (données mock déterministes)",
            settings.random_seed,
        )
    else:
        logger.info(
            "Aucun seed configuré — données mock aléatoires à chaque appel "
            "(définir RANDOM_SEED dans .env pour des données déterministes)"
        )

    logger.info(
        "API Mock MCO démarrée — environnement=%s, port=%d, CORS=%s",
        settings.environment,
        settings.port,
        settings.cors_origins,
    )

    # `yield` sépare startup et shutdown.
    # L'application accepte les requêtes entre le yield et la fin du bloc.
    yield

    # --- Shutdown ---
    logger.info("API Mock MCO arrêtée.")


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
# Le paramètre lifespan connecte notre gestionnaire de cycle de vie.
app = FastAPI(
    title="API Mock Activité MCO",
    description=(
        "API de simulation des données d'activité MCO (Médecine, Chirurgie, Obstétrique). "
        "Permet de développer et tester des clients R sans connexion à la base PMSI réelle."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# =============================================================================
# Concept FastAPI — CORSMiddleware (étape 7)
#
#   CORS (Cross-Origin Resource Sharing) est un mécanisme de sécurité des
#   navigateurs. Quand une application web (ex : Shiny R sur localhost:3838)
#   appelle une API sur une autre origine (ex : localhost:8000), le navigateur
#   vérifie d'abord si le serveur l'autorise via des en-têtes HTTP spéciaux.
#
#   FastAPI intègre le middleware CORS de Starlette. Il suffit de l'ajouter
#   avec app.add_middleware() avant de déclarer les routes.
#
#   Paramètres importants :
#     - allow_origins      : liste des origines autorisées (["*"] = tout autoriser)
#     - allow_credentials  : autoriser les cookies et les en-têtes d'authentification
#     - allow_methods      : méthodes HTTP autorisées (["*"] = toutes)
#     - allow_headers      : en-têtes HTTP autorisés dans les requêtes cross-origin
#
#   En développement, ["*"] est pratique. En production, spécifier les origines
#   exactes (ex : ["https://myapp.example.com"]) pour limiter les accès.
#
#   Doc : https://fastapi.tiangolo.com/tutorial/cors/
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    # Les origines sont lues depuis la configuration (variable CORS_ORIGINS).
    # Par défaut "*" pour autoriser tout (utile en dev/démo).
    allow_origins=settings.cors_origins_list,
    # allow_credentials=True autoriserait les cookies et les en-têtes Authorization.
    # On le désactive car cette API mock ne gère pas d'authentification.
    allow_credentials=False,
    # Autoriser toutes les méthodes HTTP (GET, POST, OPTIONS, etc.)
    allow_methods=["*"],
    # Autoriser tous les en-têtes HTTP
    allow_headers=["*"],
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
