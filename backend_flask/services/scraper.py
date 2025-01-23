from playwright.sync_api import sync_playwright
from services.utils import dismiss_popups, is_valid_link, filter_irrelevant_links, truncate_content
from services.api_handler import call_informaniak_api
from models.annuaire import AnnuaireEntries
import json

MAX_UPDATE_ENTRIES = 5
MAX_GOOGLE_SEARCH = 3

def scrape_page(url, page, delay=2000):
    """
    Scrapes content from a single webpage, handling JavaScript-rendered content, toggles, and popups.

    Args:
        url (str): The URL to scrape.
        page (playwright.sync_api.Page): Playwright Page object.
        delay (int): Time to wait after loading the page (in milliseconds).

    Returns:
        str: Extracted visible text content.
    """
    try:
        page.goto(url, timeout=10000)
        page.wait_for_load_state("domcontentloaded")  # Wait for the page to load
        page.wait_for_timeout(delay)  # Wait for a delay to mimic human interaction
        dismiss_popups(page)  # Dismiss any popups or overlays

        # Reveal hidden content by clicking toggles/buttons
        toggles = page.locator("button, .toggle, [data-toggle]")
        for toggle in toggles.all():
            if toggle.is_visible():
                try:
                    toggle.click()
                    page.wait_for_timeout(500)  # Allow DOM updates after clicking
                except Exception as e:
                    print(f"Error clicking toggle: {e}")

        # Extract text content only
        content = page.evaluate("() => document.body.innerText")
        return truncate_content(content)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_website(url, depth, max_pages, delay=2000):
    """
    Recursively scrapes a website up to a specified depth and maximum number of pages.

    Args:
        url (str): The starting URL.
        depth (int): Maximum depth for recursion.
        max_pages (int): Maximum number of pages to scrape.
        delay (int): Time to wait after loading each page (in milliseconds).

    Returns:
        list: A list of dictionaries containing the URL and content of scraped pages.
    """
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
            content = scrape_page(current_url, page, delay)
            if content:
                scraped_data.append({"url": current_url, "content": content})

            # Find and crawl other links
            links = page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
            for link in links:
                if is_valid_link(link) and not link.lower().endswith('.pdf'):
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
    
def scrape_bing(title, first_name, last_name, zip_code, max_results=5, delay=3000):
    """
    Scrapes Bing Search results for relevant data within Switzerland and in French.

    Args:
        title (str): Title of the person (e.g., Dr, Mr, Mrs).
        first_name (str): First name.
        last_name (str): Last name.
        zip_code (str): ZIP code to narrow the search.
        max_results (int): Maximum number of search results to process.
        delay (int): Time to wait after each request (in milliseconds).

    Returns:
        list: A list of dictionaries containing URLs and structured data.
    """
    query = f"{title} {first_name} {last_name} {zip_code}"
    search_url = f"https://www.bing.com/search?q={query}&setlang=fr&cc=CH"  # French results in Switzerland
    collected_entries = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"Scraping Bing results for query: {query}")
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(delay)  # Mimic human interaction
            dismiss_popups(page)

            # Extract and filter links
            result_links = page.locator('li.b_algo a').evaluate_all(
                '(links) => links.map(link => link.href)'
            )
            result_links = filter_irrelevant_links([
                link for link in result_links if is_valid_link(link) and not link.lower().endswith('.pdf')
            ])[:max_results]

            for link in result_links:
                try:
                    print(f"Scraping content from: {link}")
                    page.goto(link, timeout=30000)
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(delay)  # Wait before extracting content
                    dismiss_popups(page)

                    # Extract visible text content only from the page
                    content = page.evaluate("() => document.body.innerText")
                    if content:
                        content = truncate_content(content)

                        # Generate structured data using Informaniak API
                        prompt = f"""
                        Extract structured data in JSON format with multiple entries for a database from the following french text:
                        {content}

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
                        api_response = call_informaniak_api(prompt)
                        print(f"API response: {api_response}")
                        structured_data = AnnuaireEntries(entries=json.loads(api_response)).entries

                        # Append the structured data with the URL
                        collected_entries.append({
                            "url": link,
                            "structured_data": structured_data
                        })

                        print(f"Structured data: {structured_data}")
                except Exception as e:
                    print(f"Error processing {link}: {e}")

            browser.close()

        return collected_entries
    except Exception as e:
        print(f"Error occurred during Bing scraping: {e}")
        return []

def scrape_google(title, first_name, last_name, zip_code, max_results=MAX_GOOGLE_SEARCH):
    """Scrape Google Search results for relevant data within Switzerland and in French."""
    try:
        query = f"{title} {first_name} {last_name} {zip_code}"
        # Add `gl=ch` for geographic location and `cr=countryCH` for country restriction
        search_url = f"https://www.google.com/search?q={query}&hl=fr&gl=ch&cr=countryCH"
        collected_entries = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"Scraping Google results for query: {query}")
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")

            # Dismiss popups
            dismiss_popups(page)

            # Extract URLs
            result_links = page.locator('a').evaluate_all(
                '(links) => links.map(link => link.href)'
            )
            # Filter valid and relevant links
            result_links = [link for link in result_links if is_valid_link(link)]
            result_links = filter_irrelevant_links(result_links)[:max_results]
            # print(f"Filtered {len(result_links)} relevant and valid links.")

            for link in result_links:
                try:
                    print(f"Scraping content from: {link}")
                    page.goto(link, timeout=30000)
                    page.wait_for_load_state("domcontentloaded")
                    dismiss_popups(page)

                    # Extract visible text content only from the page
                    content = page.evaluate("() => document.body.innerText")
                    if content:
                        content = truncate_content(content)
                        # print(f"Scraped content from {link}: {content[:200]}...")

                        # Convert content into structured AnnuaireEntry
                        prompt = f"""
                        Extract structured data in JSON format with multiple entries for a database from the following french text:
                        {content}

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
                    
                        # Call Informaniak API to process the input with the detailed prompt
                        api_response = call_informaniak_api(prompt)
                        structured_data = AnnuaireEntries(entries=json.loads(api_response)).entries
                        
                        # Parse response and add entries with the associated URL
                        collected_entries.append({
                            "url": link,
                            "structured_data": structured_data
                        })

                        print(f"Structured data: {structured_data}")
                except Exception as e:
                    print(f"Error processing {link}: {e}")

            browser.close()

        return collected_entries
    except Exception as e:
        print(f"Error occurred during Google scraping: {e}")
        return []
    