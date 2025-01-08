from flask import Flask, request, jsonify, stream_with_context, Response
from flask_cors import CORS
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from llama_index.llms.openai import OpenAI
from llama_index.program.openai import OpenAIPydanticProgram
from typing import List, Optional
from datetime import datetime
import os
import psycopg2
import pandas as pd
import validators
from threading import Lock
import json
from rapidfuzz import fuzz

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Limit the number of entries processed
MAX_ENTRIES = 5
processing_lock = Lock()  # Prevent concurrent updates

# Initialize the LlamaIndex LLM
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in environment variables.")

llm = OpenAI(model="gpt-3.5-turbo", api_key=openai_api_key)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

# Define Pydantic models for structured data with descriptions
from pydantic import BaseModel
from typing import Optional

class AnnuaireEntry(BaseModel):
    """Model representing an entry for the Annuaire database."""
    id: Optional[int] = None
    no_ean: Optional[str] = None
    type: Optional[str] = None
    type_de_fournisseur: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    acronyme: Optional[str] = None
    telephone: Optional[str] = None
    portable: Optional[str] = None
    courriel: Optional[str] = None
    site_web: Optional[str] = None
    lien_org: Optional[str] = None
    organisation: Optional[str] = None
    role_activite_specialite: Optional[str] = None
    medecin: Optional[bool] = None
    medecin_intra_hospitalier: Optional[bool] = None
    lu: Optional[bool] = None
    ma: Optional[bool] = None
    me: Optional[bool] = None
    je: Optional[bool] = None
    ve: Optional[bool] = None
    sa: Optional[bool] = None
    di: Optional[bool] = None
    tags: Optional[str] = None
    selection: Optional[str] = None
    commentaire: Optional[str] = None
    voie: Optional[str] = None
    numero: Optional[str] = None
    complement: Optional[str] = None
    npa: Optional[int] = None
    localite: Optional[str] = None
    pays: Optional[str] = None
    coord_geo_nord: Optional[float] = None
    coord_geo_est: Optional[float] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    class Config:
        from_attributes = True

class EvenementEntry(BaseModel):
    """Model representing an entry for the Evenement database."""
    numero: Optional[int]
    nom_evenement: str
    titre_evenement: Optional[str]
    date_debut: Optional[str]
    date_fin: Optional[str]
    horaire_debut: Optional[str]
    horaire_fin: Optional[str]
    texte_libre: Optional[str]
    court_descriptif: Optional[str]
    numero_partenaire: Optional[int]
    nom_partenaire: Optional[str]
    partenaire_de_la_selection: Optional[str]
    sites_originaux: Optional[str]
    date_creation: Optional[str]
    mode_creation: Optional[str]
    date_derniere_modification: Optional[str]
    mode_modification: Optional[str]
    id_dernier_modificateur: Optional[str]
    date_de_peremption: Optional[str]

class AnnuaireEntries(BaseModel):
    """Model representing multiple entries for the Annuaire database."""
    entries: List[AnnuaireEntry]

class EvenementEntries(BaseModel):
    """Model representing multiple entries for the Evenement database."""
    entries: List[EvenementEntry]

# Define Pydantic programs
annuaire_program = OpenAIPydanticProgram.from_defaults(
    output_cls=AnnuaireEntries,
    llm=llm,
    prompt_template_str="""
        Extract structured data for AnnuaireEntries from the following text:
        {text_input}

        For each entry:
        - Parse the name into `prenom` and `nom` if possible. Note that `Dre` and `Dr` are title, not part of name.
        - Parse hours into fields for `lu`, `ma`, `me`, `je`, `ve`, `sa`, `di` with `True` for open and `False` for closed.
        - Include all other fields as provided.
    """,
    verbose=True
)

evenement_program = OpenAIPydanticProgram.from_defaults(
    output_cls=EvenementEntries,
    llm=llm,
    prompt_template_str="Extract structured data for EvenementEntries from the following text: {text_input}",
    verbose=True
)

@app.route('/annuaire', methods=['GET'])
def get_annuaire():
    return fetch_table_entries("annuaire")

@app.route('/evenements', methods=['GET'])
def get_evenement_entries():
    return fetch_table_entries("evenement")

