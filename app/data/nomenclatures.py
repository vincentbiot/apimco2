# =============================================================================
# app/data/nomenclatures.py — Données de référence du PMSI MCO
#
# Ce module centralise tous les codes de nomenclature utilisés pour générer
# des données fictives mais cohérentes avec les référentiels réels.
#
# Chaque dictionnaire mappe un code (clé) vers un libellé (valeur).
# Les codes sont issus de la spec §6.3.
#
# Organisation :
#   1. Nomenclatures cliniques  : GHM, racine, CMD, CIM-10, CCAM
#   2. Nomenclatures géo etab   : FINESS, secteur, catégorie
#   3. Nomenclatures géographiques : départements, régions
#   4. Nomenclatures UM         : types d'unités médicales
#   5. Nomenclatures médicaments : UCD + hiérarchie ATC
#   6. Nomenclatures DMI        : LPP + hiérarchie
#   7. Nomenclatures parcours   : modes entrée/sortie
#   8. VAR_VALUES               : valeurs disponibles par variable de ventilation
#   9. COMPOUND_VAR_NAMES       : noms de vars composées (parsing du paramètre var)
# =============================================================================

# =============================================================================
# 1. NOMENCLATURES CLINIQUES
# =============================================================================

# GHM — Groupes Homogènes de Malades (6 caractères)
# Format : CCCNNL (CMD + numéro + niveau de sévérité ou Z pour les actes)
GHM: dict[str, str] = {
    "05M09T": "Affections de l'appareil circulatoire, sévérité 4",
    "05K06T": "Coronarographies, sévérité 4",
    "01M10T": "Affections du système nerveux, sévérité 4",
    "06C04Z": "Appendicectomies sans complication",
    "08M04T": "Affections de l'appareil musculosquelettique, sévérité 4",
    "14Z08Z": "Séances de chimiothérapie pour tumeur",
    "11M05T": "Affections du rein et des voies urinaires, sévérité 4",
    "23Z02Z": "Autres séjours de moins de 2 jours",
}

# Racine de GHM (5 caractères = CMD + numéro sans niveau)
RACINE_GHM: dict[str, str] = {
    "05M09": "Affections de l'appareil circulatoire",
    "05K06": "Coronarographies",
    "01M10": "Affections du système nerveux - sévérité 4",
    "06C04": "Appendicectomies",
    "08M04": "Affections musculosquelettiques - sévérité 4",
    "14Z08": "Chimiothérapie pour tumeur",
    "11M05": "Affections du rein et des voies urinaires",
}

# CMD — Catégories Majeures de Diagnostic (2 chiffres)
CMD: dict[str, str] = {
    "01": "Affections du système nerveux",
    "05": "Affections de l'appareil circulatoire",
    "06": "Affections du tube digestif",
    "08": "Affections de l'appareil musculosquelettique",
    "11": "Affections du rein et des voies urinaires",
    "14": "Grossesses pathologiques, accouchements et affections du post-partum",
    "23": "Autres facteurs influant sur l'état de santé",
}

# CIM-10 — Classification Internationale des Maladies (codes DP/DR/DAS)
# Codes exemples issus de la spec §6.3 + codes fréquents en MCO
CIM10: dict[str, str] = {
    # Codes de la spec §6.3
    "C34": "Tumeur maligne des bronches et du poumon",
    "I50": "Insuffisance cardiaque",
    "J44": "Autres broncho-pneumopathies chroniques obstructives",
    "K80": "Lithiase biliaire",
    "S72": "Fracture du fémur",
    "I10": "Hypertension essentielle (primitive)",
    "E11": "Diabète de type 2",
    "N18": "Maladie rénale chronique",
    # Codes supplémentaires fréquents
    "J96": "Insuffisance respiratoire, non classée ailleurs",
    "E78": "Troubles du métabolisme des lipoprotéines",
    "F10": "Troubles mentaux et du comportement liés à l'utilisation d'alcool",
    "K57": "Maladie diverticulaire de l'intestin",
}

