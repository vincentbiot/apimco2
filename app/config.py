# =============================================================================
# app/config.py — Configuration centralisée avec pydantic-settings
#
# Concept FastAPI (étape 7) : Settings avec pydantic-settings
#
#   pydantic-settings est une extension de Pydantic qui permet de lire la
#   configuration depuis les variables d'environnement (ou un fichier .env).
#   C'est l'approche recommandée par FastAPI pour gérer la configuration.
#
#   Fonctionnement :
#     1. On définit une classe Settings héritant de BaseSettings.
#     2. Chaque attribut correspond à une variable d'environnement du même nom
#        (en majuscules par convention). Exemple : `port` → variable PORT.
#     3. pydantic-settings lit automatiquement l'environnement et valide
#        les valeurs avec Pydantic (types, valeurs par défaut, etc.).
#     4. Si un fichier .env est présent à la racine, il est lu automatiquement.
#
#   Doc FastAPI : https://fastapi.tiangolo.com/advanced/settings/
#   Doc pydantic-settings : https://docs.pydantic.dev/latest/concepts/pydantic_settings/
#
# Utilisation :
#   from app.config import settings
#   print(settings.port)   # → 8000 (ou la valeur de la variable PORT)
#
# =============================================================================

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration de l'application lue depuis les variables d'environnement.

    Chaque champ peut être surchargé par une variable d'environnement du même
    nom en majuscules. Exemple : PORT=9000 uvicorn app.main:app --reload

    Si un fichier .env est présent à la racine du projet, il est lu
    automatiquement (voir model_config ci-dessous).
    """

    # -------------------------------------------------------------------------
    # Paramètres du serveur
    # -------------------------------------------------------------------------

    # Port d'écoute du serveur. Variable d'environnement : PORT
    port: int = Field(default=8000, description="Port d'écoute du serveur Uvicorn")

    # Environnement d'exécution. Variable d'environnement : ENVIRONMENT
    # Valeurs attendues : "development", "production", "test"
    environment: str = Field(
        default="development",
        description="Environnement d'exécution (development, production, test)",
    )

    # -------------------------------------------------------------------------
    # Paramètres de la génération de données mock
    # -------------------------------------------------------------------------

    # Seed optionnel pour le générateur aléatoire.
    # Variable d'environnement : RANDOM_SEED
    # Laisser vide (None) pour des données différentes à chaque appel.
    # Fixer à un entier (ex: 42) pour des données toujours identiques.
    # Utile pour les démos et les tests d'intégration.
    random_seed: int | None = Field(
        default=None,
        description="Seed du générateur aléatoire (None = aléatoire, entier = déterministe)",
    )

    # -------------------------------------------------------------------------
    # Paramètres CORS
    # -------------------------------------------------------------------------

    # Origines autorisées pour les requêtes cross-origin.
    # Variable d'environnement : CORS_ORIGINS
    # Exemples :
    #   CORS_ORIGINS=*                          → tout autoriser (développement)
    #   CORS_ORIGINS=http://localhost:3000      → une seule origine
    #   CORS_ORIGINS=http://localhost,http://myapp.com → plusieurs origines (séparées par des virgules)
    cors_origins: str = Field(
        default="*",
        description="Origines CORS autorisées (séparées par des virgules, ou '*' pour tout autoriser)",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """
        Transforme la chaîne CORS_ORIGINS en liste Python.

        Exemples :
          "*"                                  → ["*"]
          "http://localhost,http://myapp.com"  → ["http://localhost", "http://myapp.com"]
        """
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # -------------------------------------------------------------------------
    # Configuration pydantic-settings
    # -------------------------------------------------------------------------

    # model_config contrôle comment pydantic-settings lit la configuration.
    # env_file : chemin du fichier .env (relatif au répertoire de travail)
    # env_file_encoding : encodage du fichier .env
    # case_sensitive : False → PORT et port sont équivalents
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# =============================================================================
# Instance globale de la configuration.
#
# On crée une seule instance de Settings au démarrage du module.
# Elle est importée partout dans l'application :
#   from app.config import settings
#
# pydantic-settings lit les variables d'environnement UNE FOIS à l'instanciation.
# Les modifications d'environnement après le démarrage ne sont pas prises en compte.
# =============================================================================
settings = Settings()
