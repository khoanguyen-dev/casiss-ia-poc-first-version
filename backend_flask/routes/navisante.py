import fitz 
import os
import json
import requests
from flask import Blueprint, request, jsonify
from services.database import query_document, fetch_table_entries, store_in_db
from services.scraper import scrape_website
from services.api_handler import generate_embedding_with_infomaniak
from multi_rake import Rake
from werkzeug.utils import secure_filename
from io import BytesIO
from PyPDF2 import PdfReader

navisante_bp = Blueprint('navisante', __name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@navisante_bp.route('/get', methods=['GET'])
def get_navisante_entries():
    return fetch_table_entries('navisante')

@navisante_bp.route('/query', methods=['POST'])
def query_document_navisante():
    return query_document()

@navisante_bp.route('/scrape', methods=['POST'])
def scrape():
    total_cost = 0
    rake = Rake(language_code='fr', max_words=3)
    if 'pdf' in request.files:  # Handle PDF upload
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        filename = secure_filename(pdf_file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(file_path)
        
        content = extract_text_from_pdf(file_path)
        
        embedding, cost = generate_embedding_with_infomaniak(content)
        total_cost += cost
        keywords = rake.apply(content)
        top_keywords = [keyword for keyword, score in keywords]
        
        store_in_db(content, embedding, file_path, top_keywords)
        
        return jsonify({"message": "PDF content processed and stored.", "keywords": top_keywords}), 200

    # Ensure correct parsing of form data
    urls = request.form.get("urls", "[]")  # Default to empty list string
    depth = int(request.form.get("depth", 1))
    max_pages = int(request.form.get("maxPages", 1))
    user_keywords = request.form.get("keywords", "")

    # Convert JSON string to Python list
    try:
        urls = json.loads(urls)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid URL list format"}), 400

    if isinstance(user_keywords, str):
        user_keywords = [kw.strip() for kw in user_keywords.split(",") if kw.strip()]
    else:
        user_keywords = []

    if not urls or not isinstance(urls, list):
        return jsonify({"error": "URLs must be provided as a list"}), 400

    print(f"URLs: {urls}, Depth: {depth}, Max Pages: {max_pages}")
    print(f"User Keywords: {user_keywords}")

    for url in urls:
        print(f"Processing URL: {url}")

        if url.lower().endswith('.pdf'):
            content = extract_text_from_pdf_url(url)
        else:
            scraped_data = scrape_website(url, depth, max_pages)
            content = " ".join(entry["content"] for entry in scraped_data)

        embedding, cost = generate_embedding_with_infomaniak(content)
        total_cost += cost
        keywords = rake.apply(content)
        top_keywords = [keyword for keyword, score in keywords]
        combined_keywords = list(set(top_keywords + user_keywords))

        store_in_db(content, embedding, url, combined_keywords)

    return jsonify({"message": "Toutes les ressources sont ajoutées.", "cost": total_cost}), 200

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text

def extract_text_from_pdf_url(pdf_url):
    try:
        response = requests.get(pdf_url)  # Correctly use requests.get()
        response.raise_for_status()  # Raise an error for bad responses

        pdf_bytes = BytesIO(response.content)
        reader = PdfReader(pdf_bytes)
        text = "\n\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PDF from URL: {e}")
    except Exception as e:
        print(f"Error processing PDF: {e}")

    return ""