# CCAM — Classification Commune des Actes Médicaux (7 caractères)
# Format : AAAANNNN (4 lettres + 3 chiffres)
CCAM: dict[str, str] = {
    "DZQM006": "Enregistrement du signal électrique de coeur",
    "YYYY600": "Acte fictif de test PMSI",
    "EQQP004": "Arthroplastie totale de hanche",
    "HFMA009": "Cholécystectomie par coelioscopie",
    "ZCQM002": "Tomographie par émission de positons du corps entier",
    "ABLB001": "Hémicolectomie droite par coelioscopie",
    "BFGA004": "Coronarographie",
}

# =============================================================================
# 2. NOMENCLATURES ÉTABLISSEMENTS
# =============================================================================

# FINESS PMSI — codes à 9 chiffres des établissements
# Exemples issus de la spec §6.3
FINESS: dict[str, str] = {
    "130783293": "AP-HM HOPITAL DE LA TIMONE",
    "750100018": "AP-HP HOPITAL HOTEL-DIEU",
    "690023154": "HCL HOPITAL EDOUARD HERRIOT",
    "330781196": "CHU DE BORDEAUX",
    "310781406": "CHU DE TOULOUSE",
    "440000289": "CLINIQUE JULES VERNE",
    "060780491": "CLINIQUE SAINT-GEORGE",
}

# Catégories d'établissements
CATEG_ETAB: dict[str, str] = {
    "CH": "Centre hospitalier",
    "CHU": "Centre hospitalo-universitaire",
    "CL": "Clinique privée",
}

# Secteurs de financement
SECTEUR: dict[str, str] = {
    "PU": "Public",
    "PR": "Privé",
    "ESPIC": "Établissement de santé privé d'intérêt collectif",
}

# =============================================================================
# 3. NOMENCLATURES GÉOGRAPHIQUES
# =============================================================================

# Départements français — code INSEE (2 à 3 caractères)
DEPARTEMENTS: dict[str, str] = {
    "75": "Paris",
    "13": "Bouches-du-Rhône",
    "69": "Rhône",
    "33": "Gironde",
    "59": "Nord",
    "31": "Haute-Garonne",
    "67": "Bas-Rhin",
    "06": "Alpes-Maritimes",
    "34": "Hérault",
    "44": "Loire-Atlantique",
}

# Régions françaises — code INSEE à 2 chiffres (post-réforme 2016)
REGIONS: dict[str, str] = {
    "11": "Île-de-France",
    "93": "Provence-Alpes-Côte d'Azur",
    "84": "Auvergne-Rhône-Alpes",
    "75": "Nouvelle-Aquitaine",
    "32": "Hauts-de-France",
    "76": "Occitanie",
    "52": "Pays de la Loire",
    "44": "Grand Est",
}

# Codes géographiques (communes/IRIS pour domicile patient)
CODEGEO: list[str] = ["75001", "13001", "69001", "33001", "59001", "31001"]

# Codes de zones ARS et territoires de santé (simplifiés pour le mock)
ZONES_ARS: list[str] = ["ZON01", "ZON02", "ZON03", "ZON04"]
TERRITOIRES_SANTE: list[str] = ["TS01", "TS02", "TS03", "TS04", "TS05"]

# =============================================================================
# 4. NOMENCLATURE UNITÉS MÉDICALES
# =============================================================================

# Type d'UM — code à 2 chiffres (nomenclature RUM)
TYPE_UM: dict[str, str] = {
    "01": "Médecine",
    "02": "Chirurgie",
    "03": "Obstétrique",
    "04": "Réanimation",
    "13": "Soins intensifs",
    "18": "Ambulatoire et chirurgie ambulatoire",
}

# =============================================================================
# 5. NOMENCLATURE MÉDICAMENTS (UCD + hiérarchie ATC)
# =============================================================================

