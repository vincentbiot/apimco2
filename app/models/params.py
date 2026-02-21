# =============================================================================
# app/models/params.py — Paramètres de requête communs à tous les endpoints
#
# Concepts FastAPI introduits dans cette étape :
#
#   1. Depends() — Injection de dépendances
#      FastAPI peut injecter automatiquement des objets dans les fonctions
#      d'endpoint via le mécanisme Depends(). Ici, au lieu de répéter les
#      ~35 paramètres dans chaque endpoint, on les déclare une seule fois
#      dans la classe CommonQueryParams et on l'injecte avec Depends().
#
#      Doc : https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/
#
#   2. Query() — Paramètres de query string avec validation
#      Query() permet de déclarer et valider les paramètres de query string.
#      Principaux arguments :
#        - premier argument : valeur par défaut (... = obligatoire, None = optionnel)
#        - description      : texte affiché dans la doc Swagger (/docs)
#        - min_length       : longueur minimale de la chaîne
#        - max_length       : longueur maximale de la chaîne
#        - pattern          : expression régulière de validation (Pydantic v2)
#
#      Doc : https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
#
#   3. str | None = None — Paramètre optionnel
#      En Python 3.10+, "str | None" signifie que la valeur peut être une
#      chaîne OU None. La valeur par défaut None rend le paramètre optionnel.
#      Si le client ne l'envoie pas, FastAPI injecte None automatiquement.
#
#      Doc : https://fastapi.tiangolo.com/tutorial/query-params/#optional-parameters
#
# Structure de la classe :
#   - __init__ déclare tous les paramètres avec Query()
#   - FastAPI lit la signature de __init__ pour construire les paramètres
#     de query string de l'endpoint
#   - Les attributs self.xxx sont ensuite accessibles dans l'endpoint
# =============================================================================

from fastapi import Query


