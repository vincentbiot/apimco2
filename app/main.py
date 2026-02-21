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

from fastapi import FastAPI

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