def fetch_table_entries(table_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        conn.close()
        return jsonify([dict(zip(column_names, row)) for row in rows])
    except Exception as e:
        print("Error occurred while fetching table entries:")
        print(e)  # Log the error for debugging
        return jsonify({'error': str(e)}), 500

def scrape_content(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Visit the page
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")  # Ensure basic page content is loaded

            # Optional: Click toggles/buttons to reveal hidden content
            try:
                # Adjust this selector to match elements that toggle hidden content
                toggles = page.query_selector_all("button, .toggle, [data-toggle]")
                for toggle in toggles:
                    if toggle.is_visible():  # Only click visible elements
                        toggle.click()
                        page.wait_for_timeout(100)  # Small delay for DOM updates
            except Exception as toggle_error:
                print(f"Error clicking toggles: {toggle_error}")

            # Wait for the main content to load
            try:
                page.wait_for_selector(".content-class", timeout=10000)  # Replace with actual content selector
            except Exception as wait_error:
                print(f"Content not found in time: {wait_error}")

            # Extract all visible text from the page
            content = page.evaluate("() => document.body.innerText")

            browser.close()
            return content
    except Exception as e:
        print(f"Error occurred while scraping: {e}")
        return None

@app.route('/process-annuaire', methods=['POST'])
def process_annuaire_input():
    return process_input("annuaire", annuaire_program)

@app.route('/process-evenement', methods=['POST'])
def process_evenement_input():
    return process_input("evenement", evenement_program)

def process_input(table_name, program):
    url = request.form.get('url', None)
    text_input = request.form.get('text', '')
    file = request.files.get('file')

    if url:
        # Scrape content if a URL is provided
        text_input = scrape_content(url)
        if not text_input:
            return jsonify({'error': 'Failed to scrape content from the provided URL'}), 400
    elif file:
        # Process the uploaded file
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith('.xlsx'):
                df = pd.read_excel(file)
            else:
                text_input = file.read().decode('utf-8')
                df = None

            if df is not None:
                text_input = df.to_json(orient='records')
        except Exception as e:
            return jsonify({'error': f"Failed to process file: {str(e)}"}), 400

    if not text_input:
        return jsonify({'error': 'No input provided'}), 400

    try:
        # Use Pydantic Program for structured extraction
        response = program(text_input=text_input)
        entries = response.entries
    except (ValidationError, Exception) as e:
        return jsonify({'error': f"Failed to process input: {str(e)}"}), 500

    conn = get_db_connection()
    cursor = conn.cursor()

    duplicates = []
    successful_inserts = []

    for entry in entries:
        try:
            entry_dict = entry.model_dump()  # Use Pydantic v2 `model_dump` to serialize data
            entry_dict.pop('numero', None)  # Ensure `numero` is excluded for new entries

            # Prepare the duplicate detection query
            if table_name == "annuaire":
                cursor.execute(
                    """
                    SELECT *
                    FROM annuaire
                    WHERE similarity(nom, %s) > 0.3 AND LEFT(prenom, 1) = LEFT(%s, 1);
                    """,
                    (entry_dict['nom'], entry_dict['prenom'])
                )
            elif table_name == "evenement":
                cursor.execute(
                    """
                    SELECT *
                    FROM evenement
                    WHERE similarity(nom_evenement, %s) > 0.3 AND LEFT(nom_evenement, 1) = LEFT(%s, 1);
                    """,
                    (entry_dict['nom_evenement'], entry_dict['nom_evenement'])
                )

            # Check for existing entries
            existing = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            close_matches = [dict(zip(column_names, row)) for row in existing]

            if close_matches:
                # Add to duplicates if matches found
                duplicates.append({
                    'new_entry': entry_dict,
                    'existing_entries': close_matches
                })
            else:
                # Insert into the database if no duplicates
                entry_dict['date_derniere_modification'] = datetime.now().strftime('%Y-%m-%d')
                columns = ', '.join(entry_dict.keys())
                values = ', '.join(['%s'] * len(entry_dict))
                cursor.execute(
                    f"INSERT INTO {table_name} ({columns}) VALUES ({values}) RETURNING numero",
                    list(entry_dict.values())
                )
                new_numero = cursor.fetchone()[0]  # Fetch the new `numero`
                entry_dict['numero'] = new_numero  # Update entry with the generated `numero`
                successful_inserts.append(entry_dict)
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f"Database error: {str(e)}"}), 500

    # Commit changes to the database
    conn.commit()
    conn.close()

    # Construct the response
    response = {'message': 'Processing completed.', 'successful_inserts': successful_inserts}
    if duplicates:
        response['duplicates'] = duplicates

    # If duplicates exist, return a 409 status with duplicate details
    if duplicates:
        return jsonify(response), 409

    # Return success response if no duplicates
    return jsonify(response), 201

@app.route('/replace-annuaire', methods=['PUT'])
def replace_annuaire_entry():
    return replace_entry("annuaire")

@app.route('/replace-evenement', methods=['PUT'])
def replace_evenement_entry():
    return replace_entry("evenement")

