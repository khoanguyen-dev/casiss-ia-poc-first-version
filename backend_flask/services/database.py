import os
import psycopg2
import pandas as pd
from services.scraper import scrape_google, scrape_website, scrape_bing
from flask import request, jsonify
from datetime import datetime
from threading import Lock
from rapidfuzz import fuzz
from services.utils import serialize_value, serialize_entry, extract_json, split_text_with_overlap
from psycopg2.extras import RealDictCursor
from services.api_handler import generate_embedding_with_infomaniak, call_informaniak_api
from models.annuaire import AnnuaireEntry
from models.evenement import EvenementEntry
from pydantic import ValidationError
from typing import List
from collections import Counter
from googletrans import Translator
from multi_rake import Rake
from rapidfuzz import fuzz, process

# Limit the number of entries processed
MAX_GOOGLE_SEARCH = 3
MAX_TOP_DOCUMENT_SEARCH = 3
MAX_KEYWORDS = 10
SIMILARITY_THRESHOLD = 90
MAX_TOKENS = 400
OVERLAP_SENTENCES = 1

processing_lock = Lock()  # Prevent concurrent updates

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

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

def process_input(table_name):
    url = request.form.get('url', None)
    text_input = request.form.get('text', '')
    file = request.files.get('file')
    print(f"url: {url}") 
    print(f"text_input: {text_input}") 
    print(f"file: {file}") 

    if url:
        # Scrape content if a URL is provided
        text_input = scrape_website(url, 1, 1)[0]['content']
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
    
    # Split text into chunks
    # chunks = split_text_with_overlap(text_input, max_tokens=MAX_TOKENS, overlap_sentences=OVERLAP_SENTENCES)
    # Initialize a list to store all extracted entries

    valid_entries = []        
    # Process each chunk separately
    #for chunk in enumerate(chunks):
        #print(f"Processing chunk:", chunk)
    try:
        # Call Informaniak API to process the input
        # Modify prompt to explicitly define the structure for each table
        if table_name == "annuaire":
            prompt = f"""
            Extract structured data in JSON format with multiple entries for a database from the provided French text.

            The fields include:
            - no_ean (optional, string)
            - type (value: Personne/Organization) (optional, string)
            - type_de_fournisseur (value: Acteur simple) (optional, string)
            - nom (must included, string)
            - prenom (must included, string)
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
            - numero (optional, integer)
            - complement (optional, string)
            - npa (optional, integer) (usually 4 letters code before localite)
            - localite (optional, string)
            - pays (optional, string)
            - coord_geo_nord (optional, string)
            - coord_geo_est (optional, string)
            - longitude (optional, string)
            - latitude (optional, string)

            Instructions for parsing the entries:
            1. Parse the `name` field into `prenom` (first name) and `nom` (last name), excluding titles like "Dre", "Dr", "Mister", or "Doctor".
            2. Parse operating hours into the `lu`, `ma`, `me`, `je`, `ve`, `sa`, and `di` fields as `True` for open and `False` for closed. Text like  `lundi - vendredi` means a period of time from Lundi (monday) to Vendredi (Friday).
            3. Include only the specified fields, even if additional information is available in the input text.
            4. Connect the address to the individual as much as possible.
            5. The `nom` and `prenom` fields are required. Otherwise, ignore the entry.
            6. Typically, there is only one entry in the input text, representing an individual, not organization.
            7. Only include max 15 entries, ignore all the others.

            Always complete the JSON even without all the entries.
            Respond in list of JSON format only, without including the word 'json'. No additional commentary. 

            **The provided French text:**
            {text_input}
            """
        elif table_name == "evenement":
            prompt = f"""
            Extract structured data in JSON format with multiple entries for a database from the provided French text.

            The fields include:
            - nom_evenement (must included, string)
            - titre_evenement (optional, string)
            - date_debut (optional, string) (format: YYYY-MM-DD)
            - date_fin (optional, string) (format: YYYY-MM-DD)
            - horaire_debut (optional, string) (format: HH:MM:SS)
            - horaire_fin (optional, string) (format: HH:MM:SS)
            - texte_libre (optional, string)
            - public cible (value: Senior/Enfant/Tout public) (optional, string) (target population, derived from titre_evenement, texte_libre or court_descriptif)
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
                - Text like `14h-17h` means `horaire_debut` is `14:00:00` and `horaire_fin` is `17:00:00`
                - Text like `A 19h`means `horaire_debut` is `19:00:00`
            2. Extract free-form descriptions into texte_libre and summaries into court_descriptif.
            3. Assign partner-related information (numero_partenaire, nom_partenaire, partenaire_de_la_selection) as applicable.
            4. Parse the creation and modification metadata (date_creation, mode_creation, mode_modification, id_dernier_modificateur) when mentioned.
            5. Use date_de_peremption if an expiration date is provided for the event.
            6. Include only the specified fields, even if additional information is available in the input text.
            7. Exclude entries without a nom_evenement.
            8. Only include max 15 entries, ignore all the others.

            Always complete the JSON even without all the entries.
            Respond in list of JSON format only, without including the word 'json'. No additional commentary. 

            **The provided French text:**
            {text_input}
            """
        
        # Call Informaniak API to process the input with the detailed prompt
        api_response, cost = call_informaniak_api(prompt, 5000, 0.2)
        print(f"api_response: {api_response}")  
        # Extract and parse JSON safely
        api_response = extract_json(api_response)

        # Ensure response is a list
        if isinstance(api_response, dict):
            api_response = [api_response]  # Wrap in a list if it's a single dict
        
        if table_name == "annuaire":
            for entry in api_response:
                try:
                    valid_entry = AnnuaireEntry.model_validate(entry)
                    valid_entries.append(valid_entry)
                except ValidationError as e:
                    print(f"Skipping invalid entry: {entry} | Error: {e}")
        elif table_name == "evenement":
            for entry in api_response:
                try:
                    valid_entry = EvenementEntry.model_validate(entry)
                    valid_entries.append(valid_entry)
                except ValidationError as e:
                    print(f"Skipping invalid entry: {entry} | Error: {e}")

    except (ValidationError, Exception) as e:
        print("Validation Error:", e)
        return jsonify({'error': f"Failed to process input: {str(e)}"}), 500

    conn = get_db_connection()
    cursor = conn.cursor()

    duplicates = []
    successful_inserts = []

    for entry in valid_entries:
        print("Entry:", entry)
        try:
            entry_dict = serialize_entry(entry.model_dump())
            entry_dict.pop('id', None)  # Ensure `id` is excluded for new entries

            # Prepare the duplicate detection query
            if table_name == "annuaire":
                cursor.execute(
                    """
                    SELECT *
                    FROM annuaire
                    WHERE similarity(nom, %s) > 0.7 AND similarity(prenom, %s) > 0.7;
                    """,
                    (entry_dict['nom'], entry_dict['prenom'])
                )
            elif table_name == "evenement":
                print("Date:", entry_dict.get('date_debut'))
                if entry_dict.get('date_debut') is not None:
                    cursor.execute(
                        """
                        SELECT *
                        FROM evenement
                        WHERE similarity(nom_evenement, %s) > 0.8
                        AND similarity(date_debut, %s) > 0.8;
                        """,
                        (entry_dict['nom_evenement'], entry_dict['date_debut'],)
                    )
                else:
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
            close_matches = [serialize_entry(dict(zip(column_names, row))) for row in existing]

            if close_matches:
                duplicates.append({
                    'new_entry': entry_dict,
                    'existing_entries': close_matches,
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
                successful_inserts.append(entry_dict)
                
        except Exception as e:
            conn.rollback()
            print(f"Database error: {str(e)}")
            return jsonify({'error': f"Database error: {str(e)}"}), 500
    
    # Commit changes to the database
    conn.commit()
    conn.close()

    # Construct the response
    response = {'message': 'Processing completed.', 'successful_inserts': successful_inserts, 'cost': cost}
    if duplicates:
        response['duplicates'] = duplicates

    print(f"Duplicates: {duplicates}")
    
    # If duplicates exist, return a 409 status with duplicate details
    if duplicates:
        return jsonify(response), 409

    # Return success response if no duplicates
    return jsonify(response), 201
    
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

def replace_entry(table_name):
    try:
        entry = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        print(f"Data received for replacement: {entry}")
        
        processed_entry = {k: (None if v == "" else v) for k, v in entry.items()}

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

def update_annuaire():
    try:
        data = request.get_json()  # Fix: Added missing ()
        entry_id = data.get("entry_id")  # Fix: Updated key name to match frontend

        if not entry_id:
            return jsonify({"error": "Missing entry ID"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the specific entry from Annuaire
        cursor.execute("SELECT * FROM annuaire WHERE id = %s;", (entry_id,))
        entry = cursor.fetchone()

        if not entry:
            return jsonify({"error": "Entry not found"}), 404

        column_names = [desc[0] for desc in cursor.description]
        entry_data = dict(zip(column_names, entry))

        # Step 1: Prepare data
        title = 'Dr'  
        first_name = entry_data.get('prenom', '')
        last_name = entry_data.get('nom', '')

        try:
            zip_code = entry_data.get('npa') or ""
        except ValueError:
            zip_code = ""

        # Step 2: Scrape Bing Search results
        search_results, cost = scrape_bing(title, first_name, last_name, zip_code)
        # search_results, cost = scrape_google(title, first_name, last_name, zip_code)

        # If no results, update `date_derniere_modification`
        if not search_results:
            try:
                cursor.execute(
                    "UPDATE annuaire SET date_derniere_modification = CURRENT_TIMESTAMP WHERE id = %s",
                    (entry_id,)
                )
                conn.commit()
                return jsonify({
                    "entry_id": entry_id,
                    "message": "No results found. Timestamp updated.",
                    "cost": cost
                })
            except Exception as update_error:
                conn.rollback()
                return jsonify({
                    "entry_id": entry_id,
                    "error": str(update_error),
                    "message": "Failed to update timestamp.",
                    "cost": cost
                })

        # Step 3: Compare results and identify conflicts
        sources = []
        for result in search_results:
            result_url = result.get("url")
            for structured_entry in result.get("structured_data", []):
                nom = structured_entry.nom
                prenom = structured_entry.prenom

                nom_similarity = fuzz.partial_ratio(entry_data.get('nom', ''), nom)
                prenom_similarity = fuzz.partial_ratio(entry_data.get('prenom', ''), prenom)

                if nom_similarity > 80 or prenom_similarity > 80:
                    conflicting_columns = {}
                    for key, value in structured_entry.dict().items():
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
            return jsonify({
                "entry_id": entry_id,
                "nom": entry_data.get("nom"),
                "prenom": entry_data.get("prenom"),
                "sources": sources,
                "message": "Conflicts found.",
                "cost": cost
            })
        else:
            try:
                cursor.execute(
                    "UPDATE annuaire SET date_derniere_modification = CURRENT_TIMESTAMP WHERE id = %s",
                    (entry_id,)
                )
                conn.commit()
                return jsonify({
                    "entry_id": entry_id,
                    "message": "No conflicts. Timestamp updated.",
                    "cost": cost
                })
            except Exception as update_error:
                conn.rollback()
                return jsonify({
                    "entry_id": entry_id,
                    "error": str(update_error),
                    "message": "Failed to update timestamp.",
                    "cost": cost
                })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

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

def store_in_db(content, embedding, source, keywords):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO navisante (content, embedding, source, keywords)
            VALUES (%s, %s, %s, %s);
            """,
            (content, embedding, source, keywords)
        )
        conn.commit()
    except Exception as e:
        print(f"Error storing data: {e}")
    finally:
        cur.close()
        conn.close()

def query_db(query_embedding, keywords, top_k=MAX_TOP_DOCUMENT_SEARCH, similarity_threshold=SIMILARITY_THRESHOLD):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch all keywords from the database
    cur.execute("SELECT DISTINCT UNNEST(keywords) AS keyword FROM navisante;")
    db_keywords = [row["keyword"] for row in cur.fetchall()]

    # Find similar keywords using RapidFuzz
    matched_keywords = set()
    for keyword in keywords:
        matches = process.extract(
            keyword, db_keywords, scorer=fuzz.ratio, score_cutoff=similarity_threshold
        )
        matched_keywords.update(match[0] for match in matches)

    # Filter by keywords if provided
    if matched_keywords:
        cur.execute(
            """
            SELECT content, source, 1 - (embedding <=> %s::vector) AS similarity
            FROM navisante
            WHERE keywords && %s::TEXT[] -- Array overlap operator
            ORDER BY similarity DESC
            LIMIT %s;
            """,
            (query_embedding, keywords, top_k)
        )
    else:
        cur.execute(
            """
            SELECT content, source, 1 - (embedding <=> %s::vector) AS similarity
            FROM navisante
            ORDER BY similarity DESC
            LIMIT %s;
            """,
            (query_embedding, top_k)
        )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def query_document():
    """
    Handles the document query endpoint, querying the database and passing results to the LLM.

    Returns:
        Response: JSON response with the LLM-generated answer and sources.
    """
    data = request.json
    print(f"Data received: {data}")

    query_text = data.get("query")
    user_history = data.get("history", [])  # Previous interactions or questions from the user

    if not query_text:
        return jsonify({"error": "Query text is required"}), 400

    try:
        translator = Translator()
        # Combine query_text with history
        combined_text = query_text + " ".join([h["content"] for h in user_history if h["role"] == "user"])
        query_text_lang = translator.detect(query_text).lang

        # Translate query_text and combined_text to French
        if (query_text_lang != "fr"):
            translated_query_text = translator.translate(query_text, src='auto', dest='fr').text
        else:
            translated_query_text = query_text 
        translated_combined_text = translator.translate(combined_text, src='auto', dest='fr').text

        # Extract keywords and generate embedding
        rake = Rake(language_code='fr', max_words=2)
        keywords = rake.apply(translated_query_text)
        # Limit to the top 20 keywords and get only the strings
        top_keywords = [keyword for keyword, score in keywords]
        query_embedding, embedding_cost = generate_embedding_with_infomaniak(translated_combined_text)  # Embedding vector

        # Ensure query_embedding is a PostgreSQL-compatible vector string
        query_embedding = f"[{','.join(map(str, query_embedding))}]"

        # Query the database
        results = query_db(query_embedding, top_keywords[:10])
        # print(f"Query results: {results}")

        # Prepare the `Relevant Documents` section
        if results:
            documents_summary = "\n\n".join(
                [
                    f"Document {idx + 1}:\nContent: {doc['content']}\n."
                    for idx, doc in enumerate(results)
                ]
            )
            sources = [result["source"] for result in results]
        else:
            documents_summary = "No relevant documents were found."
            sources = []

        # Construct the LLM prompt
        prompt = f"""
        You are an AI assistant is an expert in navigating the social and healthcare system in Canton of Vaud, Switzerland.
        - Based solely on the RELEVANT DOCUMENTS (which is written in French), the USER QUERY and the USER HISTORY, provide the best possible answer to the USER QUERY. 
        **INSTRUCTIONS:**
        - Answer the USER QUERY directly with simple vocabulary and precise sentences. DO NOT repeat the USER QUERY or information. 
        - If there is conflicting information in the RELEVANT DOCUMENTS, prioritize the information in the order they are provided. 
        - STRICTLY use only the information provided in the RELEVANT DOCUMENTS, always cite them while giving answer. 
        - DO NOT invent or use information that is outside of the RELEVANT DOCUMENTS.
        - Ask for more information or to clarify if you don't know the situation.
        - If no Relevant Documents are provided or you don't have the information from the RELEVANT DOCUMENTS, answer in the language of the User Query with the following information:
        "Please contact the following for assistance:
        EVAM - Siège administratif et centre de prestations
        Route de Chavannes 33, 1007 Lausanne
        info@evam.ch
        021 557 06 00
        Monday to Friday from 8h30 to 12h30 and 13h30 to 16h30"
        - IMPORTANT: Always answer in the language of the USER QUERY, not the language of the RELEVANT DOCUMENTS or the USER HISTORY.
        - Double check that your answer is coherent at the end.


        **USER QUERY:**
        {query_text}

        **USER HISTORY:**
        {user_history}

        **RELEVANT DOCUMENTS:**
        {documents_summary}
        """

        # Call the Informaniak API to get the response
        api_response, cost = call_informaniak_api(prompt, 500, 0.5)
        answer_text_lang = translator.detect(api_response.strip()).lang
        answer = api_response.strip()
        print(f"api_response: {api_response}")
        print(f"query_text_lang: {query_text_lang}")
        print(f"answer_text_lang: {answer_text_lang}")

        if (query_text_lang != answer_text_lang):
            answer = translator.translate(answer, src=answer_text_lang, dest=query_text_lang).text

        # Build the final response
        response_data = {
            "answer": answer,
            "sources": sources,
            "cost": cost+embedding_cost
        }

        return jsonify(response_data), 200
    except Exception as e:
        print(f"Error during query processing: {e}")
        return jsonify({"error": f"Error during query processing: {str(e)}"}), 500
