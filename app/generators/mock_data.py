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
    ATC_DATA,
    CCAM,
    CIM10,
    CODEGEO,
    COMPOUND_VAR_NAMES,
    DEPARTEMENTS,
    FINESS,
    HIERA_LPP,
    LPP,
    REGIONS,
    TERRITOIRES_SANTE,
    TYPE_UM,
    UCD,
    VAR_VALUES,
    ZONES_ARS,
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


# =============================================================================
# GÉNÉRATION DES LIGNES DE RÉPONSE — GET /dernier_trans
# =============================================================================


def generate_dernier_trans_rows(
    annee_param: str,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Génère les lignes de réponse pour l'endpoint GET /dernier_trans.

    Retourne une ligne par établissement FINESS avec la date de dernière
    transmission PMSI. Cet endpoint est exempt du contrôle petit_effectif
    (données administratives, spec §3.8).

    La convention secteur/catégorie suit les données réelles :
      - Établissements publics (CHU, CH) : secteur "PU", categ "CH"
      - Cliniques privées : secteur "PR", categ "CL"

    Args:
        annee_param: année sur 2 chiffres (ex : "23" pour 2023).
        seed: seed aléatoire pour résultats déterministes.

    Returns:
        Liste de dicts, une entrée par établissement FINESS.
    """
    rng = random.Random(seed)

    # Conversion 2 chiffres → 4 chiffres
    # Convention : on suppose que les années sont toutes dans le 21e siècle
    annee_4ch = 2000 + int(annee_param)

    # Établissements publics dans notre nomenclature FINESS (codes connus)
    # Les codes 130, 750, 690, 330, 310 sont des hôpitaux publics (CHU/CH)
    # Les codes 440, 060 sont des cliniques privées
    finess_publics = {"130783293", "750100018", "690023154", "330781196", "310781406"}

    rows = []
    for finess_code, rs in FINESS.items():
        # Déterminer le secteur et la catégorie selon le code FINESS
        if finess_code in finess_publics:
            secteur = "PU"
            categ = "CH"
        else:
            secteur = "PR"
            categ = "CL"

        # Générer une date de transmission réaliste dans l'année n+1
        # (les transmissions de l'année N se font début de l'année N+1)
        mois = rng.randint(1, 3)          # Janvier à Mars
        jour = rng.randint(1, 28)         # Jours valides pour tous les mois
        date_trans = f"{annee_4ch + 1}-{mois:02d}-{jour:02d}"

        rows.append({
            "annee": annee_4ch,
            "finess": finess_code,
            "rs": rs,
            "secteur": secteur,
            "categ": categ,
            "derniere_transmission": date_trans,
        })

    return rows


# =============================================================================
# GÉNÉRATION DES LIGNES DE RÉPONSE — GET /tx_recours
# =============================================================================


def generate_tx_recours_rows(
    type_geo: str = "dep",
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Génère les lignes de réponse pour l'endpoint GET /tx_recours.

    Retourne les taux de recours géographiques (séjours et patients pour
    1000 habitants) par zone géographique. Le niveau de granularité est
    contrôlé par le paramètre type_geo_tx_recours (spec §3.7).

    Logique de calcul des taux :
      tx_brut_sej = nb_sej / nb_pop * 1000
      tx_standard est légèrement ajusté (±5%) pour simuler la standardisation
      sur l'âge et le sexe appliquée en pratique.

    Args:
        type_geo: niveau géographique — "dep", "reg", "zon", "ts" ou "geo".
                  Détermine quelle nomenclature est utilisée pour les codes.
        seed: seed aléatoire pour résultats déterministes.

    Returns:
        Liste de dicts, une entrée par zone géographique.
    """
    rng = random.Random(seed)

    # Mapper le type géographique vers la nomenclature correspondante
    # Chaque entrée est soit un dict (code → libellé) soit une list (codes)
    geo_nomenclatures: dict[str, list[str]] = {
        "dep": list(DEPARTEMENTS.keys()),
        "reg": list(REGIONS.keys()),
        "zon": list(ZONES_ARS),
        "ts": list(TERRITOIRES_SANTE),
        "geo": list(CODEGEO),
    }

    # Utiliser "dep" par défaut si le type est inconnu
    codes = geo_nomenclatures.get(type_geo, geo_nomenclatures["dep"])

    rows = []
    for code in codes:
        # Population de la zone : entre 100 000 et 5 000 000 habitants
        nb_pop = rng.randint(100_000, 5_000_000)
        # Nombre de séjours et patients cohérents avec la population
        # Taux brut réaliste : 60 à 120 séjours pour 1000 habitants
        tx_brut_sej = rng.uniform(60.0, 120.0)
        tx_brut_pat = tx_brut_sej * rng.uniform(0.80, 0.95)  # patients < séjours

        nb_sej = int(nb_pop * tx_brut_sej / 1000)
        nb_pat = int(nb_pop * tx_brut_pat / 1000)

        # Taux standardisés : ajustement ±5% autour du taux brut
        facteur_std = rng.uniform(0.95, 1.05)
        tx_std_sej = round(tx_brut_sej * facteur_std, 2)
        tx_std_pat = round(tx_brut_pat * facteur_std, 2)

        rows.append({
            "typ_geo": type_geo,
            "code": code,
            "nb_sej": nb_sej,
            "nb_pat": nb_pat,
            "nb_pop": nb_pop,
            "tx_recours_brut_sej": round(tx_brut_sej, 2),
            "tx_recours_brut_pat": round(tx_brut_pat, 2),
            "tx_recours_standard_sej": tx_std_sej,
            "tx_recours_standard_pat": tx_std_pat,
        })

    return rows


# =============================================================================
# GÉNÉRATION DES LIGNES DE RÉPONSE — GET /resume_prec_annee
# =============================================================================


def generate_resume_prec_annee_rows(
    var: str | None = None,
    annee_param: str = "23",
    trancheage_param: str | None = None,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Génère les lignes de réponse pour l'endpoint GET /resume_prec_annee.

    Similaire à generate_resume_rows() mais avec deux différences majeures :
      1. L'année (4 chiffres) est toujours présente comme dimension de groupement.
         On génère 5 années consécutives (annee-4 à annee).
      2. nb_pat est toujours inclus dans la réponse (quel que soit var).

    Sans var : 1 ligne par année (5 lignes au total).
    Avec var  : produit cartésien années × var_values.

    Args:
        var: paramètre de ventilation, ex : 'ghm', 'sexe_trancheage'.
        annee_param: année de référence sur 2 chiffres (ex : '23' pour 2023).
        trancheage_param: bornes de tranches d'âge pour var=sexe_trancheage.
        seed: seed aléatoire pour résultats déterministes.

    Returns:
        Liste de dicts. Chaque dict contient 'annee' + statistiques de base.
    """
    rng = random.Random(seed)

    # Générer 5 années consécutives se terminant à annee_param
    annee_int = 2000 + int(annee_param)
    annees = list(range(annee_int - 4, annee_int + 1))  # ex : [2019, 2020, ..., 2023]

    var_tokens = parse_var(var)

    # -------------------------------------------------------------------------
    # CAS 1 — Sans var : 1 ligne par année
    # -------------------------------------------------------------------------
    if not var_tokens:
        rows = []
        for annee in annees:
            stats = generate_base_row(rng)
            nb_pat = _generate_nb_pat(rng, stats["nb_sej"])
            row: dict[str, Any] = {
                "annee": annee,
                "nb_sej": stats["nb_sej"],
                "nb_pat": nb_pat,
                "duree_moy_sej": stats["duree_moy_sej"],
                "tx_dc": stats["tx_dc"],
                "tx_male": stats["tx_male"],
                "age_moy": stats["age_moy"],
            }
            rows.append(row)
        return rows

    # -------------------------------------------------------------------------
    # CAS 2 — Avec var : produit cartésien années × valeurs de var
    # L'année est traitée comme une première dimension de ventilation.
    # -------------------------------------------------------------------------

    # Construire les listes de valeurs et de colonnes pour chaque token
    all_var_values: list[list[Any]] = [annees]       # l'année est la 1ère dimension
    all_var_columns: list[list[str]] = [["annee"]]

    for token in var_tokens:
        values = get_var_values(token, trancheage_param)
        columns = _get_var_columns(token)
        all_var_values.append(values)
        all_var_columns.append(columns)

    rows = []
    for combo in product(*all_var_values):
        # combo[0] = l'année, combo[1:] = les valeurs des tokens var

        # Construire les colonnes de ventilation
        var_cols: dict[str, Any] = {"annee": combo[0]}
        for token_cols, token_val in zip(all_var_columns[1:], combo[1:]):
            if len(token_cols) > 1:
                # Var composé : token_val est un tuple
                for col, val in zip(token_cols, token_val):
                    var_cols[col] = val
            else:
                var_cols[token_cols[0]] = token_val

        stats = generate_base_row(rng)
        nb_pat = _generate_nb_pat(rng, stats["nb_sej"])

        row = {
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
    max_rows = 100
    if len(rows) > max_rows:
        rng.shuffle(rows)
        rows = rows[:max_rows]

    return rows


# =============================================================================
# GÉNÉRATION DES LIGNES DE RÉPONSE — GET /diag_assoc
# =============================================================================


def generate_diag_assoc_rows(
    var: str | None = None,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Génère les lignes de réponse pour l'endpoint GET /diag_assoc.

    Retourne les diagnostics associés significatifs (DAS). L'identifiant
    primaire est code_diag (code CIM-10), toujours présent dans chaque ligne.

    Sans var : 1 ligne par code CIM-10 → statistiques de base (sans nb_pat).
    Avec var  : produit cartésien code_diag × var_values.

    Note sur "dr" dans var :
        Le paramètre dr (diagnostic relié) se comporte comme n'importe quelle
        variable de ventilation : chaque valeur de dr génère une ligne
        distincte dans le produit cartésien.

    Args:
        var: paramètre de ventilation (ex : 'finess', 'dr', 'ghm').
        seed: seed aléatoire pour résultats déterministes.

    Returns:
        Liste de dicts. Chaque dict contient 'code_diag' + statistiques.
    """
    rng = random.Random(seed)

    # L'identifiant primaire est toujours code_diag (codes CIM-10 de la nomenclature)
    diag_codes = list(CIM10.keys())
    var_tokens = parse_var(var)

    # -------------------------------------------------------------------------
    # CAS 1 — Sans var : 1 ligne par code CIM-10
    # -------------------------------------------------------------------------
    if not var_tokens:
        rows = []
        for code in diag_codes:
            stats = generate_base_row(rng)
            row: dict[str, Any] = {
                "code_diag": code,
                "nb_sej": stats["nb_sej"],
                "duree_moy_sej": stats["duree_moy_sej"],
                "tx_dc": stats["tx_dc"],
                "tx_male": stats["tx_male"],
                "age_moy": stats["age_moy"],
            }
            rows.append(row)
        return rows

    # -------------------------------------------------------------------------
    # CAS 2 — Avec var : produit cartésien code_diag × var_values
    # -------------------------------------------------------------------------
    all_var_values: list[list[Any]] = [diag_codes]
    all_var_columns: list[list[str]] = [["code_diag"]]

    for token in var_tokens:
        values = get_var_values(token)
        columns = _get_var_columns(token)
        all_var_values.append(values)
        all_var_columns.append(columns)

    rows = []
    for combo in product(*all_var_values):
        var_cols: dict[str, Any] = {"code_diag": combo[0]}
        for token_cols, token_val in zip(all_var_columns[1:], combo[1:]):
            if len(token_cols) > 1:
                for col, val in zip(token_cols, token_val):
                    var_cols[col] = val
            else:
                var_cols[token_cols[0]] = token_val

        stats = generate_base_row(rng)
        row = {
            **var_cols,
            "nb_sej": stats["nb_sej"],
            "duree_moy_sej": stats["duree_moy_sej"],
            "tx_dc": stats["tx_dc"],
            "tx_male": stats["tx_male"],
            "age_moy": stats["age_moy"],
        }
        rows.append(row)

    max_rows = 100
    if len(rows) > max_rows:
        rng.shuffle(rows)
        rows = rows[:max_rows]

    return rows


# =============================================================================
# GÉNÉRATION DES LIGNES DE RÉPONSE — GET /um
# =============================================================================


def generate_um_rows(
    var: str | None = None,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Génère les lignes de réponse pour l'endpoint GET /um.

    Retourne les données par type d'unité médicale (UM/RUM). L'identifiant
    primaire est code_rum, toujours présent dans chaque ligne.

    Spécificité de cet endpoint : présence de duree_moy_rum (durée au niveau
    RUM, c'est-à-dire par sous-séjour dans une unité médicale), distincte de
    duree_moy_sej (durée du séjour complet).

    Sans var : 1 ligne par type d'UM → statistiques de base + duree_moy_rum.
    Avec var  : produit cartésien code_rum × var_values.

    Args:
        var: paramètre de ventilation (ex : 'finess', 'ghm').
        seed: seed aléatoire pour résultats déterministes.

    Returns:
        Liste de dicts. Chaque dict contient 'code_rum', 'duree_moy_rum' + stats.
    """
    rng = random.Random(seed)

    # L'identifiant primaire est code_rum (types d'UM de la nomenclature)
    um_codes = list(TYPE_UM.keys())
    var_tokens = parse_var(var)

    # -------------------------------------------------------------------------
    # CAS 1 — Sans var : 1 ligne par type d'UM
    # -------------------------------------------------------------------------
    if not var_tokens:
        rows = []
        for code in um_codes:
            stats = generate_base_row(rng)
            # duree_moy_rum est toujours < duree_moy_sej (le RUM est un sous-séjour)
            duree_moy_rum = round(stats["duree_moy_sej"] * rng.uniform(0.5, 0.95), 2)
            row: dict[str, Any] = {
                "code_rum": code,
                "nb_sej": stats["nb_sej"],
                "duree_moy_sej": stats["duree_moy_sej"],
                "duree_moy_rum": duree_moy_rum,
                "tx_dc": stats["tx_dc"],
                "tx_male": stats["tx_male"],
                "age_moy": stats["age_moy"],
            }
            rows.append(row)
        return rows

    # -------------------------------------------------------------------------
    # CAS 2 — Avec var : produit cartésien code_rum × var_values
    # -------------------------------------------------------------------------
    all_var_values: list[list[Any]] = [um_codes]
    all_var_columns: list[list[str]] = [["code_rum"]]

    for token in var_tokens:
        values = get_var_values(token)
        columns = _get_var_columns(token)
        all_var_values.append(values)
        all_var_columns.append(columns)

    rows = []
    for combo in product(*all_var_values):
        var_cols: dict[str, Any] = {"code_rum": combo[0]}
        for token_cols, token_val in zip(all_var_columns[1:], combo[1:]):
            if len(token_cols) > 1:
                for col, val in zip(token_cols, token_val):
                    var_cols[col] = val
            else:
                var_cols[token_cols[0]] = token_val

        stats = generate_base_row(rng)
        duree_moy_rum = round(stats["duree_moy_sej"] * rng.uniform(0.5, 0.95), 2)
        row = {
            **var_cols,
            "nb_sej": stats["nb_sej"],
            "duree_moy_sej": stats["duree_moy_sej"],
            "duree_moy_rum": duree_moy_rum,
            "tx_dc": stats["tx_dc"],
            "tx_male": stats["tx_male"],
            "age_moy": stats["age_moy"],
        }
        rows.append(row)

    max_rows = 100
    if len(rows) > max_rows:
        rng.shuffle(rows)
        rows = rows[:max_rows]

    return rows


# =============================================================================
# GÉNÉRATION DES LIGNES DE RÉPONSE — GET /actes
# =============================================================================


def generate_actes_rows(
    var: str | None = None,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Génère les lignes de réponse pour l'endpoint GET /actes.

    Retourne les actes classants CCAM des séjours. L'identifiant primaire
    est code_ccam, toujours présent dans chaque ligne.

    Différences par rapport aux autres endpoints :
      - Pas de tx_dc ni de nb_pat (schéma spécifique /actes, spec §3.6)
      - Colonnes spécifiques : nb_acte, extension_pmsi, acte_activ, is_classant

    Sans var : 1 ligne par code CCAM.
    Avec var  : produit cartésien code_ccam × var_values.

    Args:
        var: paramètre de ventilation (ex : 'finess', 'dr').
        seed: seed aléatoire pour résultats déterministes.

    Returns:
        Liste de dicts. Chaque dict contient les colonnes spécifiques CCAM.
    """
    rng = random.Random(seed)

    # L'identifiant primaire est code_ccam (codes de la nomenclature CCAM)
    ccam_codes = list(CCAM.keys())
    var_tokens = parse_var(var)

    # -------------------------------------------------------------------------
    # CAS 1 — Sans var : 1 ligne par code CCAM
    # -------------------------------------------------------------------------
    if not var_tokens:
        rows = []
        for code in ccam_codes:
            nb_acte = rng.randint(500, 10_000)
            # nb_sej <= nb_acte (un séjour peut avoir plusieurs actes du même code)
            nb_sej = rng.randint(int(nb_acte * 0.8), nb_acte)
            row: dict[str, Any] = {
                "code_ccam": code,
                "extension_pmsi": rng.choice(["0", "1"]),
                "nb_acte": nb_acte,
                "nb_sej": nb_sej,
                "duree_moy_sej": round(rng.uniform(1.0, 15.0), 2),
                "tx_male": round(rng.uniform(0.30, 0.70), 4),
                "age_moy": round(rng.uniform(30.0, 85.0), 1),
                "acte_activ": rng.choice(["1", "2", "3", "4", "5"]),
                "is_classant": rng.choice([0, 1]),
            }
            rows.append(row)
        return rows

    # -------------------------------------------------------------------------
    # CAS 2 — Avec var : produit cartésien code_ccam × var_values
    # -------------------------------------------------------------------------
    all_var_values: list[list[Any]] = [ccam_codes]
    all_var_columns: list[list[str]] = [["code_ccam"]]

    for token in var_tokens:
        values = get_var_values(token)
        columns = _get_var_columns(token)
        all_var_values.append(values)
        all_var_columns.append(columns)

    rows = []
    for combo in product(*all_var_values):
        var_cols: dict[str, Any] = {"code_ccam": combo[0]}
        for token_cols, token_val in zip(all_var_columns[1:], combo[1:]):
            if len(token_cols) > 1:
                for col, val in zip(token_cols, token_val):
                    var_cols[col] = val
            else:
                var_cols[token_cols[0]] = token_val

        nb_acte = rng.randint(500, 10_000)
        nb_sej = rng.randint(int(nb_acte * 0.8), nb_acte)
        row = {
            **var_cols,
            "extension_pmsi": rng.choice(["0", "1"]),
            "nb_acte": nb_acte,
            "nb_sej": nb_sej,
            "duree_moy_sej": round(rng.uniform(1.0, 15.0), 2),
            "tx_male": round(rng.uniform(0.30, 0.70), 4),
            "age_moy": round(rng.uniform(30.0, 85.0), 1),
            "acte_activ": rng.choice(["1", "2", "3", "4", "5"]),
            "is_classant": rng.choice([0, 1]),
        }
        rows.append(row)

    max_rows = 100
    if len(rows) > max_rows:
        rng.shuffle(rows)
        rows = rows[:max_rows]

    return rows


# =============================================================================
# GÉNÉRATION DES LIGNES DE RÉPONSE — GET /dmi_med
# =============================================================================


def generate_dmi_med_rows(
    var: str | None = None,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Génère les lignes de réponse pour l'endpoint GET /dmi_med.

    Retourne un mélange de lignes médicaments (UCD) et DMI (LPP). La colonne
    'datasource' distingue les deux types. Cette structure asymétrique est
    spécifique à cet endpoint (spec §3.5) :

      - Ligne "med" : code_ucd, lib_ucd, atc1..atc5 renseignés ;
                      code_lpp, hiera, hiera_libelle à None.
      - Ligne "dmi" : code_lpp, hiera, hiera_libelle renseignés ;
                      code_ucd, lib_ucd, atc1..atc5 à None.

    Sans var : une ligne par UCD + une ligne par LPP.
    Avec var  : produit cartésien (UCD + LPP codes) × var_values.

    Args:
        var: paramètre de ventilation (ex : 'finess', 'ghm').
        seed: seed aléatoire pour résultats déterministes.

    Returns:
        Liste de dicts avec structure med ou dmi selon le datasource.
    """
    rng = random.Random(seed)

    var_tokens = parse_var(var)

    def _make_med_row(code_ucd: str, extra_cols: dict[str, Any]) -> dict[str, Any]:
        """Crée une ligne médicament (datasource='med')."""
        atc = ATC_DATA.get(code_ucd, {})
        nb = rng.randint(1_000, 10_000)
        nb_sej = rng.randint(int(nb * 0.3), nb)
        nb_pat = rng.randint(int(nb_sej * 0.70), nb_sej)
        return {
            **extra_cols,
            "datasource": "med",
            "code": code_ucd,
            "code_ucd": code_ucd,
            "lib_ucd": UCD.get(code_ucd),
            "atc1": atc.get("atc1"),
            "atc2": atc.get("atc2"),
            "atc3": atc.get("atc3"),
            "atc4": atc.get("atc4"),
            "atc5": atc.get("atc5"),
            "nb": nb,
            "nb_sej": nb_sej,
            "nb_pat": nb_pat,
            "mnt_remb": round(rng.uniform(10_000, 2_000_000), 2),
            "duree_moy_sej": round(rng.uniform(1.0, 10.0), 2),
            "age_moy": round(rng.uniform(40.0, 80.0), 1),
            "code_lpp": None,
            "hiera": None,
            "hiera_libelle": None,
        }

    def _make_dmi_row(code_lpp: str, extra_cols: dict[str, Any]) -> dict[str, Any]:
        """Crée une ligne DMI (datasource='dmi')."""
        # Associer une hiérarchie LPP au code (correspondance simplifiée pour le mock)
        hiera_codes = list(HIERA_LPP.keys())
        hiera = hiera_codes[list(LPP.keys()).index(code_lpp) % len(hiera_codes)]
        nb = rng.randint(100, 2_000)
        nb_sej = nb  # Pour les DMI, nb_sej ≈ nb (1 DMI par séjour en général)
        nb_pat = rng.randint(int(nb_sej * 0.70), nb_sej)
        return {
            **extra_cols,
            "datasource": "dmi",
            "code": code_lpp,
            "code_ucd": None,
            "lib_ucd": None,
            "atc1": None,
            "atc2": None,
            "atc3": None,
            "atc4": None,
            "atc5": None,
            "nb": nb,
            "nb_sej": nb_sej,
            "nb_pat": nb_pat,
            "mnt_remb": round(rng.uniform(5_000, 500_000), 2),
            "duree_moy_sej": round(rng.uniform(2.0, 12.0), 2),
            "age_moy": round(rng.uniform(50.0, 80.0), 1),
            "code_lpp": code_lpp,
            "hiera": hiera,
            "hiera_libelle": HIERA_LPP.get(hiera),
        }

    ucd_codes = list(UCD.keys())
    lpp_codes = list(LPP.keys())

    # -------------------------------------------------------------------------
    # CAS 1 — Sans var : 1 ligne par UCD + 1 ligne par LPP
    # -------------------------------------------------------------------------
    if not var_tokens:
        rows = []
        for code in ucd_codes:
            rows.append(_make_med_row(code, {}))
        for code in lpp_codes:
            rows.append(_make_dmi_row(code, {}))
        return rows

    # -------------------------------------------------------------------------
    # CAS 2 — Avec var : produit cartésien (UCD + LPP) × var_values
    # On génère séparément les lignes med et dmi, puis on les concatène.
    # -------------------------------------------------------------------------
    all_var_values: list[list[Any]] = []
    all_var_columns: list[list[str]] = []

    for token in var_tokens:
        values = get_var_values(token)
        columns = _get_var_columns(token)
        all_var_values.append(values)
        all_var_columns.append(columns)

    rows = []

    # Générer les lignes médicaments
    for ucd_code in ucd_codes:
        for combo in product(*all_var_values):
            extra_cols: dict[str, Any] = {}
            for token_cols, token_val in zip(all_var_columns, combo):
                if len(token_cols) > 1:
                    for col, val in zip(token_cols, token_val):
                        extra_cols[col] = val
                else:
                    extra_cols[token_cols[0]] = token_val
            rows.append(_make_med_row(ucd_code, extra_cols))

    # Générer les lignes DMI
    for lpp_code in lpp_codes:
        for combo in product(*all_var_values):
            extra_cols = {}
            for token_cols, token_val in zip(all_var_columns, combo):
                if len(token_cols) > 1:
                    for col, val in zip(token_cols, token_val):
                        extra_cols[col] = val
                else:
                    extra_cols[token_cols[0]] = token_val
            rows.append(_make_dmi_row(lpp_code, extra_cols))

    max_rows = 100
    if len(rows) > max_rows:
        rng.shuffle(rows)
        rows = rows[:max_rows]

    return rows


# =============================================================================
# SECRET STATISTIQUE — Méthode B (étape 6)
# =============================================================================


def build_petit_effectif_row_b(identifier_col: str, identifier_val: str) -> list[dict]:
    """
    Génère la réponse "petit effectif" pour les endpoints soumis à la Méthode B
    du secret statistique (spec §5.2).

    Quand un périmètre concerne moins de 10 séjours, l'API ne peut pas retourner
    de statistiques (secret statistique PMSI). Pour les endpoints autres que
    /resume, la convention est de retourner un tableau contenant UNE SEULE LIGNE
    avec uniquement des colonnes de type chaîne de caractères (aucune colonne
    numérique).

    Le client R détecte ce cas via :
        all(sapply(config_data, function(col) !any(is.numeric(col))))
    Si toutes les colonnes sont non-numériques → petit effectif détecté.

    Args:
        identifier_col: nom de la colonne identifiant de l'endpoint
                        (ex : "code_ccam" pour /actes, "code_diag" pour /diag_assoc)
        identifier_val: valeur string représentative pour cette colonne

    Returns:
        Liste avec une seule ligne tout-string, ex : [{"code_ccam": "DZQM006"}]

    Exemples d'appel par endpoint :
        /resume_prec_annee  → build_petit_effectif_row_b("annee", "2023")
        /diag_assoc         → build_petit_effectif_row_b("code_diag", "I10")
        /um                 → build_petit_effectif_row_b("code_rum", "01")
        /actes              → build_petit_effectif_row_b("code_ccam", "DZQM006")
        /dmi_med            → build_petit_effectif_row_b("datasource", "med")
    """
    # Une seule ligne, une seule colonne string.
    # Aucune valeur numérique → le client R détecte le petit effectif.
    return [{identifier_col: identifier_val}]
