import pandas as pd
from sqlalchemy import create_engine, text
import os

# Constants
USERNAME = "khoa"
PASSWORD = "k123"
DATABASE = "cassis_ia"
HOST = "localhost"
PORT = "5432"

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

CREATE_ANNUAIRE_TABLE = """
CREATE EXTENSION IF NOT EXISTS pg_trgm;
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

INSERT_SAMPLE_ANNUAIRE_DATA = """
INSERT INTO annuaire (
    no_ean, type, type_de_fournisseur, nom, prenom, acronyme, telephone, portable,
    courriel, site_web, lien_org, organisation, role_activite_specialite, medecin,
    medecin_intra_hospitalier, lu, ma, me, je, ve, sa, di, tags, selection,
    commentaire, voie, numero, complement, npa, localite, pays,
    coord_geo_nord, coord_geo_est, longitude, latitude
) VALUES
    ('123456789', 'Médecin', 'Hôpital', 'Dupont', 'Jean', 'JD', '0123456789', '0612345678',
     'jean.dupont@example.com', 'www.hopital-example.com', 'Lien Org', 'Hôpital Central',
     'Cardiologue', TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, FALSE,
     'Urgence, Cardiologie', 'Aucune', 'Disponible en semaine', 'Rue de la Santé',
     '10', 'Bâtiment A', 1000, 'VilleX', 'France', '46.2044', '6.1432', '6.1432', '46.2044');
"""

# Helper function to run a query
def execute_query(engine, query, success_msg, error_msg):
    try:
        with engine.connect() as connection:
            connection.execute(text(query))
        print(success_msg)
    except Exception as e:
        print(f"{error_msg}: {e}")

# Main script
def main():
    # Connect to the default postgres database to check/create cassis_ia
    default_engine = create_engine(f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/postgres")
    with default_engine.connect() as connection:
        db_exists = connection.execute(text(CHECK_CASSIS_IA_DB)).scalar()
        if not db_exists:
            print(f"Database '{DATABASE}' does not exist. Creating...")
            connection.execute(text(CREATE_CASSIS_IA_DB))
            print(f"Database '{DATABASE}' created successfully.")
        else:
            print(f"Database '{DATABASE}' already exists.")

    # Connect to the cassis_ia database
    engine = create_engine(f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}")

    # Check if the 'annuaire' table exists, and create it if not
    with engine.connect() as connection:
        table_exists = connection.execute(text(CHECK_ANNUAIRE_TABLE)).scalar()
        if not table_exists:
            print("Table 'annuaire' does not exist. Creating...")
            connection.execute(text(CREATE_ANNUAIRE_TABLE))
            connection.commit()
            print("Table 'annuaire' created successfully.")
        else:
            print("Table 'annuaire' already exists.")

    # Insert sample data
    execute_query(engine, INSERT_SAMPLE_ANNUAIRE_DATA, "Sample data inserted successfully into 'annuaire'.", "Failed to insert sample data into 'annuaire'")

if __name__ == "__main__":
    main()
