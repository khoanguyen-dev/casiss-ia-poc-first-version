import os
import psycopg2
import json
import pandas as pd
from services.scraper import scrape_google, scrape_website, scrape_bing
from flask import request, jsonify, stream_with_context, Response
from datetime import datetime
from threading import Lock
from rapidfuzz import fuzz
from services.utils import serialize_value, serialize_entry
from psycopg2.extras import RealDictCursor
from services.api_handler import generate_embedding_with_infomaniak, call_informaniak_api
from models.annuaire import AnnuaireEntries
from models.evenement import EvenementEntries
from pydantic import ValidationError
from typing import List
import re
from collections import Counter

# Limit the number of entries processed
MAX_UPDATE_ENTRIES = 5
MAX_GOOGLE_SEARCH = 3
MAX_TOP_DOCUMENT_SEARCH = 3
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

    for entry in entries:
        print("Entry:", entry)
        try:
            entry_dict = serialize_entry(entry.dict())
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

def replace_entry(table_name):
    try:
        entry = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        print(f"Data received for replacement: {entry}")
        
        processed_entry = {k: (None if v == "" else v) for k, v in entry.items()}

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
                #search_results = scrape_google(title, first_name, last_name, zip_code)
                search_results = scrape_bing(title, first_name, last_name, zip_code)

                # If no results, update `date_derniere_modification`
                if not search_results:
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
                print(f"google_results: {search_results}...")
                for result in search_results:
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

def store_in_db(content, embedding, url, keywords):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO documents (content, embedding, url, keywords)
            VALUES (%s, %s, %s, %s);
            """,
            (content, embedding, url, keywords)
        )
        conn.commit()
    except Exception as e:
        print(f"Error storing data: {e}")
    finally:
        cur.close()
        conn.close()

def query_db(query_embedding, keywords, top_k=MAX_TOP_DOCUMENT_SEARCH):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Filter by keywords if provided
    if keywords:
        cur.execute(
            """
            SELECT content, url, 1 - (embedding <=> %s::vector) AS similarity
            FROM documents
            WHERE keywords && %s::TEXT[] -- Array overlap operator
            ORDER BY similarity DESC
            LIMIT %s;
            """,
            (query_embedding, keywords, top_k)
        )
    else:
        cur.execute(
            """
            SELECT content, url, 1 - (embedding <=> %s::vector) AS similarity
            FROM documents
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
        # Extract keywords and generate embedding
        keywords = extract_and_match_keywords(query_text)  # List of keywords
        query_embedding = generate_embedding_with_infomaniak(query_text)  # Embedding vector
        print(f"Generated query_embedding: {query_embedding}")

        # Ensure query_embedding is a PostgreSQL-compatible vector string
        query_embedding = f"[{','.join(map(str, query_embedding))}]"

        # Query the database
        results = query_db(query_embedding, keywords)
        print(f"Query results: {results}")

        # Prepare the `Relevant Documents` section
        if results:
            documents_summary = "\n\n".join(
                [
                    f"Document {idx + 1}:\nContent: {doc['content']}\nSource: {doc['url']}"
                    for idx, doc in enumerate(results)
                ]
            )
            sources = [result["url"] for result in results]
        else:
            documents_summary = "No relevant documents were found."
            sources = []

        # Construct the LLM prompt
        prompt = f"""
        AI assistant is an expert in navigating the healthcare system in Canton of Vaud, Switzerland. 
        The traits of the AI include expert knowledge, helpfulness, cleverness, and articulateness.
        IMPORTANT: Alway respond in the language of the user query.

        Below is a query from the user and relevant documents. If there is conflicting information between documents, prioritize the order they are provided. 
        If no relevant documents are provided, respond with:
        "I'm sorry, but I don't know the answer to that question. 
        Please contact the following for assistance:

        Siège administratif et centre de prestations
        Route de Chavannes 33, 1007 Lausanne
        info@evam.ch
        021 557 06 00
        Lundi au vendredi de 8h30 à 12h30 et 13h30 à 16h30"

        Do not invent any information that is not directly drawn from the documents.

        User Query: {query_text}
        User History: {user_history}

        Relevant Documents:
        {documents_summary}

        Based on this information, provide the best possible answer to the user query.
        """
        print(f"Prompt sent to LLM:\n{prompt}")

        # Call the Informaniak API to get the response
        ai_response = call_informaniak_api(prompt)
        print(f"AI Response: {ai_response}")

        # Build the final response
        response_data = {
            "answer": ai_response.strip(),
            "sources": sources,
        }

        return jsonify(response_data), 200
    except Exception as e:
        print(f"Error during query processing: {e}")
        return jsonify({"error": f"Error during query processing: {str(e)}"}), 500

def extract_and_match_keywords(content: str, top_n: int = 5, language: str = "fr") -> List[str]:
    """
    Extract the top N keywords from the content and match them with existing keywords in the database.

    Args:
        content (str): Input content.
        top_n (int): Number of top keywords to extract.
        language (str): Language for stopwords (default: "fr").

    Returns:
        List[str]: Combined list of extracted keywords and matching database keywords.
    """
    # Define stopwords for the given language
    stopwords = {
        'fr': {'et', 'le', 'la', 'les', 'un', 'une', 'des', 'dans', 'du', 'de', 'que', 'qui',
               'au', 'aux', 'par', 'pour', 'avec', 'ce', 'ces', 'cette', 'ou', 'sur', 'se',
               'son', 'sa', 'leurs', 'nos', 'votre', 'vos', 'comme', 'en', 'il', 'elle',
               'on', 'nous', 'vous', 'ils', 'elles', 'y', 'est', 'a', 'd', 'l', 'm', 'n',
               's', 't', 'c', 'qu', 'ne', 'pas', 'plus', 'mes', 'ses', 'ma', 'mon'},
    }.get(language, set())

    # Normalize content and tokenize words
    words = re.findall(r'\b\w+\b', content.lower())
    filtered_words = [word for word in words if word not in stopwords and len(word) > 3]

    # Count word occurrences to identify potential keywords
    keyword_counts = Counter(filtered_words)
    top_keywords = [word for word, _ in keyword_counts.most_common(top_n)]
    print(f"top_keywords: {top_keywords}")

    # Fetch existing keywords from the database
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT DISTINCT UNNEST(keywords) AS keyword FROM documents;")
        existing_keywords = [row["keyword"] for row in cur.fetchall()]
        print(f"existing_keywords: {existing_keywords}")
        if not existing_keywords:
            existing_keywords = []  # Handle empty result gracefully
    finally:
        cur.close()
        conn.close()

    # Match existing keywords with the content
    matching_keywords = [kw for kw in existing_keywords if kw in content.lower()]

    # Combine extracted keywords and matching database keywords
    combined_keywords = list(set(top_keywords + matching_keywords))

    return combined_keywords
