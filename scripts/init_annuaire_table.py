import pandas as pd
from sqlalchemy import create_engine, text
import os
import re
from datetime import datetime

# Constants
USERNAME = "khoa"
PASSWORD = "k123"
DATABASE = "cassis_ia"
HOST = "localhost"
PORT = "5432"
XLSX_FILE = "data/sample_annuaire.xlsx"

# SQL queries
CHECK_CASSIS_IA_DB = f"""
SELECT 1 FROM pg_database WHERE datname = '{DATABASE}';
"""

CREATE_CASSIS_IA_DB = f"""
CREATE DATABASE {DATABASE};
"""

CHECK_ANNUAIRE_TABLE = f"""
SELECT EXISTS (
    SELECT FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename = 'annuaire'
);
"""

# Helper function to parse 'Horaires d’ouverture'
def parse_horaires(horaires):
    days_mapping = {
        "lu": ["lundi", "lu"],
        "ma": ["mardi", "ma"],
        "me": ["mercredi", "me"],
        "je": ["jeudi", "je"],
        "ve": ["vendredi", "ve"],
        "sa": ["samedi", "sa"],
        "di": ["dimanche", "di"]
    }

    parsed = {day: False for day in days_mapping}

    if pd.isna(horaires):
        return parsed

    horaires = horaires.lower()
    for day, patterns in days_mapping.items():
        for pattern in patterns:
            if re.search(rf"\b{pattern}\b", horaires):
                parsed[day] = True

    if re.search(r"lundi.*vendredi", horaires):
        for day in ["lu", "ma", "me", "je", "ve"]:
            parsed[day] = True

    if re.search(r"tous les jours", horaires) and not re.search(r"sauf.*week-end", horaires):
        for day in parsed:
            parsed[day] = True

    if re.search(r"sauf.*week-end", horaires):
        for day in ["sa", "di"]:
            parsed[day] = False

    return parsed

# Helper function to run a query directly in PostgreSQL
def execute_query(engine, query, success_msg, error_msg):
    try:
        with engine.connect() as connection:
            connection.execute(text(query))
        print(success_msg)
    except Exception as e:
        print(f"{error_msg}: {e}")

# Main script
def main():
    default_engine = create_engine(f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/postgres")
    with default_engine.connect() as connection:
        db_exists = connection.execute(text(CHECK_CASSIS_IA_DB)).scalar()
        if not db_exists:
            print(f"Database '{DATABASE}' does not exist. Creating...")
            connection.execute(text(CREATE_CASSIS_IA_DB))
            print(f"Database '{DATABASE}' created successfully.")
        else:
            print(f"Database '{DATABASE}' already exists.")

    engine = create_engine(f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}")

    with engine.connect() as connection:
        table_exists = connection.execute(text(CHECK_ANNUAIRE_TABLE)).scalar()
        if not table_exists:
            print("Table 'annuaire' does not exist. Creating...")
            create_table_query = """
            CREATE TABLE annuaire (
                id SERIAL PRIMARY KEY,
                no_ean VARCHAR(50),
                type VARCHAR(50),
                type_de_fournisseur VARCHAR(50),
                nom VARCHAR(100),
                prenom VARCHAR(100),
                acronyme VARCHAR(50),
                telephone VARCHAR(20),
                portable VARCHAR(20),
                courriel VARCHAR(100),
                site_web VARCHAR(100),
                lien_org TEXT,
                organisation VARCHAR(100),
                role_activite_specialite TEXT,
                medecin BOOLEAN,
                medecin_intra_hospitalier BOOLEAN,
                lu BOOLEAN,
                ma BOOLEAN,
                me BOOLEAN,
                je BOOLEAN,
                ve BOOLEAN,
                sa BOOLEAN,
                di BOOLEAN,
                tags TEXT,
                selection TEXT,
                commentaire TEXT,
                voie VARCHAR(200),
                numero VARCHAR(20),
                complement VARCHAR(100),
                npa INTEGER,
                localite VARCHAR(100),
                pays VARCHAR(50),
                coord_geo_nord VARCHAR(100),
                coord_geo_est VARCHAR(100),
                longitude VARCHAR(100),
                latitude VARCHAR(100),
                date_derniere_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            connection.execute(text(create_table_query))
            connection.commit()
            print("Table 'annuaire' created successfully.")
        else:
            print("Table 'annuaire' already exists.")

    if not os.path.exists(XLSX_FILE):
        print(f"Excel file '{XLSX_FILE}' not found. Exiting.")
        return

    print(f"Loading data from '{XLSX_FILE}'...")
    df = pd.read_excel(XLSX_FILE)

    # Exclude the 'ID' column entirely if it exists
    if 'ID' in df.columns:
        df.drop(columns=['ID'], inplace=True)

    # Translate 'Oui/Non' to Boolean for specific columns
    boolean_columns = ["Médecin", "Médecin intra-hospitalier"]
    for col in boolean_columns:
        if col in df.columns:
            df[col] = df[col].map({"Oui": True, "Non": False})

    column_mapping = {
        "No EAN": "no_ean",
        "Type": "type",
        "Type de fournisseur": "type_de_fournisseur",
        "Nom": "nom",
        "Prénom": "prenom",
        "Acronyme": "acronyme",
        "N° de téléphone": "telephone",
        "N° de portable": "portable",
        "Courriel": "courriel",
        "Site web": "site_web",
        "Lien org": "lien_org",
        "Organisation": "organisation",
        "Rôle / Activité et éventuelle(s) spécialité(s)": "role_activite_specialite",
        "Médecin": "medecin",
        "Médecin intra-hospitalier": "medecin_intra_hospitalier",
        "Tags": "tags",
        "Sélection": "selection",
        "Commentaire": "commentaire",
        "Voie": "voie",
        "Numéro": "numero",
        "Complément": "complement",
        "NPA": "npa",
        "Localité": "localite",
        "Pays": "pays",
        "Coordonnées Nord": "coord_geo_nord",
        "Coornonnées Est": "coord_geo_est",
        "Longitude": "longitude",
        "Latuitude": "latitude"
    }
    df.rename(columns=column_mapping, inplace=True)

    horaires_parsed = df['Horaires d’ouverture'].apply(parse_horaires)
    horaires_df = pd.DataFrame(list(horaires_parsed))
    df = pd.concat([df, horaires_df], axis=1)

    df.drop(columns=['Horaires d’ouverture'], inplace=True)
    # Add 'date_derniere_modification' column with default value
    df['date_derniere_modification'] = datetime.now()

    # Exclude 'id' column during insertion (auto-generated by PostgreSQL)
    try:
        df.to_sql('annuaire', engine, if_exists='append', index=False)
        print("Data successfully inserted into 'annuaire' table.")
    except Exception as e:
        print(f"Failed to insert data into 'annuaire': {e}")

if __name__ == "__main__":
    main()
