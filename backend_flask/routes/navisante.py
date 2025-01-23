from flask import Blueprint, request, jsonify
from services.database import query_document
from services.scraper import scrape_website
from services.api_handler import generate_embedding_with_infomaniak
from services.database import store_in_db, extract_and_match_keywords

navisante_bp = Blueprint('navisante', __name__)

@navisante_bp.route('/query', methods=['POST'])
def query_document_navisante():
    return query_document()

@navisante_bp.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get("url")
    depth = data.get("depth", 1)
    max_pages = data.get("maxPages", 1)
    user_keywords = data.get("keywords", [])

    # Ensure user_keywords is a list and remove empty/whitespace-only entries
    if isinstance(user_keywords, list):
        user_keywords = [kw.strip() for kw in user_keywords if kw.strip()]
    else:
        user_keywords = []

    print(f"URL: {url}, Depth: {depth}, Max Pages: {max_pages}")
    print(f"User Keywords: {user_keywords}")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        # Scrape the website
        scraped_data = scrape_website(url, depth, max_pages)
        print(f"Scraped Data: {scraped_data}")
        for entry in scraped_data:
            content = entry["content"]
            page_url = entry["url"]
            embedding = generate_embedding_with_infomaniak(content)

            # Combine extracted and user-provided keywords
            extracted_keywords = extract_and_match_keywords(content)
            print(f"extracted_keywords: {extracted_keywords}")
            combined_keywords = list(set(extracted_keywords + user_keywords))  # Ensure no duplicates
            print(f"combined_keywords: {combined_keywords}")

            # Store content in the database
            store_in_db(content, embedding, page_url, combined_keywords)

        return jsonify({"message": f"Contenu ajouté pour {url}."}), 200
    except Exception as e:
        print(f"Error during scraping: {e}")
        return jsonify({"error": f"Erreur lors du processus d'ajout: {str(e)}"}), 500
    