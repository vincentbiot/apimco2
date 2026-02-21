# =============================================================================
# tests/conftest.py — Fixtures pytest partagées entre tous les fichiers de test
#
# Concepts pytest introduits dans cette étape :
#
#   1. Fixture pytest
#      Une fixture est une fonction décorée avec @pytest.fixture.
#      Elle prépare un objet (ici : un client HTTP) et le met à disposition
#      des fonctions de test qui en ont besoin.
#
#      Avantages par rapport à un setup global :
#        - Chaque test reçoit une instance fraîche (isolation)
#        - La fixture peut être partagée via conftest.py entre plusieurs
#          fichiers de test sans avoir à l'importer manuellement
#        - On peut contrôler le scope (function, module, session) pour
#          réutiliser l'objet ou le recréer à chaque test
#
#      Pour utiliser une fixture dans un test, il suffit de déclarer son
#      nom comme paramètre de la fonction de test :
#          def test_mon_endpoint(client):  # pytest injecte la fixture "client"
#              response = client.get("/")
#
#      Doc : https://docs.pytest.org/en/stable/how-to/fixtures.html
#
#   2. TestClient (Starlette / FastAPI)
#      TestClient est un client HTTP synchrone fourni par Starlette (le framework
#      sur lequel FastAPI est construit). Il permet d'envoyer de vraies requêtes
#      HTTP à l'application FastAPI sans lancer de serveur réseau.
#
#      Fonctionnement :
#        - TestClient(app) crée un client lié à l'application
#        - client.get("/path", params={"key": "val"}) envoie une requête GET
#        - La réponse est un objet Response de la bibliothèque requests
#          avec response.status_code, response.json(), response.text, etc.
#
#      Note : TestClient utilise httpx en interne (depuis FastAPI 0.89).
#      On peut aussi utiliser httpx.AsyncClient directement pour les tests
#      asynchrones, mais TestClient est plus simple pour commencer.
#
#      Doc : https://fastapi.tiangolo.com/tutorial/testing/
# =============================================================================

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """
    Fixture pytest qui fournit un client HTTP de test pour l'application FastAPI.

    Portée (scope) par défaut : "function" — le client est recréé pour chaque
    fonction de test, garantissant l'isolation entre les tests.

    Utilisation dans un test :
        def test_health(client):
            response = client.get("/")
            assert response.status_code == 200

    Note :
        TestClient peut être utilisé comme context manager avec `with` pour
        déclencher les événements de démarrage/arrêt de l'application
        (lifespan events). Ici, on l'utilise sans context manager car
        l'application n'a pas encore de code de démarrage (étape 7).
    """
    return TestClient(app)
