import requests
from bs4 import BeautifulSoup
import spacy

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

def spacy_split_text(text, max_tokens=2000):  # Increased max_tokens to 2000
    """
    Splits text into larger chunks using SpaCy.

    Parameters:
    - text (str): The input text to be split.
    - max_tokens (int): The max number of words (approximate tokens) per chunk.

    Returns:
    - list: A list of text chunks, each within the token limit.
    """
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        token_count = len(sentence.split())

        if current_length + token_count > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = token_count
        else:
            current_chunk.append(sentence)
            current_length += token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# Scrape an HTML page and extract text
url = "https://renens.ch/culture-et-loisirs/index.php"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Extract text from paragraphs
extracted_text = " ".join([p.get_text() for p in soup.find_all("p")])

# Increase max tokens per chunk
chunks = spacy_split_text(extracted_text, max_tokens=2000)  # Increased to 2000 tokens per chunk

# Print the split chunks
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1} (approx. {len(chunk.split())} tokens):\n{chunk}\n")