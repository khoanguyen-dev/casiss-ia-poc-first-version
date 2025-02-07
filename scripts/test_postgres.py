import requests
import json
import psycopg2
from playwright.sync_api import sync_playwright
from flask import Flask, request, jsonify
from flask_cors import CORS
from psycopg2 import connect
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
# Enable CORS for the entire app
CORS(app)

DB_CONFIG = {
    "dbname": "casiss_ia",
    "user": "khoa",
    "password": "k123",
    "host": "localhost"
}

import re
from collections import Counter
import unicodedata

def extract_keywords(content, top_n=5):
    # Normalize text (e.g., remove accents)
    def normalize(text):
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )

    # Common French stopwords
    french_stopwords = {
        'et', 'le', 'la', 'les', 'un', 'une', 'des', 'dans', 'du', 'de', 'que', 'qui',
        'au', 'aux', 'par', 'pour', 'avec', 'ce', 'ces', 'cette', 'ou', 'sur', 'se',
        'son', 'sa', 'leurs', 'nos', 'votre', 'vos', 'comme', 'en', 'il', 'elle',
        'on', 'nous', 'vous', 'ils', 'elles', 'y', 'est', 'a', 'd', 'l', 'm', 'n',
        's', 't', 'c', 'qu', 'ne', 'pas', 'plus', 'mes', 'ses', 'ma', 'mon'
    }

    # Normalize content and extract words
    words = re.findall(r'\b\w+\b', normalize(content.lower()))
    filtered_words = [word for word in words if word not in french_stopwords and len(word) > 3]
    
    # Count keyword occurrences
    keyword_counts = Counter(filtered_words)
    return [word for word, _ in keyword_counts.most_common(top_n)]

def scrape_website(url, depth, max_pages):
    scraped_data = []
    visited_urls = set()

    def crawl(current_url, current_depth, browser):
        if current_depth > depth or len(visited_urls) >= max_pages:
            return
        if current_url in visited_urls:
            return
        visited_urls.add(current_url)

        try:
            page = browser.new_page()
            page.goto(current_url, timeout=60000)
            text = page.evaluate("""() => document.body.innerText""")  # Extract text content
            scraped_data.append({"url": current_url, "content": text})

            # Find and crawl other links
            links = page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
            for link in links:
                if link.startswith("http"):  # Only follow valid URLs
                    crawl(link, current_depth + 1, browser)
        except Exception as e:
            print(f"Error scraping {current_url}: {e}")
        finally:
            page.close()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            crawl(url, 0, browser)
            browser.close()
    except Exception as e:
        print(f"Error initializing Playwright: {e}")

    return scraped_data

def generate_embedding_with_infomaniak(content):
    print("Content to be included: ", content)

    url = "https://api.infomaniak.com/1/ai/566/openai/v1/embeddings"
    headers = {
        "Authorization": "Bearer sCx9Z0_nHFOOAUBVzdsNKGmNVd8nZfgkEflXHpbUGhkNv5AzPdGOnid_FB3Cfdq4Me5DXUUjNLwRB33x",
        "Content-Type": "application/json"
    }
    data = {
        "input": [content],
        "model": "bge_multilingual_gemma2"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)  # Use json= instead of data=
        response.raise_for_status()  # Raise HTTPError for bad responses
        res = response.json()
        print("API Response: ", res)
        return res['data'][0]['embedding']  # Extract the embedding
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except KeyError as e:
        print(f"Error in API response structure: {e}")
        return None

# Store scraped data in the database
def store_in_db(content, embedding, url, keywords):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO navisante (content, embedding, url, keywords)
        VALUES (%s, %s, %s, %s);
        """,
        (content, embedding, url, keywords)
    )
    conn.commit()
    cur.close()
    conn.close()
    
def query_db(query_embedding, keywords, top_k=5):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # Filter by keywords if provided
    if keywords:
        cur.execute(
            """
            SELECT content, url, 1 - (embedding <=> %s::vector) AS similarity
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
            SELECT content, url, 1 - (embedding <=> %s::vector) AS similarity
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

# Scrape website route
@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get("url")
    depth = data.get("depth", 1)
    max_pages = data.get("max_pages", 10)

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        # Scrape the website
        scraped_data = scrape_website(url, depth, max_pages)
        for entry in scraped_data:
            content = entry["content"]
            page_url = entry["url"]
            embedding = generate_embedding_with_infomaniak(content)
            keywords = extract_keywords(content)  # Use your keyword extraction function
            store_in_db(content, embedding, page_url, keywords)
        return jsonify({"message": f"Scraping completed for {url}."}), 200
    except Exception as e:
        return jsonify({"error": f"Error during scraping: {str(e)}"}), 500

# Query route
@app.route('/query', methods=['POST'])
def query():
    data = request.json
    query_text = data.get("query")

    if not query_text:
        return jsonify({"error": "Query text is required"}), 400

    try:
        keywords = extract_keywords(query_text)  # Extract keywords from user input
        query_embedding = generate_embedding_with_infomaniak(query_text)  # Generate embedding
        results = query_db(query_embedding, keywords)

        if results:
            response_data = {
                "answer": "Here are the most relevant results.",
                "sources": [result["url"] for result in results],
            }
        else:
            response_data = {"answer": "No relevant documents found.", "sources": []}
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": f"Error during query processing: {str(e)}"}), 500
    
if __name__ == '__main__':
    app.run(debug=True)

# 1. Scrape the website
#url_to_scrape = "https://www.evam.ch/"
#depth = 1
#max_pages = 1

#scraped_data = scrape_website(url_to_scrape, depth, max_pages)

# 2. Process and store scraped data
#process_and_store_scraped_data(scraped_data)
#keywords = ['migrant']  # Extract or define keywords
#store_in_db_with_keywords(content, embedding, "https://www.evam.ch/", keywords)