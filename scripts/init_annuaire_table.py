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
    (NULL, 'Médecin', 'Clinique', 'Murceni', 'Ibrahim', 'MI', '0123456780', '0612345670',
     'ibrahim.murceni@example.com', 'www.clinique-example.com', 'Lien Org', 'Clinique Spécialisée',
     'Généraliste', TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, FALSE, FALSE, FALSE,
     'Consultation Générale', 'Aucune', 'Disponible en matinée', 'Avenue du Centre',
     '5', '', 2000, 'VilleY', 'France', '46.2055', '6.1443', '6.1443', '46.2055'),
    (NULL, 'Infirmière', 'Cabinet', 'Nicollier', 'Ludivine', 'NL', '0123456781', '0612345671',
     'ludivine.nicollier@example.com', 'www.cabinet-example.com', 'Lien Org', 'Cabinet Médical',
     'Soins infirmiers', FALSE, FALSE, TRUE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
     'Soins à domicile', 'Aucune', 'Disponible sur rendez-vous', 'Rue des Soins',
     '15', '', 3000, 'VilleZ', 'France', '46.2066', '6.1454', '6.1454', '46.2066'),
    (NULL, 'Psychologue', 'Centre', 'Sewer-Burdet', 'Laure', 'SB', '0123456782', '0612345672',
     'laure.sewer@example.com', 'www.centre-psy-example.com', 'Lien Org', 'Centre Psychologique',
     'Psychothérapie', FALSE, FALSE, TRUE, TRUE, TRUE, FALSE, FALSE, FALSE, FALSE,
     'Consultation psychologique', 'Aucune', 'Disponible l’après-midi', 'Boulevard de la Paix',
     '20', '', 4000, 'VilleA', 'France', '46.2077', '6.1465', '6.1465', '46.2077'),
    (NULL, 'Médecin', 'Hôpital', 'Di Censi', 'Andrea', 'DC', '0123456783', '0612345673',
     'andrea.dicensi@example.com', 'www.hopital-psy-example.com', 'Lien Org', 'Hôpital Psychiatrique',
     'Psychiatrie', TRUE, FALSE, TRUE, TRUE, TRUE, TRUE, FALSE, FALSE, FALSE,
     'Consultation psychiatrique', 'Aucune', 'Sur rendez-vous', 'Chemin des Médecins',
     '25', '', 5000, 'VilleB', 'France', '46.2088', '6.1476', '6.1476', '46.2088');
"""

# Helper function to run a query
def execute_query(engine, query, success_msg, error_msg):
    try:
        with engine.begin() as connection:  # Use .begin() to ensure commit
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
