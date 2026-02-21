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
# Pour lancer le serveur :
#   uvicorn app.main:app --reload --port 8000
#
#   - "app.main"  : module Python (fichier app/main.py)
#   - "app"       : variable dans ce fichier (l'objet FastAPI())
#   - "--reload"  : redémarre le serveur à chaque modification de fichier (dev uniquement)
#
# Doc Swagger générée automatiquement : http://localhost:8000/docs
# =============================================================================

from fastapi import Depends, FastAPI, Query

from app.models.params import CommonQueryParams
from app.models.responses import ResumeRow

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


# Le décorateur @app.get("/") déclare un endpoint HTTP GET sur la route racine.
# La fonction health_check est appelée à chaque requête GET sur "/".
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


# =============================================================================
# STUB — GET /resume
#
# Ce endpoint est un stub introduit à l'étape 2 pour :
#   1. Démontrer que CommonQueryParams fonctionne avec Depends()
#   2. Permettre de valider les critères de l'étape 2 :
#      - GET /resume?annee=23   → 200 OK
#      - GET /resume            → 422 Unprocessable Entity (annee manquant)
#      - Doc Swagger /docs      → tous les paramètres sont visibles
#
# Il sera remplacé par le router complet app/routers/resume.py à l'étape 4.
#
# Concept : response_model
#   En déclarant response_model=list[ResumeRow], FastAPI :
#     - Valide que la fonction retourne bien une liste de ResumeRow
#     - Filtre les champs non déclarés dans ResumeRow
#     - Affiche le schéma de réponse dans la doc Swagger (/docs)
#   Doc : https://fastapi.tiangolo.com/tutorial/response-model/
#
# Concept : Depends()
#   Depends(CommonQueryParams) injecte une instance de CommonQueryParams
#   construite automatiquement à partir des query params de la requête.
#   Si annee est absent, FastAPI retourne 422 AVANT d'appeler la fonction.
#   Doc : https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/
# =============================================================================


@app.get(
    "/resume",
    response_model=list[ResumeRow],
    summary="Agrégats de séjours MCO — stub étape 2",
    tags=["Endpoints MCO"],
)
def get_resume(
    params: CommonQueryParams = Depends(),
    # Paramètres spécifiques à /resume (non inclus dans CommonQueryParams)
    bool_nb_pat: str | None = Query(
        None,
        description=(
            "Si 'TRUE', retourne la colonne nb_pat dans la réponse. "
            "nb_pat peut contenir 'petit_effectif' si effectif < 10 séjours (spec §5.2)."
        ),
    ),
    trancheage: str | None = Query(
        None,
        description=(
            "Points de coupure pour la pyramide des âges, séparés par '_' "
            "(ex : '10_20_30_40_50_60_70_80_90'). "
            "Utilisé avec var=sexe_trancheage."
        ),
    ),
) -> list[dict]:
    """
    **[STUB — étape 2]** Retourne les agrégats de séjours MCO.

    Endpoint principal et polyvalent, utilisé par 10 fonctions R différentes.
    Le paramètre `var` contrôle les colonnes de ventilation de la réponse.

    **Implémentation complète prévue à l'étape 4.**

    En attendant, ce stub retourne une ligne de données fictives pour valider
    que `annee` est bien obligatoire (erreur 422 si absent) et que la doc
    Swagger affiche correctement tous les paramètres via `CommonQueryParams`.
    """
    # Stub : retourne une seule ligne agrégée fictive
    # La logique réelle (ventilation par var, génération mock) sera ajoutée à l'étape 4.
    return [
        {
            "nb_sej": 125432,
            "nb_pat": 98210,
            "duree_moy_sej": 5.43,
            "tx_dc": 0.0187,
            "tx_male": 0.4823,
            "age_moy": 62.7,
        }
    ]
