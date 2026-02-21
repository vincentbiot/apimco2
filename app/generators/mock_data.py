# =============================================================================
# app/generators/mock_data.py — Génération de données mock réalistes
#
# Ce module fournit les fonctions de génération de lignes fictives pour
# tous les endpoints de l'API Mock MCO.
#
# Concepts Python utilisés :
#
#   1. random.Random (instance, pas le module global)
#      On instancie random.Random(seed) au lieu d'utiliser random.randint()
#      directement, pour que chaque appel puisse avoir son propre seed
#      sans affecter le générateur global de Python.
#      Doc : https://docs.python.org/3/library/random.html#random.Random
#
#   2. itertools.product
#      Calcule le produit cartésien de plusieurs listes.
#      Exemple : product(["M","C"], [1,2,3]) →
#                (("M",1), ("M",2), ("M",3), ("C",1), ("C",2), ("C",3))
#      Utilisé pour générer toutes les combinaisons de valeurs de var.
#      Doc : https://docs.python.org/3/library/itertools.html#itertools.product
#
#   3. typing.Any
#      Utilisé dans les annotations de type quand la valeur peut être
#      de n'importe quel type (int, str, float, tuple...).
#
# Architecture :
#
#   parse_trancheage()       → labels de tranches d'âge à partir des bornes
#   parse_var()              → liste de tokens depuis la chaîne var
#   get_var_values()         → valeurs disponibles pour un token de var
#   _get_var_columns()       → noms de colonnes produits par un token de var
#   generate_base_row()      → dict avec les 5 statistiques de base
#   generate_resume_rows()   → liste de lignes pour GET /resume
#
# Seed et déterminisme :
#   Toutes les fonctions acceptent un paramètre seed optionnel.
#   seed=None → résultats aléatoires à chaque appel (comportement par défaut)
#   seed=42   → résultats toujours identiques (utile pour les tests)
# =============================================================================

import random
from itertools import product
from typing import Any

from app.data.nomenclatures import (
    COMPOUND_VAR_NAMES,
    VAR_VALUES,
)


# =============================================================================
# FONCTIONS UTILITAIRES — Parsing du paramètre var
# =============================================================================


def parse_trancheage(trancheage_param: str | None) -> list[str]:
    """
    Génère les labels de tranches d'âge à partir du paramètre trancheage.

    Le paramètre trancheage est une chaîne de bornes séparées par '_'.
    Exemple : '10_20_30_40_50_60_70_80_90'

    La fonction produit des labels du type '[0-10 ans]', '[11-20 ans]', ...
    La dernière tranche est toujours '[N+1 ans et +]'.

    Args:
        trancheage_param: bornes de coupure séparées par '_',
                          ex : '10_20_30'. Si None, utilise les bornes standard.

    Returns:
        Liste de labels de tranches d'âge.

    Exemples :
        parse_trancheage("10_20_30") → ["[0-10 ans]", "[11-20 ans]",
                                         "[21-30 ans]", "[31 ans et +]"]
        parse_trancheage(None)       → 10 tranches avec bornes standard
    """
    if not trancheage_param:
        # Bornes par défaut correspondant à la pyramide des âges standard MCO
        bornes = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    else:
        bornes = [int(b) for b in trancheage_param.split("_")]

    labels = []
    prev = 0
    for borne in bornes:
        if prev == 0:
            labels.append(f"[0-{borne} ans]")
        else:
            labels.append(f"[{prev + 1}-{borne} ans]")
        prev = borne
    # Dernière tranche : au-delà de la dernière borne
    labels.append(f"[{prev + 1} ans et +]")
    return labels


