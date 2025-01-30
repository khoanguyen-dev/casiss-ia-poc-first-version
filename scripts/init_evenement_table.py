import pandas as pd
from sqlalchemy import create_engine, text
import os

# Constants
USERNAME = "khoa"
PASSWORD = "k123"
DATABASE = "cassis_ia"
HOST = "localhost"
PORT = "5432"
CSV_FILE = "data/sample_evenement.csv"

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
CREATE TABLE evenement (
    id SERIAL PRIMARY KEY,
    nom_evenement VARCHAR(200),
    titre_evenement VARCHAR(200),
    horaire_debut TIMESTAMP,
    horaire_fin TIMESTAMP,
    date_debut DATE DEFAULT NULL;
    date_fin DATE DEFAULT NULL;
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

    # Load CSV data into a DataFrame
    if not os.path.exists(CSV_FILE):
        print(f"CSV file '{CSV_FILE}' not found. Exiting.")
        return

    print(f"Loading data from '{CSV_FILE}'...")
    df = pd.read_csv(CSV_FILE)

    # Exclude the 'ID' column entirely if it exists
    if 'ID' in df.columns:
        df.drop(columns=['ID'], inplace=True)

    # Column mapping
    column_mapping = {
        "Nom événement": "nom_evenement",
        "Titre de l'événement": "titre_evenement",
        "Date de début": "date_debut",
        "Date de fin": "date_fin",
        "Horaire début": "horaire_debut",
        "Horaire fin": "horaire_fin",
        "Texte libre": "texte_libre",
        "Court descriptif": "court_descriptif",
        "Numéro partenaire": "numero_partenaire",
        "Nom partenaire (organisateur)": "nom_partenaire",
        "Partenaire de la sélection": "partenaire_de_la_selection",
        "Sites originaux": "sites_originaux",
        "Date de création": "date_creation",
        "Mode de création": "mode_creation",
        "Date de dernière modification": "date_derniere_modification",
        "Mode de modification": "mode_modification",
        "Id dernier modificateur": "id_dernier_modificateur",
        "Date de péremption": "date_de_peremption"
    }

    # Apply the mapping
    df.rename(columns=column_mapping, inplace=True)

    # Insert data into the 'evenement' table
    try:
        df.to_sql('evenement', engine, if_exists='append', index=False)
        print(f"Data successfully inserted into 'evenement' table.")
    except Exception as e:
        print(f"Failed to insert data into 'evenement': {e}")

if __name__ == "__main__":
    main()
    