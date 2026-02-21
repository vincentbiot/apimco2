# =============================================================================
# app/models/responses.py — Modèles Pydantic pour les réponses des endpoints
#
# Concepts FastAPI / Pydantic introduits dans cette étape :
#
#   1. BaseModel (Pydantic)
#      Classe de base pour tous les modèles de données. En héritant de
#      BaseModel, on obtient automatiquement :
#        - La validation des types à la création (ex : "abc" dans un champ int → erreur)
#        - La sérialisation JSON (model.model_dump())
#        - La génération du schéma JSON Schema (utilisé par Swagger)
#
#      Doc : https://fastapi.tiangolo.com/tutorial/body/#create-your-data-model
#      Doc Pydantic : https://docs.pydantic.dev/latest/concepts/models/
#
#   2. ConfigDict(extra='allow')
#      Par défaut, Pydantic v2 ignore les champs non déclarés dans un modèle.
#      Avec extra='allow', les champs supplémentaires sont acceptés et conservés.
#      C'est essentiel ici car les colonnes de ventilation (var=ghm, var=mois, etc.)
#      sont dynamiques : on ne peut pas les déclarer statiquement dans le modèle.
#
#      Doc : https://docs.pydantic.dev/latest/concepts/models/#extra-fields
#
#   3. response_model dans @app.get()
#      Quand on déclare response_model=list[ResumeRow], FastAPI :
#        - Valide que la réponse de la fonction correspond au modèle
#        - Filtre les champs non déclarés (sauf avec extra='allow')
#        - Génère le schéma de réponse dans la doc Swagger
#
#      Doc : https://fastapi.tiangolo.com/tutorial/response-model/
#
#   4. float | None = None — Champ optionnel
#      Indique qu'un champ peut être un float ou None (absent).
#      La valeur par défaut None signifie que le champ n'est pas obligatoire
#      dans la réponse (par exemple duree_moy_sej peut être absent selon la spec §5.4).
#
#   5. int | str — Union de types
#      Utilisé pour nb_pat dans ResumeRow : peut être un entier OU la chaîne
#      "petit_effectif" (protection du secret statistique, spec §5.2).
#
# Architecture :
#   - BaseRow        : colonnes communes à la plupart des endpoints
#   - ResumeRow      : /resume
#   - ResumePrecAnneeRow : /resume_prec_annee
#   - DiagAssocRow   : /diag_assoc
#   - UmRow          : /um
#   - DmiMedRow      : /dmi_med
#   - ActesRow       : /actes
#   - TxRecoursRow   : /tx_recours
#   - DernierTransRow : /dernier_trans
# =============================================================================

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# CLASSE DE BASE — colonnes communes à la plupart des endpoints
# =============================================================================

class BaseRow(BaseModel):
    """
    Colonnes statistiques de base communes aux endpoints MCO principaux.

    Toutes les colonnes numériques sont présentes dans la réponse standard.
    L'option extra='allow' permet d'accepter les colonnes de ventilation
    dynamiques ajoutées selon le paramètre `var` (ex : 'ghm', 'mois', 'sexe').

    Exemple avec var=ghm : chaque ligne aura aussi un champ "ghm": "05M09T".
    Ce champ n'est pas déclaré ici mais sera conservé grâce à extra='allow'.
    """

    # extra='allow' : accepte les champs non déclarés (colonnes de ventilation var)
    model_config = ConfigDict(extra="allow")

    nb_sej: int = Field(description="Nombre de séjours MCO.")
    # duree_moy_sej peut être absente selon la spec §5.4 — le client ajoute "0" via verif_data()
    duree_moy_sej: float | None = Field(
        default=None,
        description="Durée moyenne de séjour en jours. Peut être absente.",
    )
    tx_dc: float = Field(description="Taux de décès (entre 0 et 1).")
    tx_male: float = Field(description="Taux de patients masculins (entre 0 et 1).")
    age_moy: float = Field(description="Âge moyen des patients en années.")


# =============================================================================
# ENDPOINT : GET /resume
# =============================================================================

class ResumeRow(BaseRow):
    """
    Ligne de réponse de l'endpoint GET /resume.

    Hérite de BaseRow et ajoute nb_pat qui peut contenir :
      - un entier (nombre de patients)
      - la chaîne "petit_effectif" (protection du secret statistique, spec §5.2)
      - None si non demandé (bool_nb_pat non fourni et pas de var)

    Les colonnes de ventilation (ghm, mois, sexe, trancheage...) sont ajoutées
    dynamiquement grâce à extra='allow' hérité de BaseRow.
    """

    # nb_pat : int OU "petit_effectif" OU absent — d'où le type int | str | None
    nb_pat: int | str | None = Field(
        default=None,
        description=(
            "Nombre de patients. "
            "Retourné si bool_nb_pat=TRUE ou si var est fourni. "
            "Peut contenir 'petit_effectif' si effectif < 10 séjours (spec §5.2 méthode A)."
        ),
    )