# UCD — Unités Communes de Dispensation (codes à 7 chiffres)
UCD: dict[str, str] = {
    "9360937": "BEVACIZUMAB 100MG/4ML",
    "9261337": "RITUXIMAB 500MG/50ML",
    "9340017": "TRASTUZUMAB 150MG",
    "9240487": "CETUXIMAB 5MG/ML SOLUTION INJECTABLE",
    "9286507": "NIVOLUMAB 10MG/ML SOLUTION INJECTABLE",
}

# Hiérarchie ATC (Anatomical Therapeutic Chemical classification) par UCD
# L'ATC classe les médicaments en 5 niveaux anatomiques/pharmacologiques.
# Ici, tous sont dans la classe L (antinéoplasiques) — fréquents en MCO T2A.
ATC_DATA: dict[str, dict[str, str]] = {
    "9360937": {  # Bevacizumab — anticorps monoclonal anti-VEGF
        "atc1": "L",
        "atc2": "L01",
        "atc3": "L01F",
        "atc4": "L01FG",
        "atc5": "L01FG01",
    },
    "9261337": {  # Rituximab — anticorps monoclonal anti-CD20
        "atc1": "L",
        "atc2": "L01",
        "atc3": "L01F",
        "atc4": "L01FA",
        "atc5": "L01FA01",
    },
    "9340017": {  # Trastuzumab — anticorps anti-HER2
        "atc1": "L",
        "atc2": "L01",
        "atc3": "L01F",
        "atc4": "L01FD",
        "atc5": "L01FD01",
    },
    "9240487": {  # Cetuximab — anticorps anti-EGFR
        "atc1": "L",
        "atc2": "L01",
        "atc3": "L01F",
        "atc4": "L01FE",
        "atc5": "L01FE01",
    },
    "9286507": {  # Nivolumab — inhibiteur de point de contrôle immunitaire
        "atc1": "L",
        "atc2": "L01",
        "atc3": "L01F",
        "atc4": "L01FF",
        "atc5": "L01FF01",
    },
}

# =============================================================================
# 6. NOMENCLATURE DMI / LPP (Dispositifs Médicaux Implantables)
# =============================================================================

# LPP — Liste des Produits et Prestations (codes à 7 chiffres)
LPP: dict[str, str] = {
    "3415677": "PROTHESE TOTALE DE HANCHE",
    "3157742": "STIMULATEUR CARDIAQUE DOUBLE CHAMBRE",
    "3401024": "PROTHESE TOTALE DE GENOU",
    "3401036": "BIOPROTHESE VALVULAIRE AORTIQUE",
}

# Hiérarchie LPP — niveaux de classification des DMI
HIERA_LPP: dict[str, str] = {
    "04": "IMPLANTS ARTICULAIRES",
    "06": "IMPLANTS CARDIO-VASCULAIRES",
    "07": "NEUROCHIRURGIE ET NEUROLOGIE",
    "08": "OPHTALMOLOGIE",
}

# =============================================================================
# 7. NOMENCLATURES PARCOURS (modes d'entrée / sortie)
# =============================================================================

# Modes d'entrée (1er chiffre du couple modentprov)
MODE_ENTREE: dict[str, str] = {
    "6": "Mutation (depuis un autre service du même établissement)",
    "7": "Transfert (depuis un autre établissement)",
    "8": "Domicile (entrée directe)",
}

# Modes de sortie (1er chiffre du couple modsordest)
MODE_SORTIE: dict[str, str] = {
    "6": "Mutation (vers un autre service du même établissement)",
    "7": "Transfert (vers un autre établissement)",
    "8": "Retour à domicile",
    "9": "Décès",
}

# Provenance (2e chiffre du couple mode_entrée_provenance)
PROVENANCE: dict[str, str] = {
    "1": "Domicile",
    "2": "MCO",
    "3": "SSR",
    "4": "Psychiatrie",
    "5": "HAD",
    "6": "EHPAD",
}

# Destination (2e chiffre du couple mode_sortie_destination)
DESTINATION: dict[str, str] = {
    "1": "Domicile",
    "2": "MCO",
    "3": "SSR",
    "4": "Psychiatrie",
    "5": "HAD",
    "6": "EHPAD",
}

