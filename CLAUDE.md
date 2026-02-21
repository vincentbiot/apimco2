# CLAUDE.md — Contexte projet API Mock Activité MCO

## Profil développeur

- **Langage maîtrisé** : Python (niveau intermédiaire/avancé)
- **Framework API** : FastAPI — **débutant**. L'utilisateur souhaite monter en compétence progressivement sur ce framework
- **Objectif pédagogique** : Chaque étape de développement doit être accompagnée d'explications sur les concepts FastAPI utilisés, avec des commentaires dans le code et des références à la documentation officielle

## Conventions de développement

- **Langue du code** : anglais (noms de variables, fonctions, classes)
- **Langue de la documentation** : français
- **Langue des commentaires dans le code** : français
- **Langue des messages de commit** : anglais

## Stack technique retenue

- **Framework** : FastAPI (Python)
- **Serveur ASGI** : Uvicorn
- **Validation** : Pydantic v2
- **Conteneurisation** : Docker
- **Tests** : pytest + httpx (client async pour tester FastAPI)
- **Linting** : ruff

## Structure du projet

```
apimco2/
├── CLAUDE.md
├── docs/
│   ├── MOCK_API_SPEC.md          # Spécification fonctionnelle (existant)
│   ├── ADR-001-choix-fastapi.md  # Architecture Decision Record
│   └── PLAN_DEVELOPPEMENT.md     # Plan de développement détaillé
├── app/
│   ├── main.py                   # Point d'entrée FastAPI
│   ├── routers/                  # Endpoints organisés par module
│   ├── models/                   # Modèles Pydantic (requêtes/réponses)
│   ├── data/                     # Nomenclatures et données de référence
│   └── generators/               # Logique de génération de données mock
├── tests/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Commandes utiles

```bash
# Installation des dépendances
pip install -r requirements.txt

# Lancer le serveur de développement (rechargement automatique)
uvicorn app.main:app --reload --port 8000

# Lancer les tests
pytest

# Linting
ruff check .

# Docker
docker compose up --build
```

## Principes pour l'assistant

- Expliquer chaque concept FastAPI nouveau (decorateurs, injection de dépendances, Query params, Pydantic models, etc.)
- Privilégier la clarté du code à la concision
- Ajouter des commentaires pédagogiques dans le code source
- Référencer la doc officielle FastAPI quand pertinent (https://fastapi.tiangolo.com/)
- Procéder par étapes progressives, du plus simple au plus complexe
