from flask import Flask, request, jsonify, stream_with_context, Response
from flask_cors import CORS
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from typing import List, Optional
from datetime import datetime
from threading import Lock
from rapidfuzz import fuzz
from datetime import date, time, datetime
from services.scraper import scrape_website
import os
import psycopg2
import pandas as pd
import validators
import json
import requests

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Limit the number of entries processed
MAX_UPDATE_ENTRIES = 5
MAX_GOOGLE_SEARCH = 3
processing_lock = Lock()  # Prevent concurrent updates

# Informaniak API credentials
INFORMANIAK_API_KEY = os.getenv("INFORMANIAK_API_KEY")
INFORMANIAK_PRODUCT_ID = os.getenv("INFORMANIAK_PRODUCT_ID")
INFORMANIAK_API_URL = f"https://api.infomaniak.com/1/ai/{INFORMANIAK_PRODUCT_ID}/openai/chat/completions"

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

class AnnuaireEntry(BaseModel):
    """Model representing an entry for the Annuaire database."""
    id: Optional[int] = None
    no_ean: Optional[str] = None
    type: Optional[str] = None
    type_de_fournisseur: Optional[str] = None
    nom: str = None
    prenom: str = None
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
    coord_geo_nord: Optional[str] = None
    coord_geo_est: Optional[str] = None
    longitude: Optional[str] = None
    latitude: Optional[str] = None
    class Config:
        from_attributes = True

class EvenementEntry(BaseModel):
    """Model representing an entry for the Evenement database."""
    id: Optional[int]
    nom_evenement: str  # Name of the event, required
    titre_evenement: Optional[str] = None  # Event title, optional
    date_debut: Optional[date] = None  # Event start date
    date_fin: Optional[date] = None  # Event end date
    horaire_debut: Optional[datetime] = None  # Event start timestamp
    horaire_fin: Optional[datetime] = None  # Event end timestamp
    texte_libre: Optional[str] = None  # Free text for additional information
    court_descriptif: Optional[str] = None  # Short description
    numero_partenaire: Optional[int] = None  # Partner number, optional
    nom_partenaire: Optional[str] = None  # Partner name, optional
    partenaire_de_la_selection: Optional[str] = None  # Selected partner text, optional
    sites_originaux: Optional[str] = None  # Original sites, optional
    date_creation: Optional[date] = None  # Record creation date
    mode_creation: Optional[str] = None  # Mode of creation
    mode_modification: Optional[str] = None  # Mode of modification
    id_dernier_modificateur: Optional[int] = None  # ID of the last modifier
    date_de_peremption: Optional[datetime] = None  # Expiration date

class AnnuaireEntries(BaseModel):
    """Model representing multiple entries for the Annuaire database."""
    entries: List[AnnuaireEntry]

class EvenementEntries(BaseModel):
    """Model representing multiple entries for the Evenement database."""
    entries: List[EvenementEntry]