def parse_var(var_string: str | None) -> list[str]:
    """
    Parse la chaîne var en liste ordonnée de tokens de ventilation.

    Le paramètre var est construit par le client R en joignant les noms
    de variables par '_'. Certains noms composés ('sexe_trancheage',
    'modentprov_modsordest') contiennent eux-mêmes un '_' et doivent être
    reconnus comme des tokens unitaires avant tout découpage.

    L'algorithme est "greedy" : il essaie de faire correspondre les noms
    composés en priorité (par ordre de longueur décroissante), puis les
    noms simples.

    Args:
        var_string: chaîne de variables, ex : 'ghm', 'sexe_trancheage_ghm'.
                    None ou chaîne vide retourne une liste vide.

    Returns:
        Liste de tokens de var, dans l'ordre d'apparition.

    Exemples :
        parse_var(None)                    → []
        parse_var("ghm")                   → ["ghm"]
        parse_var("ghm_mois")              → ["ghm", "mois"]
        parse_var("sexe_trancheage")       → ["sexe_trancheage"]
        parse_var("sexe_trancheage_ghm")   → ["sexe_trancheage", "ghm"]
        parse_var("modentprov_modsordest") → ["modentprov_modsordest"]
    """
    if not var_string:
        return []

    tokens: list[str] = []
    remaining = var_string

    # Trier les vars composés par longueur décroissante pour éviter les
    # faux-positifs : on essaie d'abord le plus long nom composé.
    compound_sorted = sorted(COMPOUND_VAR_NAMES, key=len, reverse=True)

    while remaining:
        matched = False

        # Essayer chaque var composé en premier
        for compound in compound_sorted:
            # Le var composé correspond si :
            #   - il est exactement égal à `remaining` (dernier token)
            #   - OU il est suivi d'un '_' (d'autres tokens suivent)
            if remaining == compound or remaining.startswith(compound + "_"):
                tokens.append(compound)
                remaining = remaining[len(compound):]
                # Consommer le '_' séparateur s'il reste du texte
                if remaining.startswith("_"):
                    remaining = remaining[1:]
                matched = True
                break

        if not matched:
            # Pas de var composé trouvé : prendre le token jusqu'au prochain '_'
            parts = remaining.split("_", 1)
            tokens.append(parts[0])
            remaining = parts[1] if len(parts) > 1 else ""

    return tokens


# =============================================================================
# FONCTIONS UTILITAIRES — Valeurs et colonnes par token de var
# =============================================================================


def get_var_values(
    var_token: str,
    trancheage_param: str | None = None,
) -> list[Any]:
    """
    Retourne la liste des valeurs possibles pour un token de ventilation.

    Pour les vars composés (sexe_trancheage, modentprov_modsordest),
    retourne une liste de tuples (produit cartésien des composantes).

    Args:
        var_token: nom du token, ex : 'ghm', 'sexe_trancheage'.
        trancheage_param: paramètre trancheage transmis par le client R
                          (bornes séparées par '_').

    Returns:
        Liste de valeurs scalaires (str, int) pour les vars simples,
        ou liste de tuples pour les vars composés.
    """
    # --- Var composé : sexe × trancheage (pyramide des âges) ---
    if var_token == "sexe_trancheage":
        sexe_values = VAR_VALUES["sexe"]
        trancheage_values = parse_trancheage(trancheage_param)
        # product() génère toutes les paires (sexe, tranche_age)
        return list(product(sexe_values, trancheage_values))

    # --- Var composé : mode_entrée × mode_sortie (parcours) ---
    if var_token == "modentprov_modsordest":
        modentprov_values = VAR_VALUES["modentprov"]
        modsordest_values = VAR_VALUES["modsordest"]
        return list(product(modentprov_values, modsordest_values))

    # --- Var trancheage seul (sans sexe) ---
    if var_token == "trancheage":
        return parse_trancheage(trancheage_param)

    # --- Var simple : récupérer depuis le dictionnaire VAR_VALUES ---
    if var_token in VAR_VALUES:
        return VAR_VALUES[var_token]

    # Var inconnu : générer des valeurs génériques pour ne pas bloquer
    # (robustesse face à un paramètre var non répertorié)
    return [f"{var_token}_val1", f"{var_token}_val2", f"{var_token}_val3"]


def _get_var_columns(var_token: str) -> list[str]:
    """
    Retourne les noms de colonnes qu'ajoute un token de ventilation.

    Les vars composés ajoutent plusieurs colonnes ; les vars simples en
    ajoutent une seule (portant le même nom que le token).

    Args:
        var_token: nom du token de var.

    Returns:
        Liste de noms de colonnes JSON.

    Exemples :
        _get_var_columns("ghm")                   → ["ghm"]
        _get_var_columns("sexe_trancheage")        → ["sexe", "trancheage"]
        _get_var_columns("modentprov_modsordest")  → ["modentprov", "modsordest"]
    """
    if var_token == "sexe_trancheage":
        return ["sexe", "trancheage"]
    if var_token == "modentprov_modsordest":
        return ["modentprov", "modsordest"]
    # Var simple : une seule colonne, même nom que le token
    return [var_token]


