import os
import requests
from typing import Dict, Any

# Environment variables
INFORMANIAK_API_KEY = os.getenv("INFORMANIAK_API_KEY")
INFORMANIAK_PRODUCT_ID = os.getenv("INFORMANIAK_PRODUCT_ID")
INFORMANIAK_API_URL = f"https://api.infomaniak.com/1/ai/{INFORMANIAK_PRODUCT_ID}/openai/chat/completions"


def call_informaniak_api(prompt: str, user_query: str = "", user_history: list = [], max_tokens = 1000, 
                         temperature: float = 0.5, frequency_penalty: float = 0, 
                         presence_penalty: float = 0, model: str = "reasoning") -> str:
    """
    Makes a call to the Informaniak API with the given prompt and returns the response.

    Args:
        prompt (str): The prompt to send to the API.
        model (str): The model to use for the API call (default: "granite").
        temperature (float): The temperature for the generation (default: 0.5).

    Returns:
        str: The response content from the API.
    """
    headers = {
        "Authorization": f"Bearer {INFORMANIAK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            *user_history,
            {"role": "user", "content": user_query},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
    }

    try:
        response = requests.post(INFORMANIAK_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        # Extract the content and token usage
        content = data["choices"][0]["message"]["content"]
        input_tokens = data["usage"]["input_tokens"]
        output_tokens = data["usage"]["output_tokens"]

        # Log token usage and cost
        total_tokens = input_tokens + output_tokens
        cost = input_tokens / 10000 * 0.01 + output_tokens / 10000 * 0.03
        print(f"Tokens in: {input_tokens}")
        print(f"Tokens out: {output_tokens}")
        print(f"Total tokens used: {total_tokens}")
        print(f"Total cost: ${cost:.4f}")

        return content, cost
    except requests.exceptions.RequestException as e:
        print(f"Error during Informaniak API request: {e}")
        raise
    except KeyError as e:
        print(f"Unexpected response structure: {e}")
        raise

def generate_embedding_with_infomaniak(content: str, model: str = "bge_multilingual_gemma2") -> list:
    """
    Generates embeddings for the given content using Informaniak's API.

    Args:
        content (str): The content to generate embeddings for.
        model (str): The embedding model to use (default: "bge_multilingual_gemma2").

    Returns:
        list: The embedding vector.
    """
    embedding_url = f"https://api.infomaniak.com/1/ai/{INFORMANIAK_PRODUCT_ID}/openai/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {INFORMANIAK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": [content],
        "model": model,
    }

    try:
        response = requests.post(embedding_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Extract the content and token usage
        total_tokens = data["usage"]["total_tokens"]

        # Log token usage and cost
        cost = total_tokens / 1000000 * 0.065
        
        print(f"Total tokens used: {total_tokens}")
        print(f"Total cost: ${cost:.4f}")

        return data["data"][0]["embedding"], cost
    except requests.exceptions.RequestException as e:
        print(f"Error during Informaniak embedding request: {e}")
        raise
    except KeyError as e:
        print(f"Unexpected response structure: {e}")
        raise