# Function to directly call Informaniak API
def call_informaniak_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {INFORMANIAK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    response = requests.post(INFORMANIAK_API_URL, headers=headers, json=payload)
    response.raise_for_status()  # Raise exception for any error response

    content = response.json()["choices"][0]["message"]["content"]
    input_tokens = response.json()["usage"]["input_tokens"]
    output_tokens = response.json()["usage"]["output_tokens"]

    total_token_count = input_tokens + output_tokens
    print("Token in : \t\t\t\t\t{:7d}".format(input_tokens))
    print("Token out : \t\t\t\t\t{:7d}".format(output_tokens))
    print("Nombre de tokens utilisés: \t\t\t{:7d}".format(total_token_count))
    print("Moyenne de tokens utilisés par document: \t{:7.0f}".format(total_token_count))
    print("Prix total: \t\t\t\t\t{:11.3f}".format(input_tokens/10000*0.01 + output_tokens/10000*0.03))
    print("Prix moyen par document: \t\t\t{:11.3f}".format((input_tokens/10000*0.01 + output_tokens/10000*0.03)))

    return content

@app.route('/annuaire', methods=['GET'])
def get_annuaire():
    return fetch_table_entries("annuaire")

@app.route('/evenements', methods=['GET'])
def get_evenement_entries():
    return fetch_table_entries("evenement")

def serialize_value(value):
    """
    Converts non-JSON-serializable objects to strings.
    Handles datetime, date, and time objects.
    """
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()  # Converts to ISO 8601 string
    return value

def fetch_table_entries(table_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        conn.close()

        # Process rows and ensure JSON serializability
        result = [
            {column: serialize_value(value) for column, value in zip(column_names, row)}
            for row in rows
        ]
        return jsonify(result)
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
    return process_input("annuaire")

@app.route('/process-evenement', methods=['POST'])
def process_evenement_input():
    return process_input("evenement")

def process_input(table_name):
    url = request.form.get('url', None)
    text_input = request.form.get('text', '')
    file = request.files.get('file')

    if url:
        # Scrape content if a URL is provided
        text_input = scrape_website(url, 1, 1)
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
        # Call Informaniak API to process the input
        # Modify prompt to explicitly define the structure for each table
        if table_name == "annuaire":
            prompt = f"""
            Extract structured data in JSON format with multiple entries for a database from the following French text:
            {text_input}

            The fields must include:
            - no_ean (optional, string)
            - type (Personne/Organization) (optional, string)
            - type_de_fournisseur (Acteur simple) (optional, string)
            - nom (string)
            - prenom (string)
            - acronyme (optional, string)
            - telephone (optional, string)
            - portable (optional, string)
            - courriel (optional, string)
            - site_web (optional, string)
            - lien_org (optional, string)
            - organisation (optional, string)
            - role_activite_specialite (optional, string)
            - medecin (optional, boolean)
            - medecin_intra_hospitalier (optional, boolean)
            - lu (optional, boolean) (indicating if open on Monday/Lundi)
            - ma (optional, boolean) (indicating if open on Mardi/Tuesday)
            - me (optional, boolean) (indicating if open on Mercredi/Wednesday)
            - je (optional, boolean) (indicating if open on Jeudi/Thursday)
            - ve (optional, boolean) (indicating if open on Vendredi/Friday)
            - sa (optional, boolean) (indicating if open on Samdi/Saturday)
            - di (optional, boolean) (indicating if open on Dimanche/Sunday)
            - tags (optional, string)
            - selection (optional, string)
            - commentaire (optional, string)
            - voie (optional, string)
            - numero (optional, string)
            - complement (optional, string)
            - npa (optional, integer)
            - localite (optional, string)
            - pays (optional, string)
            - coord_geo_nord (optional, string)
            - coord_geo_est (optional, string)
            - longitude (optional, string)
            - latitude (optional, string)

            Instructions for parsing the entries:
            1. Parse the `name` field into `prenom` (first name) and `nom` (last name), excluding titles like "Dre", "Dr", "Mister", or "Doctor".
            2. Parse operating hours into the `lu`, `ma`, `me`, `je`, `ve`, `sa`, and `di` fields as `True` for open and `False` for closed. Text like  `lundi - vendredi` means a period of time from Lundi (monday) to Vendredi (Friday).
            3. Respond in JSON format only, without including the word 'json' or any additional commentary.
            4. Include only the specified fields, even if additional information is available in the input text.
            5. Connect the address to the individual as much as possible.
            6. The `nom` and `prenom` fields are required. Otherwise, ignore the entry.

            Typically, there is only one entry in the input text, representing an individual, not organization.
            """
        elif table_name == "evenement":
            prompt = f"""
            Extract structured data in JSON format with multiple entries for a database from the following French text:
            {text_input}

            The fields must include:
            - nom_evenement (string)
            - titre_evenement (optional, string)
            - date_debut (optional, string) (format: YYYY-MM-DD)
            - date_fin (optional, string) (format: YYYY-MM-DD)
            - horaire_debut (optional, string) (format: YYYY-MM-DD HH:MM:SS)
            - horaire_fin (optional, string) (format: YYYY-MM-DD HH:MM:SS)
            - texte_libre (optional, string)
            - court_descriptif (optional, string)
            - numero_partenaire (optional, integer)
            - nom_partenaire (optional, string)
            - partenaire_de_la_selection (optional, string)
            - sites_originaux (optional, string)
            - date_creation (optional, string) (format: YYYY-MM-DD)
            - mode_creation (optional, string)
            - mode_modification (optional, string)
            - id_dernier_modificateur (optional, integer)
            - date_de_peremption (optional, string) (format: YYYY-MM-DD HH:MM:SS)

            Instructions for parsing the entries:
            1. Parse event dates and times into the appropriate fields:
                Use date_debut and date_fin for general start and end dates.
                Use horaire_debut and horaire_fin for specific timestamps when provided.
            2. Extract free-form descriptions into texte_libre and summaries into court_descriptif.
            3. Assign partner-related information (numero_partenaire, nom_partenaire, partenaire_de_la_selection) as applicable.
            4. Parse the creation and modification metadata (date_creation, mode_creation, mode_modification, id_dernier_modificateur) when mentioned.
            5. Use date_de_peremption if an expiration date is provided for the event.
            6. Respond with structured data in JSON format only, without the word "JSON" or additional commentary.
            7. Include only the specified fields, even if additional information is available in the input text.
            8. Exclude entries without a nom_evenement.
            """
        
        # Call Informaniak API to process the input with the detailed prompt
        api_response = call_informaniak_api(prompt)
        # print(f"Received response from Informaniak API: {api_response}...")  # Log the first 200 characters
        
        # Parse the API response and validate using Pydantic models
        if table_name == "annuaire":
            entries = AnnuaireEntries(entries=json.loads(api_response)).entries  # Validate and extract entries
        elif table_name == "evenement":
            entries = EvenementEntries(entries=json.loads(api_response)).entries  # Validate and extract entries
        print(f"Entries: {entries}...")  # Log the first 200 characters
    except (ValidationError, Exception) as e:
        print("Validation Error:", e)
        return jsonify({'error': f"Failed to process input: {str(e)}"}), 500

    conn = get_db_connection()
    cursor = conn.cursor()

    duplicates = []
    successful_inserts = []

    def serialize_entry(entry):
        """Convert non-serializable fields to JSON-compatible types."""
        for key, value in entry.items():
            if isinstance(value, (datetime, date, time)):
                entry[key] = value.isoformat()
        return entry

    for entry in entries:
        print("Entry:", entry)
        try:
            entry_dict = entry.dict()
            entry_dict.pop('id', None)  # Ensure `id` is excluded for new entries

            # Prepare the duplicate detection query
            if table_name == "annuaire":
                cursor.execute(
                    """
                    SELECT *
                    FROM annuaire
                    WHERE similarity(nom, %s) > 0.7 OR similarity(prenom, %s) > 0.7;
                    """,
                    (entry_dict['nom'], entry_dict['prenom'])
                )
            elif table_name == "evenement":
                cursor.execute(
                    """
                    SELECT *
                    FROM evenement
                    WHERE similarity(nom_evenement, %s) > 0.8;
                    """,
                    (entry_dict['nom_evenement'],)
                )

            # Check for existing entries
            existing = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            close_matches = [dict(zip(column_names, row)) for row in existing]

            if close_matches:
                duplicates.append({
                    'new_entry': serialize_entry(entry_dict),
                    'existing_entries': [serialize_entry(match) for match in close_matches],
                })
            else:
                entry_dict['date_derniere_modification'] = datetime.now().strftime('%Y-%m-%d')
                columns = ', '.join(entry_dict.keys())
                values = ', '.join(['%s'] * len(entry_dict))
                cursor.execute(
                    f"INSERT INTO {table_name} ({columns}) VALUES ({values}) RETURNING id",
                    list(entry_dict.values())
                )
                new_id = cursor.fetchone()[0]
                entry_dict['id'] = new_id
                successful_inserts.append(serialize_entry(entry_dict))
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

    print(f"Duplicates: {duplicates}")
    
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

        print(f"Data received for replacement: {data}")

        for item in data:
            processed_entry = {k: (None if v == "" else v) for k, v in item.items()}

            # Convert `horaire_debut` and `horaire_fin` to TIME format if present
            if "horaire_debut" in processed_entry and processed_entry["horaire_debut"]:
                processed_entry["horaire_debut"] = processed_entry["horaire_debut"].split("T")[-1]
            if "horaire_fin" in processed_entry and processed_entry["horaire_fin"]:
                processed_entry["horaire_fin"] = processed_entry["horaire_fin"].split("T")[-1]

            if "existing_id" not in processed_entry:
                return jsonify({'error': "Missing 'existing_id' field for replacement"}), 400

            existing_id = processed_entry.pop("existing_id")

            # Construct SQL query for replacement
            query = f"""
                UPDATE {table_name}
                SET {', '.join([f'{k} = %s' for k in processed_entry.keys()])},
                    date_derniere_modification = CURRENT_DATE
                WHERE id = %s
            """
            values = list(processed_entry.values()) + [existing_id]

            # Debug: Log the query and parameters
            print(f"Executing query: {cursor.mogrify(query, values)}")

            cursor.execute(query, values)

        conn.commit()
        conn.close()
        return jsonify({'message': f'Entries in {table_name} replaced successfully'}), 200
    except Exception as e:
        print(f"Error in replace_entry: {str(e)}")
        return jsonify({'error': f"Database error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

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

        # Debug: Log the received data
        print(f"Entry received for adding new: {entry}")

        processed_entry = {k: (None if v == "" else v) for k, v in entry.items()}

        # Exclude `id` if present
        if "id" in processed_entry:
            processed_entry.pop("id")

        # Convert ISO 8601 datetime to time for `horaire_debut` and `horaire_fin`
        if processed_entry.get('horaire_debut'):
            try:
                processed_entry['horaire_debut'] = datetime.fromisoformat(processed_entry['horaire_debut']).time()
            except ValueError:
                processed_entry['horaire_debut'] = None  # Set to None if parsing fails

        if processed_entry.get('horaire_fin'):
            try:
                processed_entry['horaire_fin'] = datetime.fromisoformat(processed_entry['horaire_fin']).time()
            except ValueError:
                processed_entry['horaire_fin'] = None  # Set to None if parsing fails

        # Add `date_derniere_modification`
        processed_entry['date_derniere_modification'] = datetime.now().strftime('%Y-%m-%d')

        columns = ', '.join(processed_entry.keys())
        values = ', '.join(['%s'] * len(processed_entry))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
        params = list(processed_entry.values())

        # Debug: Log the query and parameters
        print(f"Executing query: {query}")
        print(f"With parameters: {params}")

        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return jsonify({'message': f'Entry added to {table_name} successfully'}), 201
    except Exception as e:
        print(f"Database Error: {str(e)}")  # Logs the error
        return jsonify({'error': f"Database error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

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


def scrape_google(title, first_name, last_name, zip_code, max_results=MAX_GOOGLE_SEARCH):
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
            # print(f"Filtered {len(result_links)} relevant and valid links.")

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
                        prompt = f"""
                        Extract structured data in JSON format with multiple entries for a database from the following french text:
                        {content}

                        The fields must include:
                        - no_ean (optional, string)
                        - type (Personne/Organization) (optional, string)
                        - type_de_fournisseur (Acteur simple) (optional, string)
                        - nom (string)
                        - prenom (string)
                        - acronyme (optional, string)
                        - telephone (optional, string)
                        - portable (optional, string)
                        - courriel (optional, string)
                        - site_web (optional, string)
                        - lien_org (optional, string)
                        - organisation (optional, string)
                        - role_activite_specialite (optional, string)
                        - medecin (optional, boolean)
                        - medecin_intra_hospitalier (optional, boolean)
                        - lu (optional, boolean) (indicating if open on Monday/Lundi)
                        - ma (optional, boolean) (indicating if open on Mardi/Tuesday)
                        - me (optional, boolean) (indicating if open on Mercredi/Wednesday)
                        - je (optional, boolean) (indicating if open on Jeudi/Thursday)
                        - ve (optional, boolean) (indicating if open on Vendredi/Friday)
                        - sa (optional, boolean) (indicating if open on Samdi/Saturday)
                        - di (optional, boolean) (indicating if open on Dimanche/Sunday)
                        - tags (optional, string)
                        - selection (optional, string)
                        - commentaire (optional, string)
                        - voie (optional, string)
                        - numero (optional, string)
                        - complement (optional, string)
                        - npa (optional, integer)
                        - localite (optional, string)
                        - pays (optional, string)
                        - coord_geo_nord (optional, string)
                        - coord_geo_est (optional, string)
                        - longitude (optional, string)
                        - latitude (optional, string)

                        Instructions for parsing the entries:
                        1. Parse the `name` field into `prenom` (first name) and `nom` (last name), excluding titles like "Dre", "Dr", "Mister", or "Doctor".
                        2. Parse operating hours into the `lu`, `ma`, `me`, `je`, `ve`, `sa`, and `di` fields as `True` for open and `False` for closed. Text like  `lundi - vendredi` means a period of time from Lundi (monday) to Vendredi (Friday).
                        3. Respond in JSON format only, without including the word 'json' or any additional commentary.
                        4. Include only the specified fields, even if additional information is available in the input text.
                        5. Connect the address to the individual as much as possible.
                        6. The `nom` and `prenom` fields are required. Otherwise, ignore the entry.

                        Typically, there is only one entry in the input text, representing an individual, not organization.
                        """
                    
                        # Call Informaniak API to process the input with the detailed prompt
                        api_response = call_informaniak_api(prompt)
                        structured_data = AnnuaireEntries(entries=json.loads(api_response)).entries
                        
                        # Parse response and add entries with the associated URL
                        collected_entries.append({
                            "url": link,
                            "structured_data": structured_data
                        })

                        print(f"Structured data: {structured_data}")
                except Exception as e:
                    print(f"Error processing {link}: {e}")

            browser.close()

        return collected_entries
    except Exception as e:
        print(f"Error occurred during Google scraping: {e}")
        return []

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
        entries = entries[:MAX_UPDATE_ENTRIES]

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
                print(f"google_results: {google_results}...")
                for result in google_results:
                    result_url = result.get("url")
                    for structured_entry in result.get("structured_data", []):
                        # Extract relevant fields
                        nom = structured_entry.nom
                        prenom = structured_entry.prenom

                        nom_similarity = fuzz.partial_ratio(entry_data.get('nom', ''), nom)
                        prenom_similarity = fuzz.partial_ratio(entry_data.get('prenom', ''), prenom)

                        if nom_similarity > 80 or prenom_similarity > 80:
                            conflicting_columns = {}
                            for key, value in structured_entry.dict().items():  # Changed from model_dump() to dict()
                                if key in ["url", "nom", "prenom", "npa"]:
                                    continue

                                existing_value = entry_data.get(key)
                                new_value = value

                                if existing_value != new_value:
                                    conflicting_columns[key] = {"existing": existing_value, "new": new_value}

                            if conflicting_columns:
                                sources.append({
                                    "url": result_url,
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
