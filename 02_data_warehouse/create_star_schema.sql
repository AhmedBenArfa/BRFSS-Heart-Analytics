-- ===========================================================================
-- Schéma en étoile — BRFSS Heart Analytics
--
-- Table de faits : fact_respondent (grain = un répondant à l'enquête)
-- Dimensions     : 7 dimensions reconstruites depuis le codebook BRFSS
--
-- Ce fichier est la SOURCE DE VÉRITÉ du modèle dimensionnel. Les tables de
-- dimension y sont déclarées (structure) ; leur contenu est inséré par
-- build_star_schema.py à partir de 02_data_warehouse/codebook.py, puis la
-- table de faits est peuplée par jointure sur la table analytique.
--
-- Convention des clés : chaque dimension possède une clé technique entière.
-- Ici, comme les codes source sont déjà des petits entiers contigus, la clé
-- de dimension EST le code source (pas de surrogate key artificielle). Un
-- membre spécial de clé -1 « Inconnu » capte tout code de fait absent du
-- codebook, ce qui garantit l'intégrité référentielle sans perdre de ligne.
-- ===========================================================================

-- --- Dimensions ------------------------------------------------------------
-- (structure seulement ; les lignes sont insérées par le script Python)

CREATE OR REPLACE TABLE dim_age (
    age_key      INTEGER PRIMARY KEY,
    tranche_age  VARCHAR NOT NULL
);

CREATE OR REPLACE TABLE dim_education (
    education_key     INTEGER PRIMARY KEY,
    niveau_education  VARCHAR NOT NULL
);

CREATE OR REPLACE TABLE dim_income (
    income_key       INTEGER PRIMARY KEY,
    tranche_revenu   VARCHAR NOT NULL
);

CREATE OR REPLACE TABLE dim_sex (
    sex_key  INTEGER PRIMARY KEY,
    sexe     VARCHAR NOT NULL
);

CREATE OR REPLACE TABLE dim_genhlth (
    genhlth_key      INTEGER PRIMARY KEY,
    sante_generale   VARCHAR NOT NULL
);

CREATE OR REPLACE TABLE dim_diabetes (
    diabetes_key    INTEGER PRIMARY KEY,
    statut_diabete  VARCHAR NOT NULL
);

CREATE OR REPLACE TABLE dim_bmi_class (
    bmi_class_key  INTEGER PRIMARY KEY,
    classe_imc     VARCHAR NOT NULL
);

-- --- Table de faits --------------------------------------------------------
-- Construite par jointure entre analytical_base et les dimensions.
-- COALESCE(..., -1) rattache au membre « Inconnu » tout code sans
-- correspondance dans le codebook, préservant l'intégrité référentielle.

CREATE OR REPLACE TABLE fact_respondent AS
SELECT
    ab.respondent_id,

    -- Clés étrangères vers les dimensions
    COALESCE(da.age_key,       -1) AS age_key,
    COALESCE(de.education_key, -1) AS education_key,
    COALESCE(di.income_key,    -1) AS income_key,
    COALESCE(ds.sex_key,       -1) AS sex_key,
    COALESCE(dg.genhlth_key,   -1) AS genhlth_key,
    COALESCE(dd.diabetes_key,  -1) AS diabetes_key,
    COALESCE(db.bmi_class_key, -1) AS bmi_class_key,

    -- Mesures continues
    ab.bmi,
    ab.ment_hlth_days,
    ab.phys_hlth_days,
    ab.total_unhealthy_days,

    -- Indicateurs binaires (conditions et comportements)
    ab.high_bp,
    ab.high_chol,
    ab.chol_check,
    ab.smoker,
    ab.stroke,
    ab.phys_activity,
    ab.fruits,
    ab.veggies,
    ab.hvy_alcohol,
    ab.any_healthcare,
    ab.no_doc_cost,
    ab.diff_walk,

    -- Variables dérivées d'agrégation
    ab.risk_factor_count,
    ab.healthy_habits_count,
    ab.has_care_access,

    -- Drapeaux qualité
    ab.flag_bmi_extreme,
    ab.flag_profil_duplique,
    ab.flag_sante_incoherente,

    -- Variable cible
    ab.heart_disease
FROM analytical_base AS ab
LEFT JOIN dim_age       AS da ON ab.age_group = da.age_key
LEFT JOIN dim_education AS de ON ab.education  = de.education_key
LEFT JOIN dim_income    AS di ON ab.income     = di.income_key
LEFT JOIN dim_sex       AS ds ON ab.sex        = ds.sex_key
LEFT JOIN dim_genhlth   AS dg ON ab.gen_hlth   = dg.genhlth_key
LEFT JOIN dim_diabetes  AS dd ON ab.diabetes   = dd.diabetes_key
LEFT JOIN dim_bmi_class AS db ON ab.bmi_class  = db.bmi_class_key;
