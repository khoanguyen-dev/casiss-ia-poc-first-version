from flask import Blueprint, request, jsonify
from services.database import query_document
from services.scraper import scrape_website
from services.api_handler import generate_embedding_with_infomaniak
from services.database import store_in_db
from multi_rake import Rake

navisante_bp = Blueprint('navisante', __name__)

@navisante_bp.route('/query', methods=['POST'])
def query_document_navisante():
    return query_document()

@navisante_bp.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    urls = data.get("urls", [])  # Updated to handle multiple URLs
    depth = data.get("depth", 1)
    max_pages = data.get("maxPages", 1)
    user_keywords = data.get("keywords", [])
    rake = Rake(language_code='fr', max_words=2)

    # Ensure user_keywords is a list and remove empty/whitespace-only entries
    if isinstance(user_keywords, list):
        user_keywords = [kw.strip() for kw in user_keywords if kw.strip()]
    else:
        user_keywords = []

    if not urls or not isinstance(urls, list):
        return jsonify({"error": "URLs must be provided as a list"}), 400

    print(f"URLs: {urls}, Depth: {depth}, Max Pages: {max_pages}")
    print(f"User Keywords: {user_keywords}")

    try:
        results = []
        for url in urls:
            print(f"Processing URL: {url}")

            # Scrape the website
            scraped_data = scrape_website(url, depth, max_pages)
            print(f"Scraped Data for {url}: {scraped_data}")

            for entry in scraped_data:
                content = entry["content"]
                page_url = entry["url"]
                embedding = generate_embedding_with_infomaniak(content)

                # Combine extracted and user-provided keywords
                keywords = rake.apply(content)

                # Limit to the top 20 keywords and get only the strings
                top_keywords = [keyword for keyword, score in keywords]
                combined_keywords = list(set(top_keywords + user_keywords))  # Ensure no duplicates

                print(f"Keywords for {page_url}: {top_keywords}")
                print(f"Combined Keywords: {combined_keywords}")

                # Store content in the database
                store_in_db(content, embedding, page_url, combined_keywords)

            results.append({"url": url, "message": f"Content added for {url}."})

        return jsonify({"message": "Toutes les ressources sont ajoutées.", "results": results}), 200
    except Exception as e:
        print(f"Error during scraping: {e}")
        return jsonify({"error": f"Error during the scraping process: {str(e)}"}), 500
    