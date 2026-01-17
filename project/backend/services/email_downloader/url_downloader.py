import re
import requests
from bs4 import BeautifulSoup

#
#   This file defines functions to extract URLs from email bodies
#   and fetch their content for further processing.
#

# -------- URL Extraction and Content Fetching Settings --------

# Timeout for URL requests (seconds)
URL_REQUEST_TIMEOUT = 10
# Maximum number of URLs to fetch per email
MAX_URLS_PER_EMAIL = 3
# Maximum content length per URL (characters)
MAX_CONTENT_LENGTH = 10000

# URL patterns to skip (social media, unsubscribe links, etc.)
SKIP_URL_PATTERNS = [
    'unsubscribe', 'mailto:', 'tel:', 'javascript:',
    'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
    'youtube.com', 'google.com/maps', 'maps.google',
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', "ilias", "ilias3", "alma"
]

CONTENT_SELECTORS = [
    "main",
    "#content",
    "#pageContent",
    "#inhalt",
    ".content",
    ".page-content",
    "div[role='main']",
]

REMOVE_SELECTORS = [
    "script", "style", "nav", "footer", "header", "aside",
    "form",  # often includes the login form noise
    ".navigation", "#navigation", ".menu", ".footer", ".header",
    ".modal", ".cookie", ".breadcrumbs",
]


# -------- URL Extraction and Content Fetching Function --------

def extract_urls_from_text(text: str) -> list[str]:
    """
    Extract unique URLs from text using regex.
    Returns a list of unique URLs found.
    """
    # Regex pattern for URLs
    url_pattern = r'https?://[^\s<>"\')\]}>]+'
    
    urls = re.findall(url_pattern, text)
    
    # Clean up URLs 
    cleaned_urls = []

    for url in urls:
        # Remove trailing punctuation
        url = url.rstrip('.,;:!?')

        # Remove URL fragments
        if url and url not in cleaned_urls:
            cleaned_urls.append(url)
    
    return cleaned_urls


def fetch_urls_for_email(email_body: str) -> dict[str, str]:
    """
    Extract URLs from an email body and fetch their content.
    Returns a dict mapping URL to its content.
    """
    urls = extract_urls_from_text(email_body)
    url_contents = {}
    urls_fetched = 0
    
    for url in urls:
        # Stop if we've fetched enough URLs for this email
        if urls_fetched >= MAX_URLS_PER_EMAIL:
            break
        
        # Skip common non-event URLs
        if any(pattern in url.lower() for pattern in SKIP_URL_PATTERNS):
            continue
        
        print(f"[download_latest_emails] Fetching content from URL: {url}")
        content = fetch_url_content(url)
        
        if content and len(content) > 100:  # Only include if meaningful content
            url_contents[url] = content
            urls_fetched += 1
    
    return url_contents


def format_url_content_block(url_contents: dict[str, str]) -> str:
    """
    Format URL contents into a text block to be appended to an email.
    """
    if not url_contents:
        return ""
    
    lines = ["\n--- URL CONTENT FROM THIS EMAIL ---\n"]
    
    for url, content in url_contents.items():
        lines.append(f"URL: {url}")
        lines.append(f"Content: {content}")
        lines.append("")
    
    return "\n".join(lines)

def extract_main_text(soup: BeautifulSoup) -> str:
    # Try to locate the "main" content area
    container = None
    for sel in CONTENT_SELECTORS:
        container = soup.select_one(sel)
        if container:
            break
    if container is None:
        container = soup  # fallback: whole doc

    # Remove noisy elements inside container
    for sel in REMOVE_SELECTORS:
        for el in container.select(sel):
            el.decompose()

    text = " ".join(container.stripped_strings)
    # Optional: collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

def fetch_url_content(url: str) -> str | None:
    try:
        session = requests.Session()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }

        resp = session.get(url, headers=headers, timeout=URL_REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        text = extract_main_text(soup)

        # If it still looks like mostly boilerplate or JS fallback, you can return it
        # or trigger a fallback (see next section).
        if not text:
            return None

        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "..."

        return text

    except requests.RequestException as e:
        print(f"[fetch_url_content] Failed to fetch URL: {url}: {e}")
        return None
    except Exception as e: #pylint: disable=broad-except
        print(f"[fetch_url_content] Error processing URL: {url}: {e}")
        return None
