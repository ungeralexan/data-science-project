import os
import json

from typing import Optional
from pathlib import Path
from urllib import response
import pandas as pd

from openai import OpenAI
from pydantic import BaseModel
from pydantic import ValidationError

class EmailInfo(BaseModel):
    """
        This pydantic model contains all the required fields to extract event information from emails.
    """

    Title: Optional[str] = None
    Start_Date: Optional[str] = None
    End_Date: Optional[str] = None
    Start_Time: Optional[str] = None
    End_Time: Optional[str] = None
    Description: Optional[str] = None
    Location: Optional[str] = None
    Speaker: Optional[str] = None
    Organizer: Optional[str] = None
    Registration_Needed: Optional[bool] = None
    URL: Optional[str] = None


def extract_event_info_with_llm(text):
    """
        This function extracts event information from email text using a large language model (LLM) via Hugging Face's API.
    """

    system_prompt = (
        "You are a multilingual assistant that extracts event information from email texts according to a given schema."
        "Not every email contains information about events. You only extract information if there is a clear event mentioned."
        "The text may be in German or in English. Keep the date and time formats as in the original text."
        "If unsure about date/time, leave fields null."
        "Respond in JSON format as specified."
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

    {text}
    """

    #Opens secrets.json to read the HF_TOKEN
    with open("secrets.json", "r", encoding = "utf-8") as f:
        secrets = json.load(f)

    # Initialize the OpenAI client with Hugging Face router
    client = OpenAI(
        #base_url = "https://router.huggingface.co/v1",
        #api_key = secrets["HF_TOKEN"]

        base_url = "https://api.groq.com/openai/v1",
        api_key = secrets["GROQ_API_KEY"]
    )

    # Creates structured output based on the EmailInfo pydantic model
    response = client.chat.completions.parse(
        #model = "Qwen/Qwen2.5-7B-Instruct:cheapest",
        #model = "llama-3.1-8b-instant",
        model = "llama-3.3-70b-versatile",

        #response_format = EmailInfo,
        response_format = {"type": "json_object"},

        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    #Returns the validated JSON response
    #return EmailInfo.model_validate_json(response.choices[0].message.content)

    content = response.choices[0].message.content

    # primary path: direct single-object JSON
    try:
        return EmailInfo.model_validate_json(content)
    except ValidationError:
        # fallback: if the model wrapped it as {"events":[{...}]}, unwrap the first
        data = json.loads(content)
        if isinstance(data, dict) and "events" in data and isinstance(data["events"], list) and data["events"]:
            return EmailInfo.model_validate(data["events"][0])
        raise

def process_all_emails(folder_path):
    """
        This function processes all email text files in the specified folder,
        extracts event information using the LLM, and saves the results to an Excel file.
    """

    #List to store results
    results = []

    # Iterate over all .txt files in the specified folder
    for email_file in Path(folder_path).glob("*.txt"):

        print(f"Processing: {email_file.name}")

        # Read the email text content
        email_text = email_file.read_text(encoding="utf-8", errors="ignore")

        # Extract event information using the LLM
        event_info = extract_event_info_with_llm(email_text)

        # Convert the pydantic model to a dictionary
        data = event_info.model_dump()

        # Add source file information
        results.append(data)
    
    # Create a DataFrame from the results
    df_results = pd.DataFrame(results)

    # Save the results to an Excel file
    df_results.to_csv("extracted_event_info.csv", index=False)

    print("Results saved!")

    return df_results

df = process_all_emails("emails_out")