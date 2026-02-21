# ADR-001 — Choix de FastAPI comme framework pour l'API Mock

**Date** : 2026-02-21
**Statut** : Accepté
**Décideur** : Équipe projet

---

## Contexte

Nous devons implémenter une API mock pour l'application Activité MCO. Cette API simule un backend de données hospitalières (PMSI) et sera utilisée pour :

- Le développement local de l'application R (sans accès à la base de données réelle)
- Les tests automatisés avec des données déterministes
- Les démonstrations sans données réelles (secret statistique)

L'API comprend **8 endpoints** REST qui retournent du JSON, avec ~25 paramètres de query string communs et 29 variables de ventilation possibles.

## Décision

Nous choisissons **Python + FastAPI** comme stack technique.

## Options envisagées

### Option 1 — Python + FastAPI (retenue)

FastAPI est un framework web Python moderne, conçu pour construire des APIs REST. Il s'appuie sur les type hints Python et Pydantic pour la validation automatique des paramètres.

**Avantages** :
- Validation automatique des paramètres de requête via les type hints Python et Pydantic
- Documentation interactive Swagger UI / ReDoc générée automatiquement — utile pour les démos
- Performances élevées (asynchrone, basé sur Starlette)
- Écosystème Python riche pour la génération de données (random, Faker, numpy)
- Courbe d'apprentissage douce pour un développeur Python
- La logique métier (petit_effectif, ventilations par `var`) s'exprime naturellement

**Inconvénients** :
- Image Docker plus lourde qu'un binaire Go (~150 MB vs ~15 MB)
- Nécessite un runtime Python sur la machine cible

### Option 2 — Node.js + Express

**Avantages** : Léger, JSON natif, écosystème large (faker-js).
**Inconvénients** : Moins de validation native, pas de doc OpenAPI auto sans plugin, nécessite de connaître JavaScript/TypeScript.

### Option 3 — Prism (mock spec-first)

**Avantages** : Zéro code, génération automatique depuis un fichier OpenAPI.
**Inconvénients** : Très limité pour la logique dynamique (filtrage par paramètres, petit_effectif, ventilation par `var` avec 29 valeurs). Ne couvre pas nos besoins fonctionnels.

### Option 4 — Go (Gin / net/http)

**Avantages** : Binaire unique ~15 MB, performance excellente, pas de dépendance runtime.
**Inconvénients** : Plus verbeux, peu d'outillage pour la génération de données mock, courbe d'apprentissage plus raide.

## Justification détaillée

### 1. Adéquation avec la complexité du paramétrage

L'API a ~25 paramètres de query string, tous optionnels sauf `annee`. FastAPI permet de déclarer ces paramètres directement dans la signature de la fonction avec des valeurs par défaut :

```python
# Exemple : déclaration des paramètres dans FastAPI
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/resume")
async def get_resume(
    annee: str,                                    # Obligatoire
    var: str | None = None,                        # Optionnel
    moissortie: str | None = None,                 # Optionnel
    sexe: str | None = Query(None, regex="^[12]$") # Optionnel avec validation
):
    ...
```

Ce style déclaratif est plus lisible et maintenable que de parser manuellement les query strings.

### 2. Documentation automatique pour les démos

FastAPI génère automatiquement une interface Swagger UI accessible à `/docs`. Cela permet :
- De tester les endpoints directement depuis le navigateur
- De documenter l'API sans effort supplémentaire
- De faciliter les démos auprès des parties prenantes

### 3. Cohérence avec le profil développeur

Le développeur principal connaît Python mais pas FastAPI. La courbe d'apprentissage est douce car FastAPI s'appuie sur des concepts Python standard (type hints, décorateurs, fonctions async). C'est aussi l'occasion de monter en compétence sur un framework très demandé.

### 4. Stratégie de déploiement

| Environnement | Méthode |
|---|---|
| Développement local | `uvicorn app.main:app --reload` |
| Tests CI | Docker ou `pip install + pytest` |
| Démonstrations | Docker Compose ou PaaS (Render, Railway) |

## Conséquences

- Le développeur devra apprendre FastAPI (documentation officielle + commentaires pédagogiques dans le code)
- Un `Dockerfile` sera créé pour faciliter le déploiement
- Les tests utiliseront `pytest` + `httpx` (client HTTP recommandé par FastAPI pour les tests)
- La validation des paramètres sera assurée par Pydantic v2

## Références

- [FastAPI — Documentation officielle](https://fastapi.tiangolo.com/)
- [Pydantic v2 — Documentation](https://docs.pydantic.dev/latest/)
- [Uvicorn — Serveur ASGI](https://www.uvicorn.org/)
- [Spécification Mock API MCO](./MOCK_API_SPEC.md)