# Types d'hospitalisation
TYPHOSP: dict[str, str] = {
    "M": "Médecine",
    "C": "Chirurgie",
    "O": "Obstétrique",
}

# Sexe du patient
SEXE: dict[str, str] = {
    "1": "Homme",
    "2": "Femme",
}

# =============================================================================
# 8. VAR_VALUES — valeurs disponibles pour chaque variable de ventilation
#
# Utilisé par le générateur mock pour produire les lignes de réponse.
# Chaque entrée associe un nom de var (tel qu'attendu dans le paramètre `var`)
# à la liste des valeurs que peut prendre cette dimension.
#
# Note : les vars composés (sexe_trancheage, modentprov_modsordest) ne sont
# pas listés ici — ils sont gérés dynamiquement dans mock_data.py.
# =============================================================================

VAR_VALUES: dict[str, list] = {
    # --- Démographie ---
    "sexe": list(SEXE.keys()),                    # ["1", "2"]
    "typhosp": list(TYPHOSP.keys()),              # ["M", "C", "O"]
    "passageurg": ["0", "1"],

    # --- Temporel ---
    "mois": list(range(1, 13)),                   # [1, 2, ..., 12]
    "duree": list(range(0, 16)),                  # [0, 1, ..., 15]

    # --- Classification clinique ---
    "ghm": list(GHM.keys()),
    "racine": list(RACINE_GHM.keys()),
    "cmd": list(CMD.keys()),
    "dp": list(CIM10.keys()),
    "dr": list(CIM10.keys()),

    # Sous-classifications GHM (codes simplifiés pour le mock)
    "da": ["01", "02", "03", "04", "05"],
    "ga": ["GA01", "GA02", "GA03", "GA04"],
    "gp": ["GP01", "GP02", "GP03"],
    "aso": ["ASO1", "ASO2", "ASO3"],
    "cas": ["CAS1", "CAS2", "CAS3"],

    # --- Établissement ---
    "finess": list(FINESS.keys()),
    "finessgeo": list(FINESS.keys()),             # même codes pour le mock
    "categ": list(CATEG_ETAB.keys()),
    "secteur": list(SECTEUR.keys()),

    # --- Géographie établissement ---
    "regetab": list(REGIONS.keys()),
    "depetab": list(DEPARTEMENTS.keys()),
    "tsetab": TERRITOIRES_SANTE,
    "zonetab": ZONES_ARS,

    # --- Géographie patient ---
    "regpat": list(REGIONS.keys()),
    "deppat": list(DEPARTEMENTS.keys()),
    "tspat": TERRITOIRES_SANTE,
    "codegeo": CODEGEO,
    "zonpat": ZONES_ARS,

    # --- Parcours (pour les vars simples) ---
    "modentprov": ["8_1", "8_5", "6_1", "7_1"],   # couple modentree_provenance
    "modsordest": ["8_4", "6_1", "7_3", "9_9"],   # couple modsortie_destination
    "modeeentree": list(MODE_ENTREE.keys()),
    "modesortie": list(MODE_SORTIE.keys()),
    "provenance": list(PROVENANCE.keys()),
    "destination": list(DESTINATION.keys()),
}

# =============================================================================
# 9. COMPOUND_VAR_NAMES — noms de variables composées
#
# Ces chaînes sont reconnues comme des tokens unitaires lors du parsing
# du paramètre `var`, même si elles contiennent un underscore.
#
# Exemples :
#   var="sexe_trancheage"          → token unique → colonnes sexe + trancheage
#   var="modentprov_modsordest"    → token unique → colonnes modentprov + modsordest
#   var="sexe_trancheage_ghm"      → 2 tokens : "sexe_trancheage" + "ghm"
# =============================================================================

COMPOUND_VAR_NAMES: frozenset[str] = frozenset(
    [
        "sexe_trancheage",       # Pyramide des âges : colonnes sexe + trancheage
        "modentprov_modsordest", # Modes E/S parcours : colonnes modentprov + modsordest
    ]
)
