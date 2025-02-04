import fitz 
import os
from flask import Blueprint, request, jsonify
from services.database import query_document
from services.scraper import scrape_website
from services.api_handler import generate_embedding_with_infomaniak
from services.database import store_in_db
from multi_rake import Rake
from werkzeug.utils import secure_filename
from io import BytesIO
from PyPDF2 import PdfReader

navisante_bp = Blueprint('navisante', __name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@navisante_bp.route('/query', methods=['POST'])
def query_document_navisante():
    return query_document()

@navisante_bp.route('/scrape', methods=['POST'])
def scrape():
    if 'pdf' in request.files:  # Check if a PDF file is uploaded
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        filename = secure_filename(pdf_file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(file_path)
        
        content = extract_text_from_pdf(file_path)
        
        embedding = generate_embedding_with_infomaniak(content)
        rake = Rake(language_code='fr', max_words=2)
        keywords = rake.apply(content)
        top_keywords = [keyword for keyword, score in keywords]
        
        store_in_db(content, embedding, file_path, top_keywords)
        
        return jsonify({"message": "PDF content processed and stored.", "keywords": top_keywords}), 200
    
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

    for url in urls:
        print(f"Processing URL: {url}")

        if url.lower().endswith('.pdf'):
            content = extract_text_from_pdf_url(url)
        else:
            scraped_data = scrape_website(url, depth, max_pages)
            content = " ".join(entry["content"] for entry in scraped_data)

        embedding = generate_embedding_with_infomaniak(content)
        keywords = rake.apply(content)
        top_keywords = [keyword for keyword, score in keywords]
        combined_keywords = list(set(top_keywords + user_keywords))

        store_in_db(content, embedding, url, combined_keywords)

    return jsonify({"message": "Toutes les ressources sont ajoutées."}), 200

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
        response = request.get(pdf_url)
        if response.status_code == 200:
            pdf_bytes = BytesIO(response.content)
            reader = PdfReader(pdf_bytes)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            return text
    except Exception as e:
        print(f"Error fetching or processing PDF from URL: {e}")
    return ""
