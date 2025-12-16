
import os
import re
import json
from datetime import datetime
from typing import List

import imaplib
import email
import ssl
import requests
from email.policy import default
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from config import IMAP_HOST, IMAP_PORT, EMAIL_TEMP_DIR  # pylint: disable=import-error

#I disable this warning because it doesn't affect our use case
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Create temp email directory if it doesn't exist
os.makedirs(EMAIL_TEMP_DIR, exist_ok=True)

# Load credentials from secrets.json
with open("secrets.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)

USER = secrets["USER_ZDV"]       # ZDV Login
PASSWORD = secrets["USER_PASSWORD"]  # ZDV password

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
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', "ilias", "ilias3"
]


# -------- URL Extraction Functions --------

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


def fetch_url_content(url: str) -> str | None:
    """
    Fetch and extract main text content from a URL.
    Returns the extracted text content or None if failed.
    """
    try:

        # Set a user-agent to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Make HTTP GET request
        response = requests.get(url, headers=headers, timeout=URL_REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Limit content length
        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "..."
        
        return text
    
    except requests.RequestException as e:
        print(f"[download_latest_emails] Failed to fetch URL: {url}: {e}")
        return None
    except Exception as e:  # pylint: disable=broad-except
        print(f"[download_latest_emails] Error processing URL: {url}: {e}")
        return None


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

# -------- Email download function --------
def download_latest_emails(limit: int = 50) -> None:
    """
    Download the latest `limit` emails, save each as a separate .txt file,
    and also return ONE big string with all emails concatenated.
    
    For each email, URLs are extracted and their content is fetched,
    then included directly after the email body for LLM context.
    """

    # ---- connect and login ----
    context = ssl.create_default_context()
    M = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=context) # connect to server
    M.login(USER, PASSWORD)
    M.select("Inbox") # select inbox

    # ---- search and fetch emails ----
    # get all email UIDs.
    typ, data = M.search(None, "ALL")  # pylint: disable=unused-variable
    all_uids = data[0].split() # list of all email UIDs
    uids = all_uids[-limit:] # get the latest `limit` UIDs

    combined_chunks: List[str] = [] # List of email text blocks

    # ---- process each email ----
    for i, uid in enumerate(uids, 1):

        # ---- fetch email ----
        # RFC822 gets the full raw email text
        typ, msg_data = M.fetch(uid, "(RFC822)")  # pylint: disable=unused-variable
        raw = msg_data[0][1] #[0] is the tuple, [1] is the raw email bytes
        em = email.message_from_bytes(raw, policy=default) # parse email

        # ---- extract plain text body ----
        text = None

        # try to get plain text part directly. Multipart emails have multiple sections including attachments
        if em.is_multipart():
            for part in em.walk():
                # look for plain text parts without a content disposition. Content disposition is used for attachments
                if (
                    part.get_content_type() == "text/plain"
                    and not part.get_content_disposition()
                ):
                    text = part.get_content()
                    break
        else:
            # try to get plain text part directly. Non-multipart emails have a single section
            if em.get_content_type() == "text/plain":
                text = em.get_content()

        # ---- if no plain text, try HTML ----
        if text is None:
            
            # try to get HTML part and convert to text
            for part in em.walk():
                if part.get_content_type() == "text/html":
                    html = part.get_content()

                    # BeautifulSoup is used to convert HTML to plain text. It is a library for parsing HTML.
                    text = BeautifulSoup(html, "lxml").get_text("\n")
                    break

        # ---- if still no text, use placeholder ----
        subject = em.get("subject") or ""
        sender = em.get("from") or ""
        body = text or "[no text body]"

        # ---- filter for "Rundmail" emails ----
        if ("rundmail" in body.lower()) or ("wiwinews" in body.lower()):
            
            # ---- fetch URL content for this email ----
            print(f"[download_latest_emails] Processing email {i}: extracting URLs...")
            url_contents = fetch_urls_for_email(body)
            url_content_block = format_url_content_block(url_contents)
            
            if url_contents:
                print(f"[download_latest_emails] Fetched content from {len(url_contents)} URLs for email {i}")
            
            # ---- save per-email .txt file ----
            per_email_path = os.path.join(EMAIL_TEMP_DIR, f"msg_{i:04d}.txt")

            # write to file including Subject and From headers for context
            with open(per_email_path, "w", encoding="utf-8") as per_email_file:
                per_email_file.write(f"Subject: {subject}\n")
                per_email_file.write(f"From: {sender}\n\n")
                per_email_file.write(body + "\n")
                if url_content_block:
                    per_email_file.write(url_content_block + "\n")

            # ---- prepare combined string for LLM to process ----
            # Include URL content right after the email body
            email_block = (
                f"--------------- EMAIL: {i} Start ---------------\n"
                f"Subject: {subject}\n"
                f"From: {sender}\n\n"
                f"Body: {body}\n"
                f"{url_content_block}"
                f"--------------- EMAIL: {i} End ---------------\n"
            )

            # Append this email block to the list
            combined_chunks.append(email_block)

    # ---- logout from the email server ----
    M.logout()

    # --- combine all email blocks into one string ----
    combined_string = "\n\n".join(combined_chunks)

    # ---- delete old email .txt files ----
    for fname in os.listdir(EMAIL_TEMP_DIR):
        if fname.lower().endswith(".txt"):
            try:
                os.remove(os.path.join(EMAIL_TEMP_DIR, fname))
            except OSError:
                pass

    # ---- save combined all_emails.txt file ----
    all_path = os.path.join(EMAIL_TEMP_DIR, "all_emails.txt")

    with open(all_path, "w", encoding="utf-8") as all_path_files:
        all_path_files.write(combined_string)

    # ---- print status ----
    print(
        f"[{datetime.now().isoformat(timespec='seconds')}] "
        f"Saved concatenated email file: {all_path}"
    )