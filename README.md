# API Mock Activité MCO

API de simulation des données d'activité MCO (Médecine, Chirurgie, Obstétrique), construite avec FastAPI. Permet de développer et tester des clients R sans connexion à la base PMSI réelle.

---

## Démarrage rapide

### Prérequis

- Python 3.12+ **ou** Docker + Docker Compose

---

### Option A — Python local (développement)

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd apimco2

# 2. Créer et activer un environnement virtuel
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. (Optionnel) Copier et personnaliser la configuration
cp .env.example .env

# 5. Lancer le serveur avec rechargement automatique
uvicorn app.main:app --reload --port 8000
```

L'API est accessible à `http://localhost:8000`.
La documentation interactive Swagger est disponible à `http://localhost:8000/docs`.

---

### Option B — Docker Compose (recommandé pour les démos)

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd apimco2

# 2. (Optionnel) Personnaliser la configuration
cp .env.example .env
# Éditer .env selon vos besoins (port, seed, CORS...)

# 3. Construire l'image et démarrer le conteneur
docker compose up --build

# Pour lancer en arrière-plan :
docker compose up --build -d
```

L'API est accessible à `http://localhost:8000`.

Pour arrêter :
```bash
docker compose down
```

---

## Endpoints disponibles

| Endpoint | Description |
|---|---|
| `GET /` | Health check — vérifie que le serveur est opérationnel |
| `GET /resume` | Résumé de l'activité MCO (endpoint principal) |
| `GET /resume_prec_annee` | Résumé multi-année (évolution dans le temps) |
| `GET /diag_assoc` | Diagnostics associés (CIM-10) |
| `GET /um` | Activité par Unité Médicale |
| `GET /dmi_med` | Dispositifs médicaux implantables et médicaments onéreux |
| `GET /actes` | Actes CCAM |
| `GET /tx_recours` | Taux de recours standardisés |
| `GET /dernier_trans` | Dernier transfert administratif |

**Documentation complète** : `http://localhost:8000/docs` (Swagger UI)

---

## Paramètre commun à tous les endpoints

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `annee` | string | Oui | Année sur 2 chiffres (ex : `23` pour 2023) |
| `var` | string | Non | Variable(s) de ventilation séparées par `_` (ex : `ghm`, `sexe_trancheage`) |
| `moissortie` | string | Non | Plage de mois `debut_fin` (ex : `1_6` pour jan-juin) |
| `sexe` | string | Non | `1` (homme) ou `2` (femme) |
| `age` | string | Non | Plage d'âge `min_max` (ex : `20_60`) |

Voir la documentation Swagger pour la liste complète des paramètres.

---

## Configuration

L'application se configure via des variables d'environnement (ou un fichier `.env`).

| Variable | Défaut | Description |
|---|---|---|
| `PORT` | `8000` | Port d'écoute du serveur |
| `ENVIRONMENT` | `development` | Environnement (`development`, `production`, `test`) |
| `RANDOM_SEED` | *(vide)* | Seed aléatoire pour des données déterministes (ex : `42`) |
| `CORS_ORIGINS` | `*` | Origines CORS autorisées (séparées par des virgules) |

Exemple de fichier `.env` :

```dotenv
PORT=8000
ENVIRONMENT=development
RANDOM_SEED=42
CORS_ORIGINS=http://localhost:3838
```

---

## Commandes utiles

```bash
# Lancer les tests
pytest

# Lancer les tests avec verbosité
pytest -v

# Linter
ruff check .

# Lancer dans Docker (tests)
docker compose run api pytest

# Voir les logs du conteneur
docker compose logs -f

# Ouvrir un shell dans le conteneur
docker compose exec api bash
```

---

## Structure du projet

```
apimco2/
├── app/
│   ├── config.py          # Configuration via pydantic-settings
│   ├── main.py            # Application FastAPI (CORS, lifespan, routers)
│   ├── data/
│   │   └── nomenclatures.py   # Codes de référence (GHM, CIM-10, CCAM...)
│   ├── generators/
│   │   └── mock_data.py       # Génération de données fictives réalistes
│   ├── models/
│   │   ├── params.py          # Paramètres de requête communs
│   │   └── responses.py       # Modèles de réponse Pydantic
│   └── routers/               # Un fichier par endpoint
├── tests/                     # Tests pytest
├── docs/
│   ├── MOCK_API_SPEC.md       # Spécification fonctionnelle complète
│   ├── ADR-001-choix-fastapi.md
│   └── PLAN_DEVELOPPEMENT.md
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

---

## Codes d'erreur

| Code HTTP | Signification |
|---|---|
| `200` | Succès — données retournées |
| `400` | Paramètre manquant ou invalide (ex : `annee` absent) |
| `404` | Aucun séjour trouvé pour le périmètre demandé |

---

## Références

- [FastAPI](https://fastapi.tiangolo.com/) — Framework web
- [Pydantic](https://docs.pydantic.dev/) — Validation des données
- [Uvicorn](https://www.uvicorn.org/) — Serveur ASGI
- [Spécification fonctionnelle](docs/MOCK_API_SPEC.md) — Description complète de l'API
