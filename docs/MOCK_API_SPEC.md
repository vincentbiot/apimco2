# Spécifications Fonctionnelles — API Mock Activité MCO

**Version** : 1.0
**Date** : 2026-02-20
**Statut** : Spécification pour implémentation

---

## Table des matières

1. [Introduction](#1-introduction)
2. [Paramètres de requête communs](#2-paramètres-de-requête-communs)
3. [Catalogue des 8 endpoints](#3-catalogue-des-8-endpoints)
4. [Variations de réponse selon le paramètre `var`](#4-variations-de-réponse-selon-le-paramètre-var)
5. [Gestion des erreurs et cas limites](#5-gestion-des-erreurs-et-cas-limites)
6. [Données de référence nécessaires](#6-données-de-référence-nécessaires)
7. [Annexe — var_list complète](#7-annexe--var_list-complète)

---

## 1. Introduction

### 1.1 Objectif

Cette spécification décrit l'API mock destinée à simuler le backend de l'application Activité MCO lors du développement local, des tests automatisés et des démonstrations. L'API mock fournit des données fictives réalistes au format exact attendu par l'application.

### 1.2 Contexte d'utilisation

| Contexte | Description |
|---|---|
| Développement local | Développer l'interface sans accès à la base de données |
| Tests automatisés | Vérifier le comportement des modules avec des données déterministes |
| Démonstrations | Présenter l'application sans données réelles (secret statistique) |

---

## 2. Paramètres de requête communs

Tous les endpoints reçoivent un ensemble commun de paramètres via la query string HTTP. Ces paramètres sont construits par la fonction `get_query_api(config_selected)` dans `R/fct_query_impala.R`.

### 2.1 Paramètres de filtrage

| Paramètre | Type | Obligatoire | Encodage | Logique de suppression |
|---|---|---|---|---|
| `annee` | character (2 chiffres) | Oui | `substr(year, 3, 4)` — ex. `"2022"` → `"22"` | Toujours envoyé |
| `moissortie` | character | Non | `"debut_fin"` — ex. `"3_9"` | `NULL` si `NULL` ou si `1_12` (plage complète) |
| `sexe` | character | Non | Scalaire : `"1"` (H) ou `"2"` (F) | `NULL` si les 2 sexes sélectionnés |
| `age` | character | Non | `"min_max"` — ex. `"18_65"` | `NULL` si `0_125` (plage complète) |
| `typhosp` | character | Non | Séparateur `_` — ex. `"M_C"` | `NULL` si >= 3 types (tous sélectionnés) |
| `{filtre}` | character | Non | Nom dynamique (`ghm`, `racine`, `cmd`, etc.), valeurs jointes par `_` | `NULL` si vecteur vide |
| `diag` | character | Non | Codes CIM-10 joints par `_` | `NULL` si vide |
| `diag_pos` | character | Non | `"DP"`, `"DR"` ou `"DA"` | `NULL` si vide |
| `acte` | character | Non | Codes CCAM (7 ou 9 car.) joints par `_` — extension `NA` tronquée | `NULL` si vide |
| `exclu_acte` | character | Non | Même encodage que `acte` | `NULL` si vide ou contient `"NA"` |
| `and_acte` | character | Non | `"0"` (OU) ou `"1"` (ET) | Passé directement |
| `and_exclu_acte` | character | Non | `"0"` (OU) ou `"1"` (ET) | Passé directement |
| `um` | character | Non | Codes UM joints par `_` | `NULL` si vide |
| `finess` | character | Non | Codes FINESS PMSI joints par `_` | `NULL` si vide |
| `finessgeo` | character | Non | Codes FINESS géo joints par `_` | `NULL` si vide |
| `categ` | character | Non | Codes catégorie joints par `_` | `NULL` si vide |
| `secteur` | character | Non | Codes secteur joints par `_` | `NULL` si vide |
| `modeentree` | character | Non | Codes mode entrée joints par `_` | `NULL` si vide |
| `modesortie` | character | Non | Codes mode sortie joints par `_` | `NULL` si vide |
| `provenance` | character | Non | Codes provenance joints par `_` | `NULL` si vide |
| `destination` | character | Non | Codes destination joints par `_` | `NULL` si vide |
| `passageurg` | character | Non | Joints par `_` | `NULL` si vide |
| `type_geo_etab` | character | Non | `"reg"`, `"dep"`, etc. | `NULL` si vide |
| `codes_geo_etab` | character | Non | Codes géo joints par `_` | `NULL` si vide |
| `codegeo` | character | Non | Codes géo joints par `_` | `NULL` si vide |
| `type_geo_pat` | character | Non | `"reg"`, `"dep"`, etc. | `NULL` si vide |
| `codes_geo_pat` | character | Non | Codes géo joints par `_` | `NULL` si vide |
| `code_lpp` | character | Non | Codes LPP joints par `_` | `NULL` si vide |
| `code_ucd` | character | Non | Codes UCD joints par `_` | `NULL` si vide |

### 2.2 Paramètres d'authentification

Ces paramètres sont transmis à chaque requête pour l'identification et le traçage :

| Paramètre | Type | Description |
|---|---|---|
| `profils_niveau` | character | Niveau du profil : `"ETABLISSEMENT"`, `"ETABLISSEMENT G"`, `"STRUCTURE_ADMINISTRATIVE"`, `""` (dev) |
| `profils_entite` | character | Code entité : `"ATIH"`, `"DGOS"`, etc. ou `""` (dev) |
| `id_utilisateur` | character | Identifiant Plage de l'utilisateur (`"test"` en dev) |
| `token_utilisateur` | character | Token OAuth2 PASREL (`""` en dev) |
| `refus_cookie` | character | `"TRUE"` si refus cookies, `"FALSE"` sinon |

### 2.3 Règles d'encodage

- **Séparateur de listes** : le caractère `_` sépare les valeurs multiples (ex. `ghm=05M09T_05M10T`)
- **Année 2 chiffres** : seuls les caractères 3-4 de l'année 4 chiffres (ex. `2023` → `23`)
- **Suppression si plage complète** : les paramètres représentant une plage complète sont envoyés à `NULL` (omis de la requête) pour optimiser le traitement côté serveur
- **Codes CCAM** : format `AAAA000` (7 car.) ou `AAAA00000` (9 car. avec extension PMSI) ; extension `NA` → tronqué à 7 car.

### 2.4 Paramètres additionnels par endpoint

Ces paramètres sont ajoutés par les fonctions de récupération de données après `get_query_api()` :

| Paramètre | Endpoint(s) | Valeur | Description |
|---|---|---|---|
| `var` | `resume`, `resume_prec_annee`, `diag_assoc`, `um`, `dmi_med`, `actes` | String de variables jointes par `_` | Dimension(s) de ventilation des résultats |
| `bool_nb_pat` | `resume` (périmètre seul) | `TRUE` | Demande le retour de la colonne `nb_pat` |
| `trancheage` | `resume` (pyramide seul) | `"10_20_30_40_50_60_70_80_90"` | Points de coupure fixes pour la pyramide des âges |
| `type_geo_tx_recours` | `tx_recours` | `"dep"` (défaut), `"reg"`, `"zon"`, `"ts"`, `"geo"` | Niveau géographique du taux de recours |

---

## 3. Catalogue des 8 endpoints

### 3.1 `GET /resume`

**Description** : Endpoint principal et polyvalent. Retourne des agrégats de séjours MCO ventilés selon le paramètre `var`. Utilisé par 10 fonctions R différentes couvrant le résumé de périmètre, la pyramide des âges, l'évolution mensuelle, la répartition FINESS, le casemix GHM, les modes d'entrée/sortie, le DP, la DMS, l'analyse flexible et la cartographie.

**Paramètres spécifiques** : `var`, `bool_nb_pat`, `trancheage` (voir §2.4)

#### Schéma de réponse — Colonnes de base (sans `var`)

| Colonne | Type R | Description |
|---|---|---|
| `nb_sej` | integer | Nombre de séjours |
| `nb_pat` | integer ou `"petit_effectif"` | Nombre de patients — retourné systématiquement quand un `var` est spécifié ; peut contenir la chaîne `"petit_effectif"` si effectif < 10 (quand `bool_nb_pat=TRUE` pour le résumé périmètre) |
| `duree_moy_sej` | numeric | Durée moyenne de séjour en jours (peut être absente) |
| `tx_dc` | numeric | Taux de décès |
| `tx_male` | numeric | Taux masculin |
| `age_moy` | numeric | Âge moyen |

Les colonnes additionnelles dépendent de la valeur de `var` (voir §4).

#### Exemple JSON — Résumé de périmètre (`bool_nb_pat=TRUE`, sans `var`)

```json
[
  {
    "nb_sej": 125432,
    "nb_pat": 98210,
    "duree_moy_sej": 5.43,
    "tx_dc": 0.0187,
    "tx_male": 0.4823,
    "age_moy": 62.7
  }
]
```

#### Exemple JSON — Pyramide des âges (`var=sexe_trancheage`, `trancheage=10_20_30_40_50_60_70_80_90`)

```json
[
  {"sexe": "1", "trancheage": "[0-10 ans]", "nb_sej": 3421, "nb_pat": 2890, "duree_moy_sej": 3.21, "tx_dc": 0.0012, "tx_male": 1.0, "age_moy": 5.2},
  {"sexe": "1", "trancheage": "[11-20 ans]", "nb_sej": 2876, "nb_pat": 2654, "duree_moy_sej": 2.87, "tx_dc": 0.0008, "tx_male": 1.0, "age_moy": 15.8},
  {"sexe": "1", "trancheage": "[21-30 ans]", "nb_sej": 4512, "nb_pat": 3987, "duree_moy_sej": 3.45, "tx_dc": 0.0015, "tx_male": 1.0, "age_moy": 25.3},
  {"sexe": "1", "trancheage": "[31-40 ans]", "nb_sej": 5234, "nb_pat": 4567, "duree_moy_sej": 4.12, "tx_dc": 0.0023, "tx_male": 1.0, "age_moy": 35.6},
  {"sexe": "1", "trancheage": "[41-50 ans]", "nb_sej": 7891, "nb_pat": 6543, "duree_moy_sej": 5.67, "tx_dc": 0.0045, "tx_male": 1.0, "age_moy": 45.8},
  {"sexe": "2", "trancheage": "[0-10 ans]", "nb_sej": 2987, "nb_pat": 2567, "duree_moy_sej": 3.08, "tx_dc": 0.0010, "tx_male": 0.0, "age_moy": 5.4},
  {"sexe": "2", "trancheage": "[11-20 ans]", "nb_sej": 3456, "nb_pat": 3210, "duree_moy_sej": 2.95, "tx_dc": 0.0007, "tx_male": 0.0, "age_moy": 16.1},
  {"sexe": "2", "trancheage": "[21-30 ans]", "nb_sej": 6789, "nb_pat": 5432, "duree_moy_sej": 3.78, "tx_dc": 0.0011, "tx_male": 0.0, "age_moy": 26.7},
  {"sexe": "2", "trancheage": "[31-40 ans]", "nb_sej": 8234, "nb_pat": 6789, "duree_moy_sej": 4.56, "tx_dc": 0.0019, "tx_male": 0.0, "age_moy": 35.2}
]
```

#### Exemple JSON — Évolution mensuelle (`var=mois`)

```json
[
  {"mois": 1, "nb_sej": 10234, "nb_pat": 8765, "duree_moy_sej": 5.67, "tx_dc": 0.0195, "tx_male": 0.4812, "age_moy": 63.1},
  {"mois": 2, "nb_sej": 9876, "nb_pat": 8432, "duree_moy_sej": 5.45, "tx_dc": 0.0188, "tx_male": 0.4798, "age_moy": 62.8},
  {"mois": 3, "nb_sej": 11023, "nb_pat": 9345, "duree_moy_sej": 5.32, "tx_dc": 0.0176, "tx_male": 0.4834, "age_moy": 62.5},
  {"mois": 4, "nb_sej": 10567, "nb_pat": 8987, "duree_moy_sej": 5.41, "tx_dc": 0.0182, "tx_male": 0.4821, "age_moy": 62.9},
  {"mois": 5, "nb_sej": 10890, "nb_pat": 9123, "duree_moy_sej": 5.38, "tx_dc": 0.0179, "tx_male": 0.4845, "age_moy": 62.6},
  {"mois": 6, "nb_sej": 10345, "nb_pat": 8876, "duree_moy_sej": 5.51, "tx_dc": 0.0191, "tx_male": 0.4809, "age_moy": 63.0}
]
```

#### Exemple JSON — Répartition par FINESS (`var=finess`)

```json
[
  {"finess": "130783293", "nb_sej": 15234, "nb_pat": 12345, "duree_moy_sej": 6.12, "tx_dc": 0.0234, "tx_male": 0.4567, "age_moy": 64.3},
  {"finess": "750100018", "nb_sej": 23456, "nb_pat": 18765, "duree_moy_sej": 7.89, "tx_dc": 0.0312, "tx_male": 0.4812, "age_moy": 58.7},
  {"finess": "690023154", "nb_sej": 18765, "nb_pat": 15432, "duree_moy_sej": 5.45, "tx_dc": 0.0198, "tx_male": 0.4923, "age_moy": 61.2},
  {"finess": "330781196", "nb_sej": 12345, "nb_pat": 10234, "duree_moy_sej": 4.87, "tx_dc": 0.0167, "tx_male": 0.5012, "age_moy": 59.8},
  {"finess": "310781406", "nb_sej": 9876, "nb_pat": 8234, "duree_moy_sej": 5.23, "tx_dc": 0.0189, "tx_male": 0.4756, "age_moy": 63.5}
]
```

#### Exemple JSON — Diagnostic principal (`var=dp`)

```json
[
  {"dp": "C34", "nb_sej": 4567, "duree_moy_sej": 8.23, "tx_dc": 0.0456, "tx_male": 0.6234, "age_moy": 67.8},
  {"dp": "I50", "nb_sej": 3876, "duree_moy_sej": 9.45, "tx_dc": 0.0678, "tx_male": 0.5123, "age_moy": 78.2},
  {"dp": "J44", "nb_sej": 3234, "duree_moy_sej": 7.12, "tx_dc": 0.0345, "tx_male": 0.5678, "age_moy": 72.1},
  {"dp": "K80", "nb_sej": 2987, "duree_moy_sej": 4.56, "tx_dc": 0.0023, "tx_male": 0.3456, "age_moy": 58.9},
  {"dp": "S72", "nb_sej": 2654, "duree_moy_sej": 11.34, "tx_dc": 0.0234, "tx_male": 0.3212, "age_moy": 81.4}
]
```

#### Exemple JSON — Durée de séjour (`var=duree`)

```json
[
  {"duree": 0, "nb_sej": 25432},
  {"duree": 1, "nb_sej": 18765},
  {"duree": 2, "nb_sej": 14321},
  {"duree": 3, "nb_sej": 10987},
  {"duree": 4, "nb_sej": 8765},
  {"duree": 5, "nb_sej": 6543},
  {"duree": 6, "nb_sej": 4321},
  {"duree": 7, "nb_sej": 3456},
  {"duree": 10, "nb_sej": 2345},
  {"duree": 15, "nb_sej": 1234}
]
```

#### Exemple JSON — Casemix GHM (`var=ghm`)

```json
[
  {"ghm": "05M09T", "nb_sej": 2345, "duree_moy_sej": 7.89, "tx_dc": 0.0123, "tx_male": 0.5432, "age_moy": 71.2},
  {"ghm": "05K06T", "nb_sej": 1987, "duree_moy_sej": 3.45, "tx_dc": 0.0034, "tx_male": 0.6123, "age_moy": 67.8},
  {"ghm": "01M10T", "nb_sej": 1654, "duree_moy_sej": 5.67, "tx_dc": 0.0234, "tx_male": 0.4876, "age_moy": 74.3},
  {"ghm": "06C04Z", "nb_sej": 1432, "duree_moy_sej": 4.12, "tx_dc": 0.0012, "tx_male": 0.3234, "age_moy": 55.6},
  {"ghm": "08M04T", "nb_sej": 1234, "duree_moy_sej": 6.34, "tx_dc": 0.0187, "tx_male": 0.4567, "age_moy": 68.9}
]
```

#### Exemple JSON — Modes entrée/sortie (`var=modentprov_modsordest`)

```json
[
  {"modentprov": "8_1", "modsordest": "8_4", "nb_sej": 45678, "duree_moy_sej": 5.23, "tx_dc": 0.0012, "tx_male": 0.4823, "age_moy": 58.3},
  {"modentprov": "8_5", "modsordest": "8_4", "nb_sej": 12345, "duree_moy_sej": 7.89, "tx_dc": 0.0345, "tx_male": 0.5123, "age_moy": 72.1},
  {"modentprov": "6_1", "modsordest": "8_4", "nb_sej": 8765, "duree_moy_sej": 9.12, "tx_dc": 0.0456, "tx_male": 0.4987, "age_moy": 76.8},
  {"modentprov": "8_1", "modsordest": "6_1", "nb_sej": 6543, "duree_moy_sej": 12.34, "tx_dc": 0.0678, "tx_male": 0.4654, "age_moy": 79.2},
  {"modentprov": "8_1", "modsordest": "9_9", "nb_sej": 2345, "duree_moy_sej": 15.67, "tx_dc": 1.0000, "tx_male": 0.5234, "age_moy": 82.1}
]
```

#### Règles de gestion spécifiques

1. **Sans `var`** : retourne une seule ligne agrégée.
2. **Avec `bool_nb_pat=TRUE`** : la colonne `nb_pat` est incluse. Peut contenir la chaîne `"petit_effectif"` si effectif < 10.
3. **Renommages automatiques** : si la réponse contient `passage_urg` → renommé `passageurg` ; si `typ_hosp` → renommé `typhosp` (effectué côté client dans `call_api_and_unwrap()`).
4. **`duree_moy_sej`** : peut être absente de la réponse ; le client ajoute une colonne `"0"` via `verif_data()`.

---

### 3.2 `GET /resume_prec_annee`

**Description** : Retourne les agrégats de séjours sur plusieurs années consécutives pour l'analyse d'évolution multi-annuelle. Utilisé par le module multi-year.

**Paramètres spécifiques** : `var` (optionnel, ventilation)

#### Schéma de réponse

| Colonne | Type R | Description |
|---|---|---|
| `annee` | integer | Année (4 chiffres : 2019, 2020, ...) |
| `nb_sej` | integer | Nombre de séjours |
| `nb_pat` | integer | Nombre de patients |
| `duree_moy_sej` | numeric | Durée moyenne de séjour (peut être absente) |
| `tx_dc` | numeric | Taux de décès |
| `tx_male` | numeric | Taux masculin |
| `age_moy` | numeric | Âge moyen |
| Colonne(s) de `var` | character | Variable(s) de ventilation (si `var` fourni) |

#### Exemple JSON — Sans `var`

```json
[
  {"annee": 2019, "nb_sej": 112345, "nb_pat": 89876, "duree_moy_sej": 5.78, "tx_dc": 0.0198, "tx_male": 0.4812, "age_moy": 62.3},
  {"annee": 2020, "nb_sej": 98765, "nb_pat": 78654, "duree_moy_sej": 5.92, "tx_dc": 0.0215, "tx_male": 0.4798, "age_moy": 62.8},
  {"annee": 2021, "nb_sej": 108432, "nb_pat": 86543, "duree_moy_sej": 5.65, "tx_dc": 0.0203, "tx_male": 0.4834, "age_moy": 62.5},
  {"annee": 2022, "nb_sej": 115678, "nb_pat": 92345, "duree_moy_sej": 5.51, "tx_dc": 0.0192, "tx_male": 0.4821, "age_moy": 62.9},
  {"annee": 2023, "nb_sej": 125432, "nb_pat": 98210, "duree_moy_sej": 5.43, "tx_dc": 0.0187, "tx_male": 0.4845, "age_moy": 62.7}
]
```

#### Exemple JSON — Avec `var=ghm`

```json
[
  {"annee": 2021, "ghm": "05M09T", "nb_sej": 2100, "nb_pat": 1890, "duree_moy_sej": 8.12, "tx_dc": 0.0134, "tx_male": 0.5456, "age_moy": 71.0},
  {"annee": 2022, "ghm": "05M09T", "nb_sej": 2234, "nb_pat": 1987, "duree_moy_sej": 7.98, "tx_dc": 0.0128, "tx_male": 0.5412, "age_moy": 71.3},
  {"annee": 2023, "ghm": "05M09T", "nb_sej": 2345, "nb_pat": 2098, "duree_moy_sej": 7.89, "tx_dc": 0.0123, "tx_male": 0.5432, "age_moy": 71.2},
  {"annee": 2021, "ghm": "05K06T", "nb_sej": 1800, "nb_pat": 1650, "duree_moy_sej": 3.67, "tx_dc": 0.0038, "tx_male": 0.6089, "age_moy": 67.2},
  {"annee": 2022, "ghm": "05K06T", "nb_sej": 1890, "nb_pat": 1723, "duree_moy_sej": 3.56, "tx_dc": 0.0036, "tx_male": 0.6112, "age_moy": 67.5},
  {"annee": 2023, "ghm": "05K06T", "nb_sej": 1987, "nb_pat": 1812, "duree_moy_sej": 3.45, "tx_dc": 0.0034, "tx_male": 0.6123, "age_moy": 67.8}
]
```

#### Règles de gestion spécifiques

1. Le client appelle `verif_data(result, "duree_moy_sej")` après réception.
2. Si `"dr"` est dans `flex_param`, le client appelle aussi `verif_data(result, "dr")`.
3. L'année est en format 4 chiffres (contrairement au paramètre `annee` envoyé en 2 chiffres).

---

### 3.3 `GET /diag_assoc`

**Description** : Retourne les diagnostics associés significatifs (DAS) des séjours du périmètre. Utilisé par le module DAS.

**Paramètres spécifiques** : `var` (optionnel, ventilation)

#### Schéma de réponse

| Colonne | Type R | Description |
|---|---|---|
| `code_diag` | character | Code CIM-10 du diagnostic associé (renommé en `diag` côté client) |
| `nb_sej` | integer | Nombre de séjours avec ce DAS |
| `duree_moy_sej` | numeric | Durée moyenne de séjour (peut être absente) |
| `tx_dc` | numeric | Taux de décès |
| `tx_male` | numeric | Taux masculin |
| `age_moy` | numeric | Âge moyen |
| `dr` | character | Diagnostic relié (si `"dr"` dans `var`) |
| Colonne(s) de `var` | character | Variable(s) de ventilation additionnelles |

#### Exemple JSON — Sans `var`

```json
[
  {"code_diag": "I10", "nb_sej": 8765, "duree_moy_sej": 6.78, "tx_dc": 0.0234, "tx_male": 0.5123, "age_moy": 72.3},
  {"code_diag": "E11", "nb_sej": 6543, "duree_moy_sej": 7.45, "tx_dc": 0.0312, "tx_male": 0.4876, "age_moy": 68.9},
  {"code_diag": "N18", "nb_sej": 4321, "duree_moy_sej": 8.12, "tx_dc": 0.0456, "tx_male": 0.5234, "age_moy": 74.1},
  {"code_diag": "J96", "nb_sej": 3456, "duree_moy_sej": 12.34, "tx_dc": 0.0789, "tx_male": 0.5567, "age_moy": 76.8},
  {"code_diag": "E78", "nb_sej": 2987, "duree_moy_sej": 5.67, "tx_dc": 0.0178, "tx_male": 0.4987, "age_moy": 65.4},
  {"code_diag": "F10", "nb_sej": 2345, "duree_moy_sej": 9.23, "tx_dc": 0.0345, "tx_male": 0.7234, "age_moy": 58.7}
]
```

#### Règles de gestion spécifiques

1. Le client appelle `verif_data(result, "duree_moy_sej")`.
2. Si `"dr"` est dans `flex_param`, le client appelle `verif_data(result, "dr")`.
3. Les colonnes de ventilation supplémentaires sont ajoutées selon `var`.

---

### 3.4 `GET /um`

**Description** : Retourne les données par unité médicale (UM). Utilisé par le module UM.

**Paramètres spécifiques** : `var` (optionnel, ventilation)

#### Schéma de réponse

| Colonne | Type R | Description |
|---|---|---|
| `code_rum` | character | Code du type d'unité médicale (renommé en `um` côté client) |
| `nb_sej` | integer | Nombre de séjours |
| `duree_moy_sej` | numeric | Durée moyenne de séjour (peut être absente) |
| `duree_moy_rum` | numeric | Durée moyenne par RUM |
| `tx_dc` | numeric | Taux de décès |
| `tx_male` | numeric | Taux masculin |
| `age_moy` | numeric | Âge moyen |
| `dr` | character | Diagnostic relié (si `"dr"` dans `var`) |
| Colonne(s) de `var` | character | Variable(s) de ventilation additionnelles |

#### Exemple JSON — Sans `var`

```json
[
  {"code_rum": "01", "nb_sej": 15432, "duree_moy_sej": 6.34, "duree_moy_rum": 5.12, "tx_dc": 0.0234, "tx_male": 0.5123, "age_moy": 68.7},
  {"code_rum": "02", "nb_sej": 12345, "duree_moy_sej": 4.56, "duree_moy_rum": 3.89, "tx_dc": 0.0045, "tx_male": 0.3876, "age_moy": 42.3},
  {"code_rum": "03", "nb_sej": 8765, "duree_moy_sej": 7.89, "duree_moy_rum": 6.45, "tx_dc": 0.0345, "tx_male": 0.5567, "age_moy": 72.1},
  {"code_rum": "04", "nb_sej": 6543, "duree_moy_sej": 3.23, "duree_moy_rum": 2.87, "tx_dc": 0.0012, "tx_male": 0.4234, "age_moy": 55.8},
  {"code_rum": "13", "nb_sej": 4321, "duree_moy_sej": 12.45, "duree_moy_rum": 10.23, "tx_dc": 0.0567, "tx_male": 0.5012, "age_moy": 76.4},
  {"code_rum": "18", "nb_sej": 2345, "duree_moy_sej": 2.12, "duree_moy_rum": 1.87, "tx_dc": 0.0008, "tx_male": 0.4567, "age_moy": 38.9}
]
```

#### Règles de gestion spécifiques

1. Le client appelle `verif_data(result, "duree_moy_sej")`.
2. Si `"dr"` est dans `flex_param`, le client appelle `verif_data(result, "dr")`.
3. La colonne `duree_moy_rum` est spécifique à cet endpoint (durée au niveau RUM, pas séjour).

---

### 3.5 `GET /dmi_med`

**Description** : Retourne les données de valorisation des médicaments (UCD) et dispositifs médicaux implantables (DMI/LPP). Utilisé par le module Valorisation médicaments/DMI.

**Paramètres spécifiques** : `var` (optionnel, ventilation)

#### Schéma de réponse

| Colonne | Type R | Description |
|---|---|---|
| `datasource` | character | Source : `"med"` (médicaments) ou `"dmi"` (DMI) |
| `code` | character | Code produit (code_ucd ou code_lpp) |
| `nb` | integer | Nombre d'unités administrées/posées |
| `nb_sej` | integer | Nombre de séjours |
| `nb_pat` | integer | Nombre de patients |
| `mnt_remb` | numeric | Montant remboursé (euros) |
| `duree_moy_sej` | numeric | Durée moyenne de séjour |
| `age_moy` | numeric | Âge moyen |
| `code_ucd` | character | Code UCD (pour médicaments) |
| `atc1` | character | Classe ATC niveau 1 |
| `atc2` | character | Classe ATC niveau 2 |
| `atc3` | character | Classe ATC niveau 3 |
| `atc4` | character | Classe ATC niveau 4 |
| `atc5` | character | Classe ATC niveau 5 |
| `lib_ucd` | character | Libellé UCD |
| `code_lpp` | character | Code LPP (pour DMI) |
| `hiera` | character | Code hiérarchie LPP |
| `hiera_libelle` | character | Libellé hiérarchie LPP |
| Colonne(s) de `var` | character | Variable(s) de ventilation additionnelles |

#### Exemple JSON

```json
[
  {"datasource": "med", "code": "9360937", "code_ucd": "9360937", "lib_ucd": "BEVACIZUMAB 100MG/4ML", "atc1": "L", "atc2": "L01", "atc3": "L01F", "atc4": "L01FG", "atc5": "L01FG01", "nb": 4567, "nb_sej": 2345, "nb_pat": 1987, "mnt_remb": 1234567.89, "duree_moy_sej": 2.34, "age_moy": 65.4, "code_lpp": null, "hiera": null, "hiera_libelle": null},
  {"datasource": "med", "code": "9261337", "code_ucd": "9261337", "lib_ucd": "RITUXIMAB 500MG/50ML", "atc1": "L", "atc2": "L01", "atc3": "L01F", "atc4": "L01FA", "atc5": "L01FA01", "nb": 3456, "nb_sej": 1876, "nb_pat": 1654, "mnt_remb": 987654.32, "duree_moy_sej": 1.89, "age_moy": 62.1, "code_lpp": null, "hiera": null, "hiera_libelle": null},
  {"datasource": "dmi", "code": "3415677", "code_ucd": null, "lib_ucd": null, "atc1": null, "atc2": null, "atc3": null, "atc4": null, "atc5": null, "nb": 876, "nb_sej": 876, "nb_pat": 854, "mnt_remb": 456789.12, "duree_moy_sej": 5.67, "age_moy": 71.2, "code_lpp": "3415677", "hiera": "04", "hiera_libelle": "IMPLANTS ARTICULAIRES"},
  {"datasource": "dmi", "code": "3157742", "code_ucd": null, "lib_ucd": null, "atc1": null, "atc2": null, "atc3": null, "atc4": null, "atc5": null, "nb": 654, "nb_sej": 654, "nb_pat": 632, "mnt_remb": 345678.90, "duree_moy_sej": 4.23, "age_moy": 68.9, "code_lpp": "3157742", "hiera": "06", "hiera_libelle": "IMPLANTS CARDIO-VASCULAIRES"},
  {"datasource": "med", "code": "9340017", "code_ucd": "9340017", "lib_ucd": "TRASTUZUMAB 150MG", "atc1": "L", "atc2": "L01", "atc3": "L01F", "atc4": "L01FD", "atc5": "L01FD01", "nb": 2345, "nb_sej": 1234, "nb_pat": 1098, "mnt_remb": 876543.21, "duree_moy_sej": 1.56, "age_moy": 58.3, "code_lpp": null, "hiera": null, "hiera_libelle": null}
]
```

#### Règles de gestion spécifiques

1. Pas d'appel à `verif_data()` côté client (code commenté dans le source).
2. Le module utilise `datasource` pour séparer les onglets Médicaments et DMI.
3. Le module utilise les niveaux ATC (`atc1` à `atc5`) pour la navigation drill-down.

---

### 3.6 `GET /actes`

**Description** : Retourne les actes classants CCAM des séjours du périmètre. Utilisé par le module Actes classants.

**Paramètres spécifiques** : `var` (optionnel, ventilation)

#### Schéma de réponse

| Colonne | Type R | Description |
|---|---|---|
| `code_ccam` | character | Code CCAM de l'acte |
| `extension_pmsi` | character | Extension PMSI de l'acte |
| `nb_acte` | integer | Nombre d'actes réalisés |
| `nb_sej` | integer | Nombre de séjours |
| `duree_moy_sej` | numeric | Durée moyenne de séjour (peut être absente) |
| `tx_male` | numeric | Taux masculin |
| `age_moy` | numeric | Âge moyen |
| `acte_activ` | character | Niveau d'activité de l'acte (1-5) |
| `is_classant` | integer | Acte classant (1) ou non (0) |
| `dr` | character | Diagnostic relié (si `"dr"` dans `var`) |
| Colonne(s) de `var` | character | Variable(s) de ventilation additionnelles |

#### Exemple JSON — Sans `var`

```json
[
  {"code_ccam": "DZQM006", "extension_pmsi": "0", "nb_acte": 4567, "nb_sej": 4321, "duree_moy_sej": 3.45, "tx_male": 0.5432, "age_moy": 62.3, "acte_activ": "1", "is_classant": 1},
  {"code_ccam": "YYYY600", "extension_pmsi": "0", "nb_acte": 3876, "nb_sej": 3654, "duree_moy_sej": 0.00, "tx_male": 0.4876, "age_moy": 58.7, "acte_activ": "1", "is_classant": 1},
  {"code_ccam": "EQQP004", "extension_pmsi": "0", "nb_acte": 3234, "nb_sej": 2987, "duree_moy_sej": 5.67, "tx_male": 0.4567, "age_moy": 71.2, "acte_activ": "1", "is_classant": 1},
  {"code_ccam": "HFMA009", "extension_pmsi": "0", "nb_acte": 2876, "nb_sej": 2654, "duree_moy_sej": 4.12, "tx_male": 0.3456, "age_moy": 55.6, "acte_activ": "1", "is_classant": 1},
  {"code_ccam": "ZCQM002", "extension_pmsi": "0", "nb_acte": 2345, "nb_sej": 2123, "duree_moy_sej": 6.78, "tx_male": 0.4234, "age_moy": 67.8, "acte_activ": "1", "is_classant": 0},
  {"code_ccam": "ABLB001", "extension_pmsi": "1", "nb_acte": 1987, "nb_sej": 1876, "duree_moy_sej": 2.34, "tx_male": 0.5678, "age_moy": 59.4, "acte_activ": "1", "is_classant": 1}
]
```

#### Règles de gestion spécifiques

1. Le client appelle `verif_data(result, "duree_moy_sej")`.
2. Si `"dr"` est dans `flex_param`, le client appelle `verif_data(result, "dr")`.
3. Le module enrichit `code_ccam` avec le libellé depuis `df_ccam` (nomenclature CCAM).

---

### 3.7 `GET /tx_recours`

**Description** : Retourne les taux de recours géographiques (nombre de séjours/patients pour 1000 habitants par zone géographique). Utilisé par le module Taux de recours avec cartographie Leaflet.

**Paramètres spécifiques** : `type_geo_tx_recours` (niveau géographique, défaut `"dep"`)

#### Schéma de réponse

| Colonne | Type R | Description |
|---|---|---|
| `typ_geo` | character | Type géographique : `"dep"`, `"reg"`, `"zon"`, `"ts"`, `"geo"` |
| `code` | character | Code géographique (code département, région, etc.) |
| `nb_sej` | integer | Nombre de séjours |
| `nb_pat` | integer | Nombre de patients |
| `nb_pop` | integer | Population de la zone (habitants) |
| `tx_recours_brut_sej` | numeric | Taux de recours brut en séjours (/ 1000 hab) |
| `tx_recours_brut_pat` | numeric | Taux de recours brut en patients (/ 1000 hab) |
| `tx_recours_standard_sej` | numeric | Taux de recours standardisé en séjours (/ 1000 hab) |
| `tx_recours_standard_pat` | numeric | Taux de recours standardisé en patients (/ 1000 hab) |

#### Exemple JSON — `type_geo_tx_recours=dep`

```json
[
  {"typ_geo": "dep", "code": "75", "nb_sej": 234567, "nb_pat": 198765, "nb_pop": 2165423, "tx_recours_brut_sej": 108.32, "tx_recours_brut_pat": 91.79, "tx_recours_standard_sej": 95.67, "tx_recours_standard_pat": 82.34},
  {"typ_geo": "dep", "code": "13", "nb_sej": 187654, "nb_pat": 156432, "nb_pop": 2024162, "tx_recours_brut_sej": 92.71, "tx_recours_brut_pat": 77.28, "tx_recours_standard_sej": 88.45, "tx_recours_standard_pat": 74.12},
  {"typ_geo": "dep", "code": "69", "nb_sej": 165432, "nb_pat": 143210, "nb_pop": 1843319, "tx_recours_brut_sej": 89.75, "tx_recours_brut_pat": 77.69, "tx_recours_standard_sej": 86.23, "tx_recours_standard_pat": 75.34},
  {"typ_geo": "dep", "code": "33", "nb_sej": 143210, "nb_pat": 121987, "nb_pop": 1623749, "tx_recours_brut_sej": 88.20, "tx_recours_brut_pat": 75.13, "tx_recours_standard_sej": 84.56, "tx_recours_standard_pat": 72.89},
  {"typ_geo": "dep", "code": "59", "nb_sej": 198765, "nb_pat": 176543, "nb_pop": 2604361, "tx_recours_brut_sej": 76.32, "tx_recours_brut_pat": 67.80, "tx_recours_standard_sej": 79.45, "tx_recours_standard_pat": 70.12},
  {"typ_geo": "dep", "code": "31", "nb_sej": 132456, "nb_pat": 112345, "nb_pop": 1400039, "tx_recours_brut_sej": 94.61, "tx_recours_brut_pat": 80.24, "tx_recours_standard_sej": 89.78, "tx_recours_standard_pat": 76.45}
]
```

#### Règles de gestion spécifiques

1. Le module filtre par `typ_geo` pour afficher le bon niveau géographique.
2. Le module filtre `!is.na(code)` pour exclure les lignes sans code géographique.
3. Aucun appel `verif_data()` côté client.
4. Le module effectue une jointure avec la carte géographique (`cartes[[type_rgp]]`) via le champ `codgeo`.
5. Les taux sont exprimés pour 1000 habitants.

---

### 3.8 `GET /dernier_trans`

**Description** : Retourne la date de dernière transmission PMSI par établissement. Utilisé par le module Dernière Transmission. Ce endpoint est **exempt du contrôle `petit_effectif`** car il s'agit de données administratives.

**Paramètres spécifiques** : Aucun (paramètres communs uniquement)

#### Schéma de réponse

| Colonne | Type R | Description |
|---|---|---|
| `annee` | integer | Année PMSI (supprimée à l'affichage par le module) |
| `finess` | character | Code FINESS PMSI de l'établissement |
| `rs` | character | Raison sociale de l'établissement |
| `secteur` | character | Secteur (public/privé) |
| `categ` | character | Catégorie d'établissement |
| `derniere_transmission` | character | Date de dernière transmission (format `"YYYY-MM-DD"`) |

#### Exemple JSON

```json
[
  {"annee": 2023, "finess": "130783293", "rs": "AP-HM HOPITAL DE LA TIMONE", "secteur": "PU", "categ": "CH", "derniere_transmission": "2024-03-15"},
  {"annee": 2023, "finess": "750100018", "rs": "AP-HP HOPITAL HOTEL-DIEU", "secteur": "PU", "categ": "CH", "derniere_transmission": "2024-03-12"},
  {"annee": 2023, "finess": "690023154", "rs": "HCL HOPITAL EDOUARD HERRIOT", "secteur": "PU", "categ": "CH", "derniere_transmission": "2024-03-18"},
  {"annee": 2023, "finess": "330781196", "rs": "CHU DE BORDEAUX", "secteur": "PU", "categ": "CH", "derniere_transmission": "2024-03-10"},
  {"annee": 2023, "finess": "310781406", "rs": "CHU DE TOULOUSE", "secteur": "PU", "categ": "CH", "derniere_transmission": "2024-03-14"},
  {"annee": 2023, "finess": "440000289", "rs": "CLINIQUE JULES VERNE", "secteur": "PR", "categ": "CL", "derniere_transmission": "2024-02-28"},
  {"annee": 2023, "finess": "060780491", "rs": "CLINIQUE SAINT-GEORGE", "secteur": "PR", "categ": "CL", "derniere_transmission": "2024-03-05"}
]
```

#### Règles de gestion spécifiques

1. Le module supprime la colonne `annee` avant affichage (`dplyr::select(-annee)`).
2. Ce endpoint est **explicitement exclu** du contrôle `petit_effectif` dans `get_data()`.
3. Les colonnes affichées dans le DT sont : Finess PMSI, Raison sociale, Secteur, Catégorie, Dernière transmission.

---

## 4. Variations de réponse selon le paramètre `var`

Le paramètre `var` contrôle les colonnes de ventilation ajoutées à la réponse. Il est construit en joignant les noms de variables par `_` (ex. `var=ghm_mois`). Chaque valeur de `var` ajoute une ou plusieurs colonnes de groupement à la réponse.

### 4.1 Table des colonnes ajoutées

| Valeur de `var` | Colonne(s) ajoutée(s) | Type R | Utilisé par |
|---|---|---|---|
| `sexe` | `sexe` | character (`"1"`, `"2"`) | Flexible |
| `trancheage` | `trancheage` | character (`"[0-10 ans]"`, ...) | Pyramide (avec `sexe`) |
| `sexe_trancheage` | `sexe`, `trancheage` | character | Pyramide |
| `mois` | `mois` | integer (1-12) | Évolution mensuelle |
| `finess` | `finess` | character (9 chiffres) | Répartition FINESS, Carto |
| `dp` | `dp` | character (code CIM-10) | Diagnostic principal |
| `dr` | `dr` | character (code CIM-10) | Flexible, DAS, UM, Casemix, etc. |
| `ghm` | `ghm` | character (6 car., ex. `"05M09T"`) | Casemix |
| `racine` | `racine` | character (5 car., ex. `"05M09"`) | Casemix |
| `cmd` | `cmd` | character (2 chiffres) | Casemix |
| `da` | `da` | character | Casemix |
| `ga` | `ga` | character | Casemix |
| `gp` | `gp` | character | Casemix |
| `aso` | `aso` | character | Casemix |
| `cas` | `cas` | character | Casemix |
| `duree` | `duree` | integer (0, 1, 2, ...) | DMS |
| `typhosp` | `typhosp` | character (`"M"`, `"C"`, `"O"`) | Flexible |
| `categ` | `categ` | character | Flexible |
| `secteur` | `secteur` | character | Flexible |
| `finessgeo` | `finessgeo` | character (9 chiffres) | Flexible |
| `regetab` | `regetab` | character (code région) | Flexible |
| `depetab` | `depetab` | character (code département) | Flexible |
| `tsetab` | `tsetab` | character | Flexible |
| `zonetab` | `zonetab` | character | Flexible |
| `regpat` | `regpat` | character (code région) | Flexible |
| `deppat` | `deppat` | character (code département) | Flexible |
| `tspat` | `tspat` | character | Flexible |
| `codegeo` | `codegeo` | character | Flexible |
| `zonpat` | `zonpat` | character | Flexible |
| `modentprov` | `modentprov` | character (ex. `"8_1"`) | Modes E/S |
| `modsordest` | `modsordest` | character (ex. `"8_4"`) | Modes E/S |
| `modentprov_modsordest` | `modentprov`, `modsordest` | character | Modes E/S (parcours) |
| `modeeentree` | `modeeentree` | character | Flexible |
| `modesortie` | `modesortie` | character | Flexible |
| `provenance` | `provenance` | character | Flexible |
| `destination` | `destination` | character | Flexible |
| `passageurg` | `passageurg` | character (`"0"`, `"1"`) | Flexible |

### 4.2 Combinaisons courantes

Les modules peuvent combiner plusieurs valeurs de `var` séparées par `_`. Les colonnes de toutes les valeurs sont alors présentes dans la réponse. Le mock doit supporter les combinaisons suivantes :

| Combinaison | Modules |
|---|---|
| `sexe_trancheage` | Pyramide des âges |
| `modentprov_modsordest` | Modes entrée/sortie (parcours Sankey) |
| `ghm_mois` | Multi-year avec GHM et mois |
| `finess` | Répartition FINESS, Cartographie |
| `ghm` | Casemix (défaut) |
| `mois` | Évolution mensuelle |
| `dp` | Diagnostic principal |
| `duree` | Distribution durée de séjour |

### 4.3 Exemple avec combinaison `var=ghm_typhosp`

```json
[
  {"ghm": "05M09T", "typhosp": "M", "nb_sej": 1234, "duree_moy_sej": 7.89, "tx_dc": 0.0123, "tx_male": 0.5432, "age_moy": 71.2},
  {"ghm": "05M09T", "typhosp": "C", "nb_sej": 567, "duree_moy_sej": 4.56, "tx_dc": 0.0089, "tx_male": 0.5678, "age_moy": 69.8},
  {"ghm": "05K06T", "typhosp": "C", "nb_sej": 1987, "duree_moy_sej": 3.45, "tx_dc": 0.0034, "tx_male": 0.6123, "age_moy": 67.8},
  {"ghm": "06C04Z", "typhosp": "C", "nb_sej": 1432, "duree_moy_sej": 4.12, "tx_dc": 0.0012, "tx_male": 0.3234, "age_moy": 55.6},
  {"ghm": "06C04Z", "typhosp": "O", "nb_sej": 234, "duree_moy_sej": 3.78, "tx_dc": 0.0004, "tx_male": 0.0000, "age_moy": 31.2}
]
```

---

## 5. Gestion des erreurs et cas limites

### 5.1 Codes HTTP et messages

L'API mock doit reproduire les codes d'erreur gérés par `api_erreur_libelle` dans `fct_helpers.R` :

| Code HTTP | Label français | Quand l'utiliser dans le mock |
|---|---|---|
| `200` | (succès) | Réponse normale avec données JSON |
| `400` | Requête invalide | Paramètre `annee` manquant ou invalide |
| `404` | Pas de résultat | Périmètre de filtrage ne correspondant à aucun séjour |
| `500` | Erreur du serveur | Erreur interne simulée |
| `503` | Serveur indisponible | Serveur mock arrêté ou en maintenance |
| `504` | Timeout | Simulation de timeout (ne pas implémenter sauf test) |

En cas d'erreur, `call_api_and_unwrap()` retourne le code HTTP (integer) au lieu d'un data.frame.

Le format de réponse d'erreur n'est pas significatif pour le client (seul le `status_code` HTTP est lu). L'API mock peut retourner un body vide ou un message JSON simple.

### 5.2 Format `petit_effectif`

Quand le périmètre de requête concerne moins de 10 séjours, l'API doit gérer le secret statistique.

**Méthode A — Via `nb_pat`** (endpoint `/resume` avec `bool_nb_pat=TRUE`) :

La colonne `nb_pat` contient la chaîne `"petit_effectif"` au lieu d'un entier :

```json
[
  {
    "nb_sej": 5,
    "nb_pat": "petit_effectif",
    "duree_moy_sej": 3.2,
    "tx_dc": 0.0,
    "tx_male": 0.6,
    "age_moy": 45.3
  }
]
```

**Méthode B — Réponse tout-non-numérique** (autres endpoints) :

Quand l'effectif est trop petit, l'API retourne un dataframe où toutes les colonnes sont des chaînes de caractères (aucune colonne numérique). Le client détecte cela via :

```r
all(sapply(config_data, function(col) !any(is.numeric(col))))
```

Exemple pour `/actes` en petit effectif :

```json
[
  {"code_ccam": "DZQM006"}
]
```

### 5.3 Renommages automatiques côté client

Le client (`call_api_and_unwrap()`) effectue systématiquement ces renommages après réception :

| Colonne API | Colonne renommée | Raison |
|---|---|---|
| `passage_urg` | `passageurg` | Convention interne de l'app |
| `typ_hosp` | `typhosp` | Convention interne de l'app |

L'API mock peut choisir de retourner directement les noms internes (`passageurg`, `typhosp`) ou les noms API (`passage_urg`, `typ_hosp`) — le client gère les deux cas.

### 5.4 Colonnes optionnelles et `verif_data()`

Les colonnes `duree_moy_sej` et `dr` peuvent être absentes de la réponse. Le client les ajoute automatiquement avec la valeur `"0"` (character) via `verif_data()`. L'API mock devrait idéalement toujours les inclure pour simplifier, mais leur absence est tolérée.

---

## 6. Données de référence nécessaires

L'application utilise des nomenclatures côté client pour enrichir les codes retournés par l'API avec des libellés. Ces nomenclatures ne sont pas servies par l'API mais sont packagées dans l'application R.

### 6.1 Nomenclatures côté client

Le mock n'a pas besoin de fournir ces données, mais les codes retournés doivent être cohérents avec ces référentiels.

| Nomenclature | Objet R | Colonnes | Usage |
|---|---|---|---|
| GHM | `df_classif` / `nomenclature$ghm` | `var`, `lib`, `annee_deb`, `annee_fin` | Libellés GHM, racine, CMD, DA, GA, GP, ASO, CAS |
| CIM-10 | `nomenclature$diag` | `var`, `lib`, `annee_deb`, `annee_fin` | Libellés diagnostics (DP, DAS, DR) |
| CCAM | `df_ccam` / `nomenclature$ccam` | `var`, `lib`, `annee_deb`, `annee_fin` | Libellés actes CCAM |
| FINESS | `df_finess` | `finess`, `finessgeo`, `secteur`, `region`, `departement`, `categ`, `rs`, `code_com`, `code_ght`, `lib_ght`, `nb_rsa`, `annee` | Référentiel établissements |
| Géographie | `nomenclature$reg`, `$dep`, `$ts`, `$zon` | `var`, `lib`, `annee_deb`, `annee_fin` | Noms régions, départements, territoires |
| UCD | `nomenclature$ucd` ou `nomen_med` | `var`, `lib`, `annee_deb`, `annee_fin` | Libellés médicaments |
| LPP | `nomenclature$lpp` ou `nomen_dmi` | `var`, `lib`, `annee_deb`, `annee_fin` | Libellés DMI |
| UM | `nomenclature$um` | `var`, `lib`, `annee_deb`, `annee_fin` | Libellés unités médicales |
| Modes E/S | implicite dans l'app | mode, provenance, destination | Codes modes d'entrée/sortie |

### 6.2 Format standard des nomenclatures

Toutes les nomenclatures suivent le format :

| Colonne | Type | Description |
|---|---|---|
| `var` | character | Code de la nomenclature |
| `lib` | character | Libellé français |
| `annee_deb` | character | Année de début de validité |
| `annee_fin` | character | Année de fin de validité (`"9999"` = encore valide) |

### 6.3 Codes exemples pour le mock

Pour produire des données fictives cohérentes, utiliser ces codes représentatifs :

| Référentiel | Codes exemples |
|---|---|
| GHM | `05M09T`, `05K06T`, `01M10T`, `06C04Z`, `08M04T`, `14Z08Z` |
| Racine GHM | `05M09`, `05K06`, `01M10`, `06C04`, `08M04` |
| CMD | `01`, `05`, `06`, `08`, `14` |
| CIM-10 (DP/DAS) | `C34`, `I50`, `J44`, `K80`, `S72`, `I10`, `E11`, `N18` |
| CCAM | `DZQM006`, `YYYY600`, `EQQP004`, `HFMA009`, `ZCQM002` |
| FINESS | `130783293`, `750100018`, `690023154`, `330781196`, `310781406` |
| Département | `75`, `13`, `69`, `33`, `59`, `31` |
| Région | `11` (IDF), `93` (PACA), `84` (ARA), `75` (NA), `32` (HDF) |
| Type UM | `01`, `02`, `03`, `04`, `13`, `18` |
| UCD | `9360937`, `9261337`, `9340017` |
| LPP | `3415677`, `3157742` |

---

## 7. Annexe — var_list complète

Mapping complet des 29 variables de ventilation disponibles, tel que défini dans `data-raw/nomen_variables.R` :

| Label français | Nom interne (`var`) | Description |
|---|---|---|
| Type d'hospitalisation (ambu/hc/séances) | `typhosp` | `"M"` (médecine), `"C"` (chirurgie), `"O"` (obstétrique) |
| Sexe | `sexe` | `"1"` (homme), `"2"` (femme) |
| Tranche d'âge | `trancheage` | Groupes d'âge selon les bornes fournies |
| Région (localisation établissement) | `regetab` | Code région de l'établissement |
| Département (localisation établissement) | `depetab` | Code département de l'établissement |
| Territoire de santé (localisation établissement) | `tsetab` | Code TS de l'établissement |
| Zone ARS (localisation établissement) | `zonetab` | Code zone ARS de l'établissement |
| Catégorie d'établissement | `categ` | Code catégorie (CH, CL, etc.) |
| Secteur de financement | `secteur` | PU (public), PR (privé), etc. |
| Finess PMSI | `finess` | Code FINESS PMSI (9 chiffres) |
| Finess géographique | `finessgeo` | Code FINESS géographique (9 chiffres) |
| Région (domiciliation patient) | `regpat` | Code région du domicile patient |
| Département (domiciliation patient) | `deppat` | Code département du domicile patient |
| Territoire de santé (domiciliation patient) | `tspat` | Code TS du domicile patient |
| Code géographique de domiciliation du patient | `codegeo` | Code géographique détaillé |
| Zone ARS | `zonpat` | Code zone ARS du domicile patient |
| Mois de sortie du séjour | `mois` | Mois (1-12) |
| Diagnostic principal | `dp` | Code CIM-10 du DP |
| Diagnostic relié du séjour | `dr` | Code CIM-10 du DR |
| GHM | `ghm` | Code GHM (6 caractères) |
| Racine de GHM | `racine` | Racine GHM (5 caractères) |
| Catégorie Majeure de Diagnostic | `cmd` | Code CMD (2 chiffres) |
| Groupe d'activité | `ga` | Code GA |
| Groupe de planification | `gp` | Code GP |
| Domaine d'activité | `da` | Code DA |
| Activité de soins | `aso` | Code ASO |
| Catégorie d'activité de soins | `cas` | Code CAS |
| Mode d'entrée | `modeeentree` | Code mode d'entrée (note : double `e` dans `var_list`) |
| Mode de sortie | `modesortie` | Code mode de sortie |
| Provenance | `provenance` | Code provenance |
| Destination | `destination` | Code destination |
| Passage par les urgences | `passageurg` | `"0"` (non) ou `"1"` (oui) |

**Note** : Le nom interne `modeeentree` (double `e`) dans `var_list` est une anomalie connue. Le paramètre API correspondant est `modeentree` (simple `e`).

**Note `var_pyear_lst`** : Le module multi-annuel utilise une liste de variables différente (`var_pyear_lst`) qui diffère de `var_list` sur deux points :
- `modeentree` (simple `e`) au lieu de `modeeentree` (double `e`)
- `codegeo` est absent de `var_pyear_lst`
- Un choix `"aucun"` est ajouté pour signifier « pas de variable de ventilation »