# =============================================================================
# ENDPOINT : GET /resume_prec_annee
# =============================================================================

class ResumePrecAnneeRow(BaseRow):
    """
    Ligne de réponse de l'endpoint GET /resume_prec_annee.

    Retourne les agrégats sur plusieurs années consécutives pour l'analyse
    multi-annuelle. La colonne `annee` est en format 4 chiffres (contrairement
    au paramètre de requête `annee` envoyé en 2 chiffres).
    """

    annee: int = Field(
        description="Année PMSI sur 4 chiffres (ex : 2023).",
    )
    nb_pat: int = Field(
        description="Nombre de patients (toujours présent pour cet endpoint).",
    )


# =============================================================================
# ENDPOINT : GET /diag_assoc
# =============================================================================

class DiagAssocRow(BaseRow):
    """
    Ligne de réponse de l'endpoint GET /diag_assoc.

    Retourne les diagnostics associés significatifs (DAS) des séjours.
    La colonne code_diag est renommée en 'diag' côté client R dans call_api_and_unwrap().
    """

    code_diag: str = Field(
        description=(
            "Code CIM-10 du diagnostic associé (DAS). "
            "Renommé en 'diag' par le client R."
        ),
    )
    # dr (diagnostic relié) est optionnel — présent seulement si "dr" est dans var
    dr: str | None = Field(
        default=None,
        description="Code CIM-10 du diagnostic relié. Présent si 'dr' est dans le paramètre var.",
    )


# =============================================================================
# ENDPOINT : GET /um
# =============================================================================

class UmRow(BaseRow):
    """
    Ligne de réponse de l'endpoint GET /um.

    Retourne les données par type d'unité médicale (UM).
    La colonne code_rum est renommée en 'um' côté client R.
    """

    code_rum: str = Field(
        description=(
            "Code du type d'unité médicale (ex : '01', '13'). "
            "Renommé en 'um' par le client R."
        ),
    )
    duree_moy_rum: float = Field(
        description="Durée moyenne de séjour au niveau RUM (sous-séjour par unité médicale).",
    )
    # dr optionnel — présent seulement si "dr" est dans var
    dr: str | None = Field(
        default=None,
        description="Code CIM-10 du diagnostic relié. Présent si 'dr' est dans le paramètre var.",
    )


# =============================================================================
# ENDPOINT : GET /dmi_med
# =============================================================================

class DmiMedRow(BaseModel):
    """
    Ligne de réponse de l'endpoint GET /dmi_med.

    Retourne les données de valorisation des médicaments (UCD) et des
    dispositifs médicaux implantables (DMI/LPP). La colonne 'datasource'
    permet de distinguer les deux types de produits.

    Structure asymétrique :
      - Si datasource='med' : code_ucd, lib_ucd, atc1..atc5 sont renseignés ;
                              code_lpp, hiera, hiera_libelle sont null.
      - Si datasource='dmi' : code_lpp, hiera, hiera_libelle sont renseignés ;
                              code_ucd, lib_ucd, atc1..atc5 sont null.
    """

    model_config = ConfigDict(extra="allow")

    datasource: str = Field(
        description="Source des données : 'med' (médicaments) ou 'dmi' (DMI/LPP).",
    )
    code: str = Field(
        description="Code produit : code UCD pour les médicaments, code LPP pour les DMI.",
    )
    nb: int = Field(description="Nombre d'unités administrées (méd.) ou posées (DMI).")
    nb_sej: int = Field(description="Nombre de séjours concernés.")
    nb_pat: int = Field(description="Nombre de patients concernés.")
    mnt_remb: float = Field(description="Montant remboursé en euros.")
    duree_moy_sej: float = Field(description="Durée moyenne de séjour en jours.")
    age_moy: float = Field(description="Âge moyen des patients.")

    # --- Colonnes spécifiques médicaments (UCD) ---
    code_ucd: str | None = Field(
        default=None,
        description="Code UCD du médicament. Null pour les DMI.",
    )
    lib_ucd: str | None = Field(
        default=None,
        description="Libellé UCD du médicament. Null pour les DMI.",
    )
    # Hiérarchie ATC (Anatomical Therapeutic Chemical classification)
    atc1: str | None = Field(default=None, description="Classe ATC niveau 1 (ex : 'L' pour antinéoplasiques).")
    atc2: str | None = Field(default=None, description="Classe ATC niveau 2 (ex : 'L01').")
    atc3: str | None = Field(default=None, description="Classe ATC niveau 3 (ex : 'L01F').")
    atc4: str | None = Field(default=None, description="Classe ATC niveau 4 (ex : 'L01FG').")
    atc5: str | None = Field(default=None, description="Classe ATC niveau 5 — code molécule (ex : 'L01FG01').")

    # --- Colonnes spécifiques dispositifs médicaux (LPP) ---
    code_lpp: str | None = Field(
        default=None,
        description="Code LPP du dispositif médical. Null pour les médicaments.",
    )
    hiera: str | None = Field(
        default=None,
        description="Code hiérarchie LPP (ex : '04' pour implants articulaires). Null pour les médicaments.",
    )
    hiera_libelle: str | None = Field(
        default=None,
        description="Libellé de la hiérarchie LPP. Null pour les médicaments.",
    )


