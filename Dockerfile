# =============================================================================
# Dockerfile — Image Docker pour l'API Mock Activité MCO
#
# Concept : Build multi-stage
#
#   Un Dockerfile multi-stage utilise plusieurs instructions FROM.
#   Chaque FROM démarre un nouveau "stage" de construction.
#
#   Avantages :
#     - L'image finale ne contient que le strict nécessaire (pas les outils de build)
#     - Image plus petite → moins de surface d'attaque, téléchargement plus rapide
#     - Les couches intermédiaires ne sont pas incluses dans l'image finale
#
#   Notre stratégie :
#     Stage 1 (builder) : installe les dépendances dans un venv isolé
#     Stage 2 (runtime) : copie uniquement le venv et le code source
#
# Construction : docker build -t apimco2 .
# Exécution    : docker run -p 8000:8000 apimco2
# =============================================================================


# =============================================================================
# Stage 1 : builder
#
#   Ce stage installe toutes les dépendances Python dans un virtualenv.
#   L'image python:3.12-slim est une image Debian minimale avec Python 3.12.
#   Le suffixe "-slim" signifie qu'elle ne contient pas les compilateurs C
#   ni les headers, mais uniquement le runtime Python.
# =============================================================================
FROM python:3.12-slim AS builder

# Désactive le cache bytecode .pyc (inutile dans un conteneur Docker)
# et passe Python en mode non-bufferisé (les logs s'affichent en temps réel)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Copier uniquement requirements.txt d'abord.
# Docker met en cache chaque instruction RUN/COPY séparément.
# Si requirements.txt ne change pas, Docker réutilise la couche du cache
# et ne réinstalle pas les dépendances (gain de temps considérable).
COPY requirements.txt .

# Créer un virtualenv et y installer les dépendances.
# On utilise un venv plutôt que l'environnement global pour pouvoir le copier
# proprement dans le stage suivant avec COPY --from=builder.
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip --quiet && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# =============================================================================
# Stage 2 : runtime
#
#   Ce stage constitue l'image finale. Il repart d'une image propre
#   et copie uniquement ce qui est nécessaire depuis le stage builder.
# =============================================================================
FROM python:3.12-slim AS runtime

# Même variables que le stage builder pour la cohérence
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Ajouter le venv au PATH : toutes les commandes python/uvicorn/etc.
# utiliseront automatiquement les packages installés dans /opt/venv.
ENV PATH="/opt/venv/bin:$PATH"

# Créer un utilisateur non-root pour exécuter l'application.
# Bonne pratique de sécurité : ne jamais exécuter un service en root
# dans un conteneur Docker.
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copier le virtualenv depuis le stage builder
COPY --from=builder /opt/venv /opt/venv

# Copier le code source de l'application
# On ne copie QUE le répertoire app/ (pas les tests, docs, .env, etc.)
COPY app/ ./app/

# Changer le propriétaire des fichiers pour l'utilisateur appuser
RUN chown -R appuser:appgroup /app

# Passer à l'utilisateur non-root
USER appuser

# Documenter le port exposé (informatif, ne publie pas le port)
EXPOSE 8000

# Commande de démarrage de l'application.
# On utilise uvicorn directement (sans --reload en production).
# --host 0.0.0.0 : écoute sur toutes les interfaces réseau du conteneur
#                  (nécessaire pour que le port soit accessible depuis l'hôte)
# --port 8000    : port d'écoute (doit correspondre à EXPOSE ci-dessus)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
