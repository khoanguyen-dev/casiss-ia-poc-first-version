import unicodedata
import validators
from datetime import datetime, date, time
from typing import Union, List
import re
import json

def normalize_text(text: str) -> str:
    """
    Normalize text by removing accents and converting to lowercase.

    Args:
        text (str): Input text.

    Returns:
        str: Normalized text.
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def serialize_value(value: Union[datetime, date, time, None]) -> Union[str, None]:
    """
    Converts non-JSON-serializable objects to strings (ISO 8601 format).

    Args:
        value (Union[datetime, date, time, None]): The value to serialize.

    Returns:
        Union[str, None]: Serialized value.
    """
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value

def serialize_entry(entry: dict) -> dict:
    """
    Serializes all values in a dictionary to ensure JSON compatibility.

    Args:
        entry (dict): The dictionary to serialize.

    Returns:
        dict: The serialized dictionary.
    """
    return {key: serialize_value(value) for key, value in entry.items()}

def truncate_content(content: str, max_length: int = 4000) -> str:
    """
    Truncate content to avoid exceeding length limits.

    Args:
        content (str): Input content.
        max_length (int): Maximum allowed length.

    Returns:
        str: Truncated content.
    """
    return content[:max_length]

def convert_to_boolean(value: str) -> bool:
    """
    Convert a string value to boolean.

    Args:
        value (str): Input string.

    Returns:
        bool: True if the value represents a truthy value, otherwise False.
    """
    truthy_values = {'true', 'yes', '1', 'y'}
    return str(value).strip().lower() in truthy_values


def filter_irrelevant_links(links: List[str]) -> List[str]:
    """
    Filter out irrelevant or non-informative links.

    Args:
        links (List[str]): List of URLs.

    Returns:
        List[str]: Filtered list of URLs.
    """
    irrelevant_domains = ['google.com', 'google.ch', 'support.google', 'microsoft.com', 'bing.com', 'bingj.com', 'go.microsoft.com',
        'support.microsoft.com', 'answers.microsoft.com']
    return [link for link in links if not any(domain in link for domain in irrelevant_domains)]

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

def is_valid_link(link):
    """Check if the link is valid and starts with http/https."""
    return link and link.startswith(('http://', 'https://')) and validators.url(link)

def split_text_with_overlap(text, max_tokens=100, overlap_sentences=2, newline_replacement=" "):
    """
    Splits text into chunks of approximately max_tokens words while keeping sentence integrity.
    Includes overlapping sentences and replaces newlines/tabs with a space or dot.

    Parameters:
    - text (str): The text to be split.
    - max_tokens (int): The max number of tokens per chunk.
    - overlap_sentences (int): Number of overlapping sentences between chunks.
    - newline_replacement (str): Character(s) to replace newlines/tabs (default: " . ").

    Returns:
    - list of str: The split text chunks.
    """
    # Normalize multiple newlines & tabs into a single separator
    text = re.sub(r'\n[\t ]*\n', newline_replacement, text)  # Convert multiple newlines/tabs into a dot or space
    text = re.sub(r'\t+', ' ', text)  # Convert multiple tabs into a single space
    text = re.sub(r'\n+', newline_replacement, text)  # Convert single newlines to dots or spaces

    # Split text into meaningful chunks using both sentence and paragraph boundaries
    sentences = re.split(r'(?<=[.!?])\s+|\n\n', text)

    chunks = []
    current_chunk = []
    current_length = 0
    previous_sentences = []

    for sentence in sentences:
        token_count = len(sentence.split())  # Approximate token count

        if current_length + token_count > max_tokens:
            # Save the current chunk and start a new one with overlapping sentences
            chunks.append(" ".join(current_chunk))

            # Keep last `overlap_sentences` for context in the next chunk
            current_chunk = previous_sentences[-overlap_sentences:] + [sentence]
            current_length = sum(len(sent.split()) for sent in current_chunk)
        else:
            # Add the sentence to the current chunk
            current_chunk.append(sentence)
            current_length += token_count

        # Store sentences for overlap reference
        previous_sentences.append(sentence)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def extract_json(text: str):
    """Extracts JSON from a string if needed"""
    try:
        # Try parsing as direct JSON first
        return json.loads(text)
    except json.JSONDecodeError:
        pass  # Proceed to regex extraction

    # Attempt to extract JSON part from text
    match = re.search(r'\[.*\]|\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as e:
            print(f"Error extracting JSON: {e}")
    
    return []  # Return empty list if extraction fails