# =============================================================================
# ENDPOINT : GET /actes
# =============================================================================

class ActesRow(BaseModel):
    """
    Ligne de réponse de l'endpoint GET /actes.

    Retourne les actes CCAM des séjours du périmètre. Notez l'absence de
    tx_dc et nb_pat par rapport à BaseRow — cet endpoint a un schéma propre.
    """

    model_config = ConfigDict(extra="allow")

    code_ccam: str = Field(
        description="Code CCAM de l'acte (7 caractères, ex : 'DZQM006').",
    )
    extension_pmsi: str = Field(
        description="Extension PMSI de l'acte CCAM (ex : '0', '1').",
    )
    nb_acte: int = Field(description="Nombre d'actes réalisés.")
    nb_sej: int = Field(description="Nombre de séjours ayant cet acte.")
    # duree_moy_sej peut être absente — le client appelle verif_data(result, "duree_moy_sej")
    duree_moy_sej: float | None = Field(
        default=None,
        description="Durée moyenne de séjour en jours. Peut être absente.",
    )
    tx_male: float = Field(description="Taux de patients masculins (entre 0 et 1).")
    age_moy: float = Field(description="Âge moyen des patients.")
    acte_activ: str = Field(
        description="Niveau d'activité de l'acte CCAM (valeurs : '1' à '5').",
    )
    is_classant: int = Field(
        description="Acte classant (1) ou non classant (0).",
    )
    # dr optionnel — présent seulement si "dr" est dans var
    dr: str | None = Field(
        default=None,
        description="Code CIM-10 du diagnostic relié. Présent si 'dr' est dans le paramètre var.",
    )


# =============================================================================
# ENDPOINT : GET /tx_recours
# =============================================================================

class TxRecoursRow(BaseModel):
    """
    Ligne de réponse de l'endpoint GET /tx_recours.

    Retourne les taux de recours géographiques exprimés pour 1000 habitants.
    Cet endpoint n'a pas de paramètre var — le niveau géographique est contrôlé
    par le paramètre spécifique type_geo_tx_recours.
    """

    model_config = ConfigDict(extra="allow")

    typ_geo: str = Field(
        description=(
            "Type géographique de la zone : "
            "'dep' (département), 'reg' (région), 'zon' (zone), 'ts' (territoire santé), 'geo'."
        ),
    )
    code: str = Field(
        description="Code géographique de la zone (ex : '75' pour Paris, '11' pour IDF).",
    )
    nb_sej: int = Field(description="Nombre de séjours dans cette zone.")
    nb_pat: int = Field(description="Nombre de patients dans cette zone.")
    nb_pop: int = Field(description="Population de la zone géographique (habitants).")
    tx_recours_brut_sej: float = Field(
        description="Taux de recours brut en séjours pour 1000 habitants.",
    )
    tx_recours_brut_pat: float = Field(
        description="Taux de recours brut en patients pour 1000 habitants.",
    )
    tx_recours_standard_sej: float = Field(
        description="Taux de recours standardisé en séjours pour 1000 habitants.",
    )
    tx_recours_standard_pat: float = Field(
        description="Taux de recours standardisé en patients pour 1000 habitants.",
    )


# =============================================================================
# ENDPOINT : GET /dernier_trans
# =============================================================================

class DernierTransRow(BaseModel):
    """
    Ligne de réponse de l'endpoint GET /dernier_trans.

    Retourne la date de dernière transmission PMSI par établissement.
    Cet endpoint :
      - N'utilise pas le paramètre var
      - Est exempt du contrôle petit_effectif (données administratives)
      - La colonne 'annee' est supprimée côté client avant affichage
    """

    annee: int = Field(
        description="Année PMSI sur 4 chiffres (supprimée à l'affichage côté client).",
    )
    finess: str = Field(
        description="Code FINESS PMSI de l'établissement (9 chiffres).",
    )
    rs: str = Field(
        description="Raison sociale de l'établissement.",
    )
    secteur: str = Field(
        description="Secteur de financement : 'PU' (public) ou 'PR' (privé).",
    )
    categ: str = Field(
        description="Catégorie d'établissement (ex : 'CH', 'CL').",
    )
    derniere_transmission: str = Field(
        description="Date de dernière transmission PMSI au format 'YYYY-MM-DD'.",
    )