class CommonQueryParams:
    """
    Paramètres de requête communs à tous les endpoints MCO.

    Regroupe :
      - Les paramètres de filtrage (annee, sexe, age, typhosp, etc.)
      - Les filtres cliniques (diag, acte, ghm, cmd, etc.)
      - Les filtres établissement (finess, categ, secteur, etc.)
      - Les paramètres géographiques (type_geo_etab, codegeo, etc.)
      - Les paramètres d'authentification (profils_niveau, id_utilisateur, etc.)
      - Le paramètre de ventilation var (commun à 6 des 8 endpoints)

    Utilisation dans un endpoint :
        from fastapi import Depends
        from app.models.params import CommonQueryParams

        @app.get("/mon-endpoint")
        def mon_endpoint(params: CommonQueryParams = Depends()):
            annee = params.annee  # valeur du query param ?annee=23
            var = params.var      # valeur du query param ?var=ghm
    """

    def __init__(
        self,
        # -------------------------------------------------------------------------
        # PARAMÈTRE OBLIGATOIRE
        # "..." signifie "sans valeur par défaut" → FastAPI retourne 422 si absent
        # -------------------------------------------------------------------------
        annee: str = Query(
            ...,
            description=(
                "Année sur 2 chiffres (ex : '23' pour 2023). **Obligatoire.** "
                "Correspond aux caractères 3-4 de l'année 4 chiffres."
            ),
            min_length=2,
            max_length=2,
            pattern=r"^\d{2}$",
        ),
        # -------------------------------------------------------------------------
        # FILTRES TEMPORELS
        # -------------------------------------------------------------------------
        moissortie: str | None = Query(
            None,
            description=(
                "Plage de mois de sortie au format 'debut_fin' (ex : '3_9'). "
                "NULL si plage complète 1_12."
            ),
        ),
        # -------------------------------------------------------------------------
        # FILTRES DÉMOGRAPHIQUES
        # -------------------------------------------------------------------------
        sexe: str | None = Query(
            None,
            description=(
                "Sexe du patient : '1' (homme) ou '2' (femme). "
                "NULL si les 2 sexes sont sélectionnés."
            ),
        ),
        age: str | None = Query(
            None,
            description=(
                "Plage d'âge au format 'min_max' (ex : '18_65'). "
                "NULL si 0_125 (plage complète)."
            ),
        ),
        # -------------------------------------------------------------------------
        # TYPE D'HOSPITALISATION
        # -------------------------------------------------------------------------
        typhosp: str | None = Query(
            None,
            description=(
                "Type(s) d'hospitalisation séparés par '_' "
                "(ex : 'M_C' pour médecine et chirurgie). "
                "NULL si >= 3 types sélectionnés (tous)."
            ),
        ),
        # -------------------------------------------------------------------------
        # FILTRES CLINIQUES — DIAGNOSTIC
        # -------------------------------------------------------------------------
        diag: str | None = Query(
            None,
            description="Codes CIM-10 de diagnostic à filtrer, joints par '_'.",
        ),
        diag_pos: str | None = Query(
            None,
            description=(
                "Position du diagnostic : 'DP' (principal), "
                "'DR' (relié) ou 'DA' (associé)."
            ),
        ),
        # -------------------------------------------------------------------------
        # FILTRES CLINIQUES — ACTES
        # -------------------------------------------------------------------------
        acte: str | None = Query(
            None,
            description=(
                "Codes CCAM à filtrer (7 ou 9 caractères), joints par '_'. "
                "Extension PMSI 'NA' est tronquée à 7 caractères."
            ),
        ),
        exclu_acte: str | None = Query(
            None,
            description="Codes CCAM à exclure, joints par '_'.",
        ),
        and_acte: str | None = Query(
            None,
            description=(
                "Opérateur logique sur les actes inclus : "
                "'0' = OU logique, '1' = ET logique."
            ),
        ),
        and_exclu_acte: str | None = Query(
            None,
            description=(
                "Opérateur logique sur les actes exclus : "
                "'0' = OU logique, '1' = ET logique."
            ),
        ),
        # -------------------------------------------------------------------------
        # FILTRES ÉTABLISSEMENT
        # -------------------------------------------------------------------------
        um: str | None = Query(
            None,
            description="Codes d'unité médicale à filtrer, joints par '_'.",
        ),
        finess: str | None = Query(
            None,
            description="Codes FINESS PMSI à filtrer (9 chiffres), joints par '_'.",
        ),
        finessgeo: str | None = Query(
            None,
            description="Codes FINESS géographiques à filtrer, joints par '_'.",
        ),
        categ: str | None = Query(
            None,
            description="Codes catégorie d'établissement à filtrer, joints par '_'.",
        ),
        secteur: str | None = Query(
            None,
            description=(
                "Codes secteur de financement à filtrer, joints par '_' "
                "(ex : 'PU' pour public, 'PR' pour privé)."
            ),
        ),
        # -------------------------------------------------------------------------
        # MODES D'ENTRÉE ET DE SORTIE
        # -------------------------------------------------------------------------
        modeentree: str | None = Query(
            None,
            description="Codes mode d'entrée à filtrer, joints par '_'.",
        ),
        modesortie: str | None = Query(
            None,
            description="Codes mode de sortie à filtrer, joints par '_'.",
        ),
        provenance: str | None = Query(
            None,
            description="Codes provenance à filtrer, joints par '_'.",
        ),
        destination: str | None = Query(
            None,
            description="Codes destination à filtrer, joints par '_'.",
        ),
        passageurg: str | None = Query(
            None,
            description="Passage par les urgences à filtrer, joints par '_'.",
        ),
        # -------------------------------------------------------------------------
        # GÉOGRAPHIE ÉTABLISSEMENT
        # -------------------------------------------------------------------------
        type_geo_etab: str | None = Query(
            None,
            description=(
                "Type géographique de localisation de l'établissement : "
                "'reg' (région), 'dep' (département), etc."
            ),
        ),
        codes_geo_etab: str | None = Query(
            None,
            description="Codes géographiques de l'établissement, joints par '_'.",
        ),
        # -------------------------------------------------------------------------
        # GÉOGRAPHIE PATIENT
        # -------------------------------------------------------------------------
        codegeo: str | None = Query(
            None,
            description="Codes géographiques de domiciliation du patient, joints par '_'.",
        ),
        type_geo_pat: str | None = Query(
            None,
            description=(
                "Type géographique du domicile patient : "
                "'reg' (région), 'dep' (département), etc."
            ),
        ),
        codes_geo_pat: str | None = Query(
            None,
            description="Codes géographiques du domicile patient, joints par '_'.",
        ),
        # -------------------------------------------------------------------------
        # FILTRES MÉDICAMENTS ET DISPOSITIFS MÉDICAUX
        # -------------------------------------------------------------------------
        code_lpp: str | None = Query(
            None,
            description="Codes LPP (dispositifs médicaux implantables), joints par '_'.",
        ),
        code_ucd: str | None = Query(
            None,
            description="Codes UCD (médicaments), joints par '_'.",
        ),
        # -------------------------------------------------------------------------
        # FILTRES DE CASEMIX — paramètres {filtre} dynamiques de la spec
        # Ces paramètres permettent de filtrer par classification PMSI.
        # -------------------------------------------------------------------------
        ghm: str | None = Query(
            None,
            description=(
                "Codes GHM à filtrer, joints par '_' "
                "(ex : '05M09T_05K06T'). Format 6 caractères."
            ),
        ),
        racine: str | None = Query(
            None,
            description=(
                "Codes racine GHM à filtrer, joints par '_' "
                "(ex : '05M09'). Format 5 caractères."
            ),
        ),
        cmd: str | None = Query(
            None,
            description=(
                "Codes CMD (Catégorie Majeure de Diagnostic) à filtrer, "
                "joints par '_' (ex : '05_06')."
            ),
        ),
        dp: str | None = Query(
            None,
            description="Codes CIM-10 de diagnostic principal à filtrer, joints par '_'.",
        ),
        da: str | None = Query(
            None,
            description="Codes domaine d'activité à filtrer, joints par '_'.",
        ),
        ga: str | None = Query(
            None,
            description="Codes groupe d'activité à filtrer, joints par '_'.",
        ),
        gp: str | None = Query(
            None,
            description="Codes groupe de planification à filtrer, joints par '_'.",
        ),
        aso: str | None = Query(
            None,
            description="Codes activité de soins à filtrer, joints par '_'.",
        ),
        cas: str | None = Query(
            None,
            description="Codes catégorie d'activité de soins à filtrer, joints par '_'.",
        ),
        # -------------------------------------------------------------------------
        # PARAMÈTRES D'AUTHENTIFICATION
        # Ces paramètres sont transmis par le client R à chaque requête pour
        # l'identification et le traçage. Le mock les accepte mais ne les utilise pas.
        # -------------------------------------------------------------------------
        profils_niveau: str | None = Query(
            None,
            description=(
                "Niveau du profil utilisateur : 'ETABLISSEMENT', "
                "'ETABLISSEMENT G', 'STRUCTURE_ADMINISTRATIVE', ou '' (dev)."
            ),
        ),
        profils_entite: str | None = Query(
            None,
            description="Code entité du profil : 'ATIH', 'DGOS', etc. (ou '' en dev).",
        ),
        id_utilisateur: str | None = Query(
            None,
            description="Identifiant Plage de l'utilisateur ('test' en développement).",
        ),
        token_utilisateur: str | None = Query(
            None,
            description="Token OAuth2 PASREL (chaîne vide en développement).",
        ),
        refus_cookie: str | None = Query(
            None,
            description="Refus des cookies analytiques : 'TRUE' ou 'FALSE'.",
        ),
        # -------------------------------------------------------------------------
        # PARAMÈTRE DE VENTILATION
        # Commun à 6 des 8 endpoints (absent de /tx_recours et /dernier_trans).
        # Contrôle les colonnes de regroupement dans la réponse JSON.
        # -------------------------------------------------------------------------
        var: str | None = Query(
            None,
            description=(
                "Variable(s) de ventilation séparées par '_' "
                "(ex : 'ghm', 'sexe_trancheage', 'mois', 'ghm_typhosp'). "
                "Chaque variable ajoute une ou plusieurs colonnes de groupement "
                "à la réponse. Voir la spec §4 pour la liste complète."
            ),
        ),
    ):
        # --- Paramètre obligatoire ---
        self.annee = annee

        # --- Filtres temporels ---
        self.moissortie = moissortie

        # --- Filtres démographiques ---
        self.sexe = sexe
        self.age = age

        # --- Type d'hospitalisation ---
        self.typhosp = typhosp

        # --- Filtres cliniques ---
        self.diag = diag
        self.diag_pos = diag_pos
        self.acte = acte
        self.exclu_acte = exclu_acte
        self.and_acte = and_acte
        self.and_exclu_acte = and_exclu_acte

        # --- Filtres établissement ---
        self.um = um
        self.finess = finess
        self.finessgeo = finessgeo
        self.categ = categ
        self.secteur = secteur

        # --- Modes d'entrée / sortie ---
        self.modeentree = modeentree
        self.modesortie = modesortie
        self.provenance = provenance
        self.destination = destination
        self.passageurg = passageurg

        # --- Géographie établissement ---
        self.type_geo_etab = type_geo_etab
        self.codes_geo_etab = codes_geo_etab

        # --- Géographie patient ---
        self.codegeo = codegeo
        self.type_geo_pat = type_geo_pat
        self.codes_geo_pat = codes_geo_pat

        # --- Médicaments / dispositifs ---
        self.code_lpp = code_lpp
        self.code_ucd = code_ucd

        # --- Filtres de casemix ---
        self.ghm = ghm
        self.racine = racine
        self.cmd = cmd
        self.dp = dp
        self.da = da
        self.ga = ga
        self.gp = gp
        self.aso = aso
        self.cas = cas

        # --- Authentification ---
        self.profils_niveau = profils_niveau
        self.profils_entite = profils_entite
        self.id_utilisateur = id_utilisateur
        self.token_utilisateur = token_utilisateur
        self.refus_cookie = refus_cookie

        # --- Ventilation ---
        self.var = var
