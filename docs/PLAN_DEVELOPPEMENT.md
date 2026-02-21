# Plan de développement — API Mock Activité MCO

**Date** : 2026-02-21
**Stack** : Python + FastAPI (voir [ADR-001](./ADR-001-choix-fastapi.md))
**Spécification** : [MOCK_API_SPEC.md](./MOCK_API_SPEC.md)

---

## Vue d'ensemble

Le développement est découpé en **7 étapes progressives**. Chaque étape introduit de nouveaux concepts FastAPI et produit un livrable fonctionnel testable.

```
Étape 1 → Étape 2 → Étape 3 → Étape 4 → Étape 5 → Étape 6 → Étape 7
Squelette  Modèles   Données   Endpoint   Tous les  Erreurs   Docker
FastAPI    Pydantic  mock      /resume    endpoints & petits  & CI
                                                    effectifs
```

---

## Étape 1 — Squelette FastAPI et premier endpoint "hello world"

### Objectif
Mettre en place la structure du projet et vérifier que tout fonctionne.

### Ce que tu vas apprendre (concepts FastAPI)

| Concept | Description | Doc officielle |
|---|---|---|
| **`FastAPI()`** | L'objet application principal. Équivalent de `Flask()` en Flask | [First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/) |
| **Décorateur `@app.get()`** | Déclare une route HTTP GET. Chaque fonction décorée = un endpoint | [Path Operations](https://fastapi.tiangolo.com/tutorial/first-steps/#define-a-path-operation-decorator) |
| **`uvicorn`** | Le serveur ASGI qui exécute l'app FastAPI. Le flag `--reload` relance le serveur à chaque modification de fichier | [Uvicorn](https://www.uvicorn.org/) |
| **Retour JSON automatique** | FastAPI convertit automatiquement les `dict` et `list` Python en JSON | [First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/#return-the-content) |

### Livrables

- `requirements.txt` avec les dépendances (fastapi, uvicorn, pydantic, httpx, pytest, ruff)
- `app/main.py` : application FastAPI minimale avec un endpoint `GET /` qui retourne `{"status": "ok"}`
- `app/__init__.py` : fichier vide (pour que Python reconnaisse le package)
- Vérification : lancer `uvicorn app.main:app --reload` et ouvrir `http://localhost:8000/docs`

### Fichiers à créer

```
app/
├── __init__.py
└── main.py
requirements.txt
```

### Critère de validation
- `GET /` retourne `{"status": "ok"}` avec un code 200
- L'interface Swagger est accessible à `/docs`

---

## Étape 2 — Modèles Pydantic pour les paramètres et les réponses

### Objectif
Définir les modèles de données qui valideront automatiquement les entrées et les sorties de l'API.

### Ce que tu vas apprendre (concepts FastAPI / Pydantic)

| Concept | Description | Doc officielle |
|---|---|---|
| **Pydantic `BaseModel`** | Classe Python avec des champs typés. Pydantic valide automatiquement les données à l'instanciation | [Pydantic Models](https://fastapi.tiangolo.com/tutorial/body/#create-your-data-model) |
| **`Query()`** | Permet de déclarer des paramètres de query string avec validation (défaut, regex, description) | [Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/) |
| **`Optional` / `None`** | Un paramètre `str | None = None` est optionnel dans la query string | [Optional Parameters](https://fastapi.tiangolo.com/tutorial/query-params/#optional-parameters) |
| **`response_model`** | Spécifie le modèle Pydantic de la réponse → doc Swagger automatique + validation sortante | [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/) |
| **`Depends()`** | Injection de dépendances : permet de factoriser les paramètres communs aux 8 endpoints dans une seule classe | [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) |

### Livrables

- `app/models/params.py` : classe `CommonQueryParams` regroupant les ~25 paramètres communs (avec `Depends()`)
- `app/models/responses.py` : modèles Pydantic pour chaque type de réponse (ResumeRow, DiagAssocRow, UmRow, etc.)

### Fichiers à créer

```
app/
├── models/
│   ├── __init__.py
│   ├── params.py       # Paramètres de requête communs
│   └── responses.py    # Modèles de réponse
```

### Exemple concret — `CommonQueryParams`

```python
from fastapi import Query

class CommonQueryParams:
    """
    Paramètres de requête communs à tous les endpoints.

    Utilise le mécanisme d'injection de dépendances de FastAPI (Depends).
    Au lieu de répéter ces paramètres dans chaque endpoint, on les déclare
    une seule fois ici et on les injecte avec Depends(CommonQueryParams).

    Doc : https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/
    """
    def __init__(
        self,
        annee: str = Query(..., description="Année sur 2 chiffres (ex: '23' pour 2023)"),
        var: str | None = Query(None, description="Variable(s) de ventilation, séparées par '_'"),
        moissortie: str | None = Query(None, description="Plage de mois 'debut_fin'"),
        sexe: str | None = Query(None, description="'1' (H) ou '2' (F)"),
        age: str | None = Query(None, description="Plage d'âge 'min_max'"),
        # ... autres paramètres
    ):
        self.annee = annee
        self.var = var
        self.moissortie = moissortie
        self.sexe = sexe
        self.age = age
```

### Critère de validation
- Un appel `GET /resume?annee=23` est accepté
- Un appel `GET /resume` (sans `annee`) retourne une erreur 422 avec un message clair
- La doc Swagger affiche tous les paramètres avec leurs descriptions

---

## Étape 3 — Données de référence et générateur mock

### Objectif
Créer les nomenclatures (GHM, CIM-10, CCAM, FINESS...) et la logique de génération de données fictives réalistes.

### Ce que tu vas apprendre (concepts Python)

| Concept | Description |
|---|---|
| **Modules Python** | Organisation du code en modules réutilisables |
| **`random`** | Bibliothèque standard pour la génération de nombres aléatoires |
| **`typing`** | Types pour les signatures de fonctions |
| **Dictionnaires constants** | Stockage des nomenclatures comme données statiques Python |

### Livrables

- `app/data/nomenclatures.py` : dictionnaires de codes de référence (GHM, CIM-10, CCAM, FINESS, départements, régions, UM, UCD, LPP)
- `app/generators/mock_data.py` : fonctions de génération de lignes mock
  - `generate_base_row()` → génère `nb_sej`, `duree_moy_sej`, `tx_dc`, `tx_male`, `age_moy`
  - `generate_resume_rows(var, ...)` → génère les lignes pour `/resume` selon la variable de ventilation
  - Logique de ventilation par `var` : pour chaque valeur de `var`, itérer sur les codes de la nomenclature correspondante et générer une ligne par code

### Fichiers à créer

```
app/
├── data/
│   ├── __init__.py
│   └── nomenclatures.py
├── generators/
│   ├── __init__.py
│   └── mock_data.py
```

### Approche pour la génération de données

La spec demande des données fictives mais réalistes. L'approche recommandée :

1. **Valeurs de base réalistes** : définir des plages cohérentes (ex : `age_moy` entre 30 et 85, `tx_dc` entre 0 et 0.1)
2. **Seed fixe optionnel** : permettre de fixer le `random.seed()` pour des résultats déterministes (utile pour les tests)
3. **Cohérence interne** : `nb_pat <= nb_sej`, `tx_male` entre 0 et 1, etc.

### Critère de validation
- `generate_base_row()` retourne un dict avec les 6 colonnes de base, toutes dans des plages réalistes
- Les codes GHM, CIM-10, etc. sont issus des nomenclatures définies dans la spec (§6.3)

---

## Étape 4 — Implémentation complète de `GET /resume`

### Objectif
Implémenter le premier vrai endpoint, le plus complexe (utilisé par 10 fonctions R côté client).

### Ce que tu vas apprendre (concepts FastAPI)

| Concept | Description | Doc officielle |
|---|---|---|
| **`APIRouter`** | Permet de découper les routes en plusieurs fichiers (un par endpoint ou groupe) | [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) |
| **`app.include_router()`** | Enregistre un router dans l'application principale | [Include Router](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-the-apirouter) |
| **`JSONResponse`** | Retourne une réponse JSON avec un code HTTP personnalisé | [Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/) |
| **`Depends()`** (avancé) | Réutilisation de `CommonQueryParams` dans le router | [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) |

### Livrables

- `app/routers/__init__.py`
- `app/routers/resume.py` : endpoint `GET /resume` complet avec :
  - Injection de `CommonQueryParams`
  - Paramètres spécifiques : `bool_nb_pat`, `trancheage`
  - Logique de ventilation par `var` (appel au générateur)
  - Retour JSON conforme à la spec (§3.1)
- Mise à jour de `app/main.py` pour inclure le router
- `tests/test_resume.py` : tests du endpoint

### Fichiers à créer / modifier

```
app/
├── routers/
│   ├── __init__.py
│   └── resume.py
├── main.py              # Modifié pour inclure le router
tests/
├── __init__.py
├── conftest.py          # Fixtures pytest (client HTTP)
└── test_resume.py
```

### Ce que tu vas apprendre (concepts pytest + httpx)

| Concept | Description | Doc officielle |
|---|---|---|
| **`TestClient`** | Client HTTP de test fourni par Starlette (utilisé par FastAPI) | [Testing](https://fastapi.tiangolo.com/tutorial/testing/) |
| **Fixtures pytest** | Fonctions réutilisables qui préparent l'environnement de test | [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) |

### Exemple concret — Test de `/resume`

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_resume_sans_var():
    """Sans paramètre var, /resume retourne une seule ligne agrégée."""
    response = client.get("/resume", params={"annee": "23"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "nb_sej" in data[0]

def test_resume_annee_obligatoire():
    """Sans annee, l'API retourne 400 ou 422."""
    response = client.get("/resume")
    assert response.status_code in (400, 422)
```

### Critère de validation
- `GET /resume?annee=23` retourne 1 ligne JSON avec les colonnes de base
- `GET /resume?annee=23&var=ghm` retourne plusieurs lignes, chacune avec une colonne `ghm`
- `GET /resume?annee=23&var=sexe_trancheage&trancheage=10_20_30` retourne le format pyramide
- Tous les tests passent

---

## Étape 5 — Implémentation des 7 endpoints restants

### Objectif
Compléter l'API avec tous les endpoints de la spec.

### Ce que tu vas apprendre (concepts FastAPI)

| Concept | Description | Doc officielle |
|---|---|---|
| **Factorisation avec les routers** | Organiser le code pour éviter la duplication entre endpoints similaires | [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) |
| **Tags** | Grouper les endpoints dans la doc Swagger avec `tags=["nom"]` | [Path Operation Config](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/#tags) |

### Livrables

Un router par endpoint :

| Fichier | Endpoint | Spécificité |
|---|---|---|
| `app/routers/resume_prec_annee.py` | `GET /resume_prec_annee` | Colonne `annee` 4 chiffres, multi-année |
| `app/routers/diag_assoc.py` | `GET /diag_assoc` | Colonne `code_diag`, possible colonne `dr` |
| `app/routers/um.py` | `GET /um` | Colonnes `code_rum`, `duree_moy_rum` |
| `app/routers/dmi_med.py` | `GET /dmi_med` | Colonnes `datasource`, `code_ucd`/`code_lpp`, hiérarchies ATC/LPP |
| `app/routers/actes.py` | `GET /actes` | Colonnes `code_ccam`, `extension_pmsi`, `acte_activ`, `is_classant` |
| `app/routers/tx_recours.py` | `GET /tx_recours` | Param `type_geo_tx_recours`, colonnes taux standardisés |
| `app/routers/dernier_trans.py` | `GET /dernier_trans` | Pas de `var`, données administratives, exempt du petit_effectif |

Un fichier de test par endpoint dans `tests/`.

### Fichiers à créer

```
app/routers/
├── resume_prec_annee.py
├── diag_assoc.py
├── um.py
├── dmi_med.py
├── actes.py
├── tx_recours.py
└── dernier_trans.py
tests/
├── test_resume_prec_annee.py
├── test_diag_assoc.py
├── test_um.py
├── test_dmi_med.py
├── test_actes.py
├── test_tx_recours.py
└── test_dernier_trans.py
```

### Ordre de développement suggéré

1. **`/dernier_trans`** — le plus simple (pas de `var`, pas de petit_effectif)
2. **`/tx_recours`** — simple aussi (pas de `var`, structure fixe)
3. **`/resume_prec_annee`** — similaire à `/resume` mais multi-année
4. **`/diag_assoc`** — colonnes spécifiques (`code_diag`, `dr`)
5. **`/um`** — colonne spécifique (`code_rum`, `duree_moy_rum`)
6. **`/actes`** — colonnes spécifiques CCAM
7. **`/dmi_med`** — le plus complexe (structure med/dmi, hiérarchies ATC/LPP)

### Critère de validation
- Chaque endpoint retourne des données conformes aux exemples JSON de la spec
- Tous les tests passent
- La doc Swagger à `/docs` affiche les 8 endpoints

---

## Étape 6 — Gestion des erreurs et protection du secret statistique

### Objectif
Implémenter les codes d'erreur HTTP et la logique `petit_effectif`.

### Ce que tu vas apprendre (concepts FastAPI)

| Concept | Description | Doc officielle |
|---|---|---|
| **`HTTPException`** | Lève une exception HTTP avec un code et un message | [Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/) |
| **Exception handlers** | Personnalise le format des réponses d'erreur | [Custom Exception Handlers](https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers) |
| **`JSONResponse`** | Retourne un JSON avec un code HTTP spécifique (pour 404 avec body custom) | [Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/) |

### Livrables

- Gestion du code 400 : si `annee` manquant ou invalide
- Gestion du code 404 : si le périmètre de filtrage ne matche aucun séjour (simulé aléatoirement ou via un paramètre spécial)
- Logique `petit_effectif` (spec §5.2) :
  - Méthode A (`/resume` avec `bool_nb_pat=TRUE`) : `nb_pat` = `"petit_effectif"` si < 10 séjours
  - Méthode B (autres endpoints) : retourne un dataframe tout-string si petit effectif
- Tests spécifiques pour chaque cas d'erreur

### Critère de validation
- `GET /resume` sans `annee` → code 400
- Le cas `petit_effectif` retourne le format attendu par le client R
- Les tests couvrent tous les codes d'erreur de la spec (200, 400, 404)

---

## Étape 7 — Docker, configuration et finalisation

### Objectif
Rendre le projet prêt à l'emploi pour les 3 contextes d'usage (dev local, tests CI, démos).

### Ce que tu vas apprendre

| Concept | Description |
|---|---|
| **Dockerfile multi-stage** | Image optimisée pour la production |
| **Docker Compose** | Orchestration locale avec un seul fichier |
| **Variables d'environnement** | Configuration via `.env` et `os.environ` |
| **CORS** | Cross-Origin Resource Sharing — nécessaire si l'app R fait des appels depuis un navigateur |

### Livrables

- `Dockerfile` : image Python optimisée
- `docker-compose.yml` : configuration pour lancer le mock en une commande
- `.env.example` : variables d'environnement documentées (port, seed, etc.)
- Configuration CORS dans `app/main.py` (si nécessaire)
- `README.md` à la racine : guide de démarrage rapide

### Ce que tu vas apprendre (concepts FastAPI)

| Concept | Description | Doc officielle |
|---|---|---|
| **`CORSMiddleware`** | Middleware pour autoriser les requêtes cross-origin | [CORS](https://fastapi.tiangolo.com/tutorial/cors/) |
| **Lifespan events** | Code exécuté au démarrage/arrêt de l'application | [Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) |
| **Settings avec Pydantic** | Gestion de la configuration via `pydantic-settings` | [Settings](https://fastapi.tiangolo.com/advanced/settings/) |

### Fichiers à créer

```
Dockerfile
docker-compose.yml
.env.example
.dockerignore
README.md
```

### Critère de validation
- `docker compose up` lance le serveur et `/docs` est accessible
- Les tests passent dans le conteneur Docker
- Le README permet à un nouveau développeur de démarrer en 5 minutes

---

## Récapitulatif des concepts FastAPI par étape

| Étape | Concepts clés |
|---|---|
| 1 | `FastAPI()`, `@app.get()`, `uvicorn`, retour JSON auto |
| 2 | `Query()`, `BaseModel`, `Optional`, `response_model`, `Depends()` |
| 3 | *(Python pur : modules, random, typing)* |
| 4 | `APIRouter`, `include_router()`, `JSONResponse`, `TestClient`, fixtures pytest |
| 5 | Tags, factorisation des routers |
| 6 | `HTTPException`, exception handlers, `JSONResponse` avec code custom |
| 7 | `CORSMiddleware`, lifespan events, `pydantic-settings`, Docker |

## Estimation de la structure finale

```
apimco2/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── docs/
│   ├── MOCK_API_SPEC.md
│   ├── ADR-001-choix-fastapi.md
│   └── PLAN_DEVELOPPEMENT.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── params.py
│   │   └── responses.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── nomenclatures.py
│   ├── generators/
│   │   ├── __init__.py
│   │   └── mock_data.py
│   └── routers/
│       ├── __init__.py
│       ├── resume.py
│       ├── resume_prec_annee.py
│       ├── diag_assoc.py
│       ├── um.py
│       ├── dmi_med.py
│       ├── actes.py
│       ├── tx_recours.py
│       └── dernier_trans.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_resume.py
    ├── test_resume_prec_annee.py
    ├── test_diag_assoc.py
    ├── test_um.py
    ├── test_dmi_med.py
    ├── test_actes.py
    ├── test_tx_recours.py
    └── test_dernier_trans.py
```