# =============================================================================
# GÉNÉRATION DES DONNÉES DE BASE
# =============================================================================


def generate_base_row(rng: random.Random) -> dict[str, Any]:
    """
    Génère les statistiques de base d'une ligne mock MCO.

    Retourne un dictionnaire avec les 5 colonnes statistiques communes
    à la plupart des endpoints. Les valeurs sont dans des plages réalistes
    pour des données d'activité hospitalière MCO :

      - nb_sej          : 100 à 30 000 séjours
      - duree_moy_sej   : 1.0 à 15.0 jours (médiane MCO réelle ≈ 5 jours)
      - tx_dc           : 0.0 à 0.10 (taux de décès MCO réel ≈ 2%)
      - tx_male         : 0.30 à 0.70 (distribution par sexe)
      - age_moy         : 30.0 à 85.0 ans (population MCO adulte surtout)

    Args:
        rng: instance de random.Random, permet le contrôle du seed.
             Exemple : rng = random.Random(42) pour résultats déterministes.

    Returns:
        Dictionnaire avec les 5 colonnes de base.

    Note:
        nb_pat (nombre de patients) n'est PAS inclus ici. Il est généré
        séparément selon le contexte (bool_nb_pat, présence de var).
        Règle de cohérence : nb_pat <= nb_sej (un patient peut avoir
        plusieurs séjours, mais pas l'inverse).
    """
    return {
        "nb_sej": rng.randint(100, 30_000),
        "duree_moy_sej": round(rng.uniform(1.0, 15.0), 2),
        "tx_dc": round(rng.uniform(0.0, 0.10), 4),
        "tx_male": round(rng.uniform(0.30, 0.70), 4),
        "age_moy": round(rng.uniform(30.0, 85.0), 1),
    }


def _generate_nb_pat(rng: random.Random, nb_sej: int) -> int:
    """
    Génère un nombre de patients cohérent avec le nombre de séjours.

    nb_pat <= nb_sej : un patient peut avoir plusieurs séjours dans l'année.
    En pratique, le ratio nb_pat/nb_sej est entre 0.7 et 1.0.
    """
    return rng.randint(int(nb_sej * 0.70), nb_sej)


# =============================================================================
# GÉNÉRATION DES LIGNES DE RÉPONSE — GET /resume
# =============================================================================