def replace_entry(table_name):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        for entry in data:
            processed_entry = {k: (None if v == "" else v) for k, v in entry.items()}
            if "numero" in processed_entry:
                cursor.execute(f"""
                    UPDATE {table_name}
                    SET {', '.join([f'{k} = %s' for k in processed_entry.keys() if k != 'numero'])},
                        date_derniere_modification = CURRENT_DATE
                    WHERE numero = %s
                """, list(processed_entry.values()) + [processed_entry['numero']])
            else:
                return jsonify({'error': "Missing 'numero' field for replacement"}), 400

        conn.commit()
        conn.close()
        return jsonify({'message': f'Entries in {table_name} replaced successfully'}), 200
    except Exception as e:
        return jsonify({'error': f"Database error: {str(e)}"}), 500

@app.route('/add-annuaire', methods=['POST'])
def add_annuaire_entry():
    return add_entry("annuaire")

@app.route('/add-evenement', methods=['POST'])
def add_evenement_entry():
    return add_entry("evenement")

def add_entry(table_name):
    try:
        entry = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        processed_entry = {k: (None if v == "" else v) for k, v in entry.items()}
        processed_entry['date_derniere_modification'] = datetime.now().strftime('%Y-%m-%d')

        columns = ', '.join(processed_entry.keys())
        values = ', '.join(['%s'] * len(processed_entry))
        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({values})", list(processed_entry.values()))

        conn.commit()
        conn.close()
        return jsonify({'message': f'Entry added to {table_name} successfully'}), 201
    except Exception as e:
        return jsonify({'error': f"Database error: {str(e)}"}), 500

def dismiss_popups(page):
    """Dismiss popups or overlays that block interactions."""
    try:
        popups = [
            "button[aria-label='Accept all']",
            "button[aria-label='Agree']",
            ".scSharedMaterialpopupbackdrop",
        ]
        for selector in popups:
            elements = page.locator(selector)
            if elements.count() > 0:
                for element in elements.all():
                    if element.is_visible():
                        try:
                            element.click()
                            print(f"Dismissed popup: {selector}")
                            page.wait_for_timeout(500)  # Allow DOM updates
                        except Exception as e:
                            print(f"Error clicking popup {selector}: {e}")
    except Exception as e:
        print(f"Error dismissing popups: {e}")


def filter_irrelevant_links(links):
    """Filter out irrelevant or non-informative links."""
    irrelevant_domains = ['google.com', 'google.ch', 'support.google']
    return [link for link in links if not any(domain in link for domain in irrelevant_domains)]


def truncate_content(content, max_length=4000):
    """Truncate content to avoid exceeding token limits."""
    return content[:max_length]


def is_valid_link(link):
    """Check if the link is valid and starts with http/https."""
    return link and link.startswith(('http://', 'https://')) and validators.url(link)


def scrape_google(title, first_name, last_name, zip_code, max_results=3):
    """Scrape Google Search results for relevant data within Switzerland and in French."""
    try:
        query = f"{title} {first_name} {last_name} {zip_code}"
        # Add `gl=ch` for geographic location and `cr=countryCH` for country restriction
        search_url = f"https://www.google.com/search?q={query}&hl=fr&gl=ch&cr=countryCH"
        collected_entries = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"Scraping Google results for query: {query}")
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")

            # Dismiss popups
            dismiss_popups(page)

            # Extract URLs
            result_links = page.locator('a').evaluate_all(
                '(links) => links.map(link => link.href)'
            )
            # Filter valid and relevant links
            result_links = [link for link in result_links if is_valid_link(link)]
            result_links = filter_irrelevant_links(result_links)[:max_results]
            print(f"Filtered {len(result_links)} relevant and valid links.")

            for link in result_links:
                try:
                    print(f"Scraping content from: {link}")
                    page.goto(link, timeout=30000)
                    page.wait_for_load_state("domcontentloaded")
                    dismiss_popups(page)

                    # Extract visible text content only from the page
                    content = page.evaluate("() => document.body.innerText")
                    if content:
                        content = truncate_content(content)
                        # print(f"Scraped content from {link}: {content[:200]}...")

                        # Convert content into structured AnnuaireEntry
                        structured_data = annuaire_program(text_input=content).entries[0].model_dump()
                        
                        # Attach the URL to the structured data
                        structured_data['url'] = link
                        collected_entries.append(structured_data)
                except Exception as e:
                    print(f"Error processing {link}: {e}")

            browser.close()

        return collected_entries
    except Exception as e:
        print(f"Error occurred during Google scraping: {e}")
        return []

def to_boolean(value):
    if isinstance(value, str):
        return value.lower() in ["true", "t", "yes", "y", "oui"]
    return bool(value)

