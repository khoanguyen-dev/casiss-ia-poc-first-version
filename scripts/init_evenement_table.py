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

CHECK_EVENEMENT_TABLE = f"""
SELECT EXISTS (
    SELECT FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename = 'evenement'
);
"""

CREATE_EVENEMENT_TABLE = """
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE TABLE evenement (
    id SERIAL PRIMARY KEY,
    nom_evenement VARCHAR(200),
    titre_evenement VARCHAR(200),
    horaire_debut TIMESTAMP,
    horaire_fin TIMESTAMP,
    date_debut DATE GENERATED ALWAYS AS (CASE WHEN horaire_debut IS NOT NULL THEN horaire_debut::DATE ELSE NULL END) STORED,
    date_fin DATE GENERATED ALWAYS AS (CASE WHEN horaire_fin IS NOT NULL THEN horaire_fin::DATE ELSE NULL END) STORED,
    texte_libre TEXT,
    court_descriptif TEXT,
    numero_partenaire INTEGER,
    nom_partenaire VARCHAR(200),
    partenaire_de_la_selection TEXT,
    sites_originaux TEXT,
    date_creation DATE DEFAULT CURRENT_DATE,
    mode_creation VARCHAR(50),
    date_derniere_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode_modification VARCHAR(50),
    id_dernier_modificateur INTEGER,
    date_de_peremption TIMESTAMP
);
"""

INSERT_SAMPLE_DATA = """
INSERT INTO evenement (
    nom_evenement, titre_evenement, horaire_debut, horaire_fin, texte_libre,
    court_descriptif, numero_partenaire, nom_partenaire, partenaire_de_la_selection,
    sites_originaux, mode_creation, mode_modification, id_dernier_modificateur,
    date_de_peremption
) VALUES
    ('Festival du Jazz', 'Soirée d''ouverture', '2025-06-10 18:00:00', '2025-06-10 23:00:00',
     'Une soirée inoubliable avec les plus grands musiciens de jazz.',
     'Cérémonie d''ouverture avec invités spéciaux.', 101, 'Jazz Club International',
     'Sélection Officielle', 'www.jazzfestival.com', 'Automatique', 'Manuel', 1,
     '2025-06-15 23:59:59'),
    ('Conférence AI', 'Keynote sur l''intelligence artificielle', '2025-09-15 09:00:00', '2025-09-15 12:00:00',
     'Discussion sur les dernières avancées en IA avec des experts mondiaux.',
     'Présentations et discussions sur l''éthique et les applications de l''IA.',
     202, 'Tech Innovators', 'Hors Sélection', 'www.aiconf.com', 'Automatique', 'Automatique', 2,
     '2025-09-20 23:59:59');
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

    # Check if the 'evenement' table exists, and create it if not
    with engine.connect() as connection:
        table_exists = connection.execute(text(CHECK_EVENEMENT_TABLE)).scalar()
        if not table_exists:
            print("Table 'evenement' does not exist. Creating...")
            connection.execute(text(CREATE_EVENEMENT_TABLE))
            connection.commit()
            print("Table 'evenement' created successfully.")
        else:
            print("Table 'evenement' already exists.")

    # Insert sample data
    execute_query(engine, INSERT_SAMPLE_DATA, "Sample data inserted successfully.", "Failed to insert sample data")

if __name__ == "__main__":
    main()
    