def generate_resume_rows(
    var: str | None = None,
    trancheage_param: str | None = None,
    bool_nb_pat: bool = False,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Génère les lignes de réponse pour l'endpoint GET /resume.

    Logique de ventilation (spec §3.1 et §4) :

      - Sans var      → 1 seule ligne agrégée (résumé de périmètre)
      - Avec var=ghm  → 1 ligne par code GHM
      - Avec var=mois → 1 ligne par mois (1 à 12)
      - Avec var=sexe_trancheage → 1 ligne par (sexe, tranche_âge)
      - Avec var=ghm_typhosp → produit cartésien GHM × typhosp

    Le paramètre var est parsé en tokens avec parse_var(), puis pour chaque
    token on récupère les valeurs avec get_var_values(). Le produit cartésien
    de tous les tokens donne les combinaisons finales.

    Cas spécial var=duree :
      La réponse ne contient que {"duree": N, "nb_sej": X} (distribution
      de la DMS), sans les autres colonnes statistiques (spec §3.1).

    Args:
        var: paramètre var de la requête, ex : 'ghm', 'sexe_trancheage_ghm'.
        trancheage_param: bornes de coupure pour les tranches d'âge,
                          ex : '10_20_30_40_50_60_70_80_90'.
        bool_nb_pat: si True, inclut nb_pat même sans var (résumé périmètre).
        seed: seed aléatoire pour des résultats déterministes (utile en tests).

    Returns:
        Liste de dicts JSON. Chaque dict est une ligne de la réponse.

    Exemples de sortie :
        generate_resume_rows()
        → [{"nb_sej": 12345, "duree_moy_sej": 5.4, "tx_dc": 0.02, ...}]

        generate_resume_rows(var="ghm")
        → [{"ghm": "05M09T", "nb_sej": 2345, "nb_pat": 1987, ...}, ...]

        generate_resume_rows(var="duree")
        → [{"duree": 0, "nb_sej": 25432}, {"duree": 1, "nb_sej": 18765}, ...]
    """
    # Initialiser le générateur aléatoire (reproductible si seed fourni)
    rng = random.Random(seed)

    # Découper le paramètre var en tokens
    var_tokens = parse_var(var)

    # -------------------------------------------------------------------------
    # CAS 1 — Sans var : une seule ligne agrégée
    # -------------------------------------------------------------------------
    if not var_tokens:
        row = generate_base_row(rng)
        if bool_nb_pat:
            # nb_pat demandé explicitement (résumé de périmètre)
            row["nb_pat"] = _generate_nb_pat(rng, row["nb_sej"])
        return [row]

    # -------------------------------------------------------------------------
    # CAS 2 — CAS SPÉCIAL var=duree seul : distribution DMS
    # La réponse n'a que duree + nb_sej, pas les autres colonnes (spec §3.1)
    # -------------------------------------------------------------------------
    if var_tokens == ["duree"]:
        duree_values = get_var_values("duree")
        rows = []
        nb_sej_total = rng.randint(50_000, 150_000)
        for duree_val in duree_values:
            # Distribution décroissante : plus de séjours courts que longs
            nb_sej = int(nb_sej_total / (duree_val + 1.5) * rng.uniform(0.8, 1.2))
            nb_sej = max(100, nb_sej)
            rows.append({"duree": duree_val, "nb_sej": nb_sej})
        return rows

    # -------------------------------------------------------------------------
    # CAS 3 — Avec var : produit cartésien des valeurs de chaque token
    # -------------------------------------------------------------------------

    # Pour chaque token, récupérer la liste de valeurs et les colonnes associées
    all_var_values: list[list[Any]] = []
    all_var_columns: list[list[str]] = []

    for token in var_tokens:
        values = get_var_values(token, trancheage_param)
        columns = _get_var_columns(token)
        all_var_values.append(values)
        all_var_columns.append(columns)

    # Calculer le produit cartésien de toutes les valeurs
    # Exemple : product(["M","C"], [1,2]) → [("M",1), ("M",2), ("C",1), ("C",2)]
    rows: list[dict[str, Any]] = []

    for combo in product(*all_var_values):
        # combo est un tuple : une valeur (ou tuple de valeurs) par token
        # Exemple avec var="ghm_typhosp" : combo = ("05M09T", "M")
        # Exemple avec var="sexe_trancheage" : combo = (("1", "[0-10 ans]"),)

        # Construire les colonnes de ventilation pour cette combinaison
        var_cols: dict[str, Any] = {}
        for i, (token_cols, token_val) in enumerate(
            zip(all_var_columns, combo)
        ):
            if len(token_cols) > 1:
                # Var composé : token_val est un tuple de valeurs
                # Exemple : token_cols=["sexe","trancheage"], token_val=("1","[0-10 ans]")
                for col, val in zip(token_cols, token_val):
                    var_cols[col] = val
            else:
                # Var simple : token_val est un scalaire
                var_cols[token_cols[0]] = token_val

        # Générer les statistiques de base pour cette ligne
        stats = generate_base_row(rng)
        nb_pat = _generate_nb_pat(rng, stats["nb_sej"])

        # Avec var, nb_pat est toujours inclus dans la réponse (spec §3.1)
        # Colonnes var en premier (convention spec), puis statistiques
        row: dict[str, Any] = {
            **var_cols,
            "nb_sej": stats["nb_sej"],
            "nb_pat": nb_pat,
            "duree_moy_sej": stats["duree_moy_sej"],
            "tx_dc": stats["tx_dc"],
            "tx_male": stats["tx_male"],
            "age_moy": stats["age_moy"],
        }
        rows.append(row)

    # Limiter le nombre de lignes pour les produits cartésiens très larges
    # (ex : finess × dp × mois = 7 × 12 × 12 = 1008 lignes → trop)
    max_rows = 100
    if len(rows) > max_rows:
        # Mélanger avant de couper pour garder une diversité représentative
        rng.shuffle(rows)
        rows = rows[:max_rows]

    return rows
