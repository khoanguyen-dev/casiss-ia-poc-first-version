import weaviate
from weaviate.classes.config import Configure
from playwright.sync_api import sync_playwright
import requests
from weaviate.classes.config import Property, DataType, Configure

client = weaviate.connect_to_local()

# Define the collection configuration for "WebPage"
webpage_collection = {
    "name": "WebPage",
    "description": "A collection representing web pages with content and URL.",
    "properties": [
        Property(name="content", data_type=DataType.TEXT),
        Property(name="url", data_type=DataType.TEXT),
    ],
    "vectorizer_config": Configure.Vectorizer.none(),  # Indicate that vectors will be provided manually
}

# Check if the "WebPage" collection exists
if not client.collections.exists("WebPage"):
    # Create the "WebPage" collection since it doesn't exist
    client.collections.create(**webpage_collection)
    print('Collection "WebPage" has been created.')
else:
    print('Collection "WebPage" already exists.')

# Function to generate embeddings using Infomaniak's API
def generate_embedding(text):
    api_url = "https://api.infomaniak.com/ai/your_product_id/openai/v1/embeddings"
    headers = {
        "Authorization": "Bearer sCx9Z0_nHFOOAUBVzdsNKGmNVd8nZfgkEflXHpbUGhkNv5AzPdGOnid_FB3Cfdq4Me5DXUUjNLwRB33x",
        "Content-Type": "application/json",
    }
    data = {
        "input": text,
        "model": "bge_multilingual_gemma2",
    }
    response = requests.post(api_url, headers=headers, json=data)
    response.raise_for_status()
    embedding = response.json()["data"][0]["embedding"]
    return embedding

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

data = scrape_website("https://www.evam.ch/", 1, 1)
collection = client.collections.get("WebPage")
# Add scraped data to Weaviate with custom vectors
with client.batch as batch:
    for item in data:
        embedding = generate_embedding(item["content"])
        batch.add_data_object(
            {
                "content": item["content"],
                "url": item["url"],
            },
            class_name="WebPage",
            vector=embedding,
        )

client.close()  # Free up resources