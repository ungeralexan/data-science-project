import json
from typing import Optional, get_origin, get_args
from pathlib import Path
import pandas as pd

from typing import Optional
from pydantic import BaseModel, ValidationError
from google import genai
import json
import re

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "Title": {"type": "STRING", "nullable": True},
        "Start_Date": {"type": "STRING", "nullable": True},
        "End_Date": {"type": "STRING", "nullable": True},
        "Start_Time": {"type": "STRING", "nullable": True},
        "End_Time": {"type": "STRING", "nullable": True},
        "Description": {"type": "STRING", "nullable": True},
        "Location": {"type": "STRING", "nullable": True},
        "Speaker": {"type": "STRING", "nullable": True},
        "Organizer": {"type": "STRING", "nullable": True},
        "Registration_Needed": {"type": "BOOLEAN", "nullable": True},
        "URL": {"type": "STRING", "nullable": True},
    },
    "required": [
        "Title", "Start_Date", "End_Date", "Start_Time", "End_Time",
        "Description", "Location", "Speaker", "Organizer", "Registration_Needed", "URL"
    ],
}


def extract_event_info_with_llm(email_text: str) -> dict:
    system_instruction = (
        "You are a multilingual assistant that extracts event information from email texts according to a given schema. "
        "Only extract if there is a clear event. Keep original date/time formats. If unsure, use null. "
        "Return ONLY a single JSON object with exactly these keys and nothing else: "
        "Title, Start_Date, End_Date, Start_Time, End_Time, Description, Location, Speaker, Organizer, Registration_Needed, URL. "
        "Do NOT wrap in arrays or extra objects; do NOT add extra keys; do NOT use markdown fences. "
        "If there is no clear event, return the same object with all fields set to null."
    )

    user_prompt = f"""

    Extract event information from the following email text.

    Each event must contain the following fields:

    - Title (String): The title or name of the event. 
    - Start_Date (String or null): The starting date of the event.
    - End_Date (String or null): The ending date of the event. 
    - Start_Time (String or null): The starting time of the event.
    - End_Time (String or null): The ending time of the event.
    - Description (String or null): A description of the event that provides more context and details.
    - Location (String or null): The location of the event. If the event is remote or online, specify that.
    - Speaker (String or null): The speaker of the event if available.
    - Organizer (String or null): The organizer of the event if available.
    - Registration_Needed (Boolean or null): Whether registration is needed for the event as true or false.
    - URL (String or null): The URL for more information about the event if available.

    E-Mail Text content:

    {email_text}
    """

    contents = f"{system_instruction}\n\n{user_prompt}"

    # read API key from your existing secrets.json
    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)

    client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config={
            "response_mime_type": "application/json",
            "response_schema": SCHEMA,  # <— schema derived from Pydantic
        },
    )

    return json.loads(resp.text)

def process_all_emails(folder_path):
    """
        This function processes all email text files in the specified folder,
        extracts event information using the LLM, and saves the results to an Excel file.
    """

    # List to store results
    results = []

    # Iterate over all .txt files in the specified folder
    for email_file in Path(folder_path).glob("*.txt"):

        print(f"Processing: {email_file.name}")

        # Read the email text content
        email_text = email_file.read_text(encoding="utf-8", errors="strict")

        # Add source file information
        results.append(extract_event_info_with_llm(email_text))

    # Create a DataFrame from the results
    df_results = pd.DataFrame(results)

    # Save the results to an Excel file
    df_results.to_csv("extracted_event_info.csv", index=False)

    print("Results saved!")

    return df_results


df = process_all_emails("emails_out")