@app.route('/update-annuaire', methods=['POST'])
def update_annuaire():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch all entries from Annuaire
        cursor.execute("SELECT * FROM annuaire;")
        entries = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        # Limit to MAX_ENTRIES
        entries = entries[:MAX_ENTRIES]

        @stream_with_context
        def process_entries():
            for idx, entry in enumerate(entries):
                entry_data = dict(zip(column_names, entry))

                # Step 1: Prepare data
                title = 'Dr'  # Default to "Dr" if None or empty
                first_name = entry_data.get('prenom', '')
                last_name = entry_data.get('nom', '')
                try:
                    zip_code = int(entry_data.get('npa') or 0)  # Ensure zip_code is an integer, fallback to 0
                except ValueError:
                    zip_code = 0

                # Step 2: Scrape Google Search results
                google_results = scrape_google(title, first_name, last_name, zip_code)

                # If no results, update `date_derniere_modification`
                if not google_results:
                    try:
                        cursor.execute(
                            """
                            UPDATE annuaire
                            SET date_derniere_modification = CURRENT_TIMESTAMP
                            WHERE id = %s
                            """,
                            (entry_data["id"],)
                        )
                        conn.commit()
                        yield json.dumps({
                            "entry_id": entry_data["id"],
                            "message": "No results found. Timestamp updated."
                        }) + "\n"
                    except Exception as update_error:
                        conn.rollback()
                        yield json.dumps({
                            "entry_id": entry_data["id"],
                            "error": str(update_error),
                            "message": "Failed to update timestamp."
                        }) + "\n"
                    continue

                # Step 3: Compare results and identify conflicts
                sources = []

                for structured_data in google_results:
                    nom_similarity = fuzz.partial_ratio(entry_data.get('nom', ''), structured_data.get('nom', ''))
                    prenom_similarity = fuzz.partial_ratio(entry_data.get('prenom', ''), structured_data.get('prenom', ''))

                    if nom_similarity > 80 or prenom_similarity > 80:
                        conflicting_columns = {}
                        for key, value in structured_data.items():
                            if key in ["url", "nom", "prenom", "npa"]:
                                continue

                            existing_value = to_boolean(entry_data.get(key)) if key in ["medecin", "medecin_intra_hospitalier", "lu", "ma", "me", "je", "ve", "sa", "di"] else entry_data.get(key)
                            new_value = to_boolean(value) if key in ["medecin", "medecin_intra_hospitalier", "lu", "ma", "me", "je", "ve", "sa", "di"] else value

                            if existing_value != new_value:
                                conflicting_columns[key] = {"existing": existing_value, "new": new_value}

                        if conflicting_columns:
                            sources.append({
                                "url": structured_data.get("url"),
                                "conflicting_columns": conflicting_columns
                            })

                if sources:
                    yield json.dumps({
                        "entry_id": entry_data["id"],
                        "nom": entry_data.get("nom"),
                        "prenom": entry_data.get("prenom"),
                        "sources": sources,
                        "message": "Conflicts found."
                    }) + "\n"
                else:
                    try:
                        cursor.execute(
                            """
                            UPDATE annuaire
                            SET date_derniere_modification = CURRENT_TIMESTAMP
                            WHERE id = %s
                            """,
                            (entry_data["id"],)
                        )
                        conn.commit()
                        yield json.dumps({
                            "entry_id": entry_data["id"],
                            "message": "No conflicts. Timestamp updated."
                        }) + "\n"
                    except Exception as update_error:
                        conn.rollback()
                        yield json.dumps({
                            "entry_id": entry_data["id"],
                            "error": str(update_error),
                            "message": "Failed to update timestamp."
                        }) + "\n"

            # Signal to frontend that all entries have been processed
            yield json.dumps({
                "message": "All entries processed."
            }) + "\n"

        return Response(process_entries(), content_type='application/json')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    try:
        data = request.json  # A single conflict resolution
        conn = get_db_connection()
        cursor = conn.cursor()

        print("Raw data received:", data)  # Debugging log

        entry_id = data.get('entry_id')
        updates = data.get('updates', {})

        if not entry_id:
            return jsonify({"error": "Invalid data: 'entry_id' is required"}), 400

        if not updates:
            return jsonify({"error": "No updates provided"}), 400

        sanitized_updates = {k: v for k, v in updates.items() if v is not None}
        if not sanitized_updates:
            return jsonify({"message": "No valid updates to process."}), 200

        # Build the dynamic update query
        update_query = f"""
            UPDATE annuaire
            SET {', '.join([f"{key} = %s" for key in sanitized_updates.keys()])},
                date_derniere_modification = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        update_values = list(sanitized_updates.values()) + [entry_id]

        try:
            cursor.execute(update_query, update_values)
            conn.commit()
            print(f"Entry {entry_id} updated successfully.")
            return jsonify({"message": f"Entry {entry_id} updated successfully."}), 200
        except Exception as update_error:
            conn.rollback()
            print(f"Failed to update entry {entry_id}: {update_error}")
            return jsonify({"error": f"Failed to update entry {entry_id}: {str(update_error)}"}), 500

    except Exception as e:
        print(f"Error in /resolve-conflicts: {str(e)}")
        return jsonify({"error": f"Failed to resolve conflict: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
