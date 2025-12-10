import json
from typing import Dict, List
import textwrap
from google import genai
from sqlalchemy.orm import Session

from data.database.database_events import UserORM, EventORM  # pylint: disable=import-error
from config import LLM_MODEL  # pylint: disable=import-error


#   Event Recommender Service
#
#   This service uses an LLM (Gemini) to recommend events to users based on their
#   provided interests (interest_keys and interest_text columns in the users table).
#
#   The recommendation process:
#   1. Collect all users with interests (either interest_keys or interest_text)
#   2. Collect all events with their titles and descriptions
#   3. Send both to the LLM to match events to users based on interests
#   4. Update each user's suggested_event_ids column with recommendations

# Maximum number of events to recommend per user
MAX_RECOMMENDATIONS_PER_USER = 3


def get_users_with_interests(db: Session) -> Dict[int, dict]:
    """
    Fetch all users who have provided interests.
    
    Returns:
        Dictionary mapping user_id to their interest data:
        {
            user_id: {
                "interest_keys": ["keyword1", "keyword2"],
                "interest_text": "Free text description"
            }
        }
    """
    users = db.query(UserORM).all()
    users_dict = {}
    
    for user in users:
        # Only include users with at least one interest field populated
        has_keys = user.interest_keys and len(user.interest_keys) > 0
        has_text = user.interest_text and len(user.interest_text.strip()) > 0
        
        if has_keys or has_text:
            users_dict[user.user_id] = {
                "interest_keys": user.interest_keys or [],
                "interest_text": user.interest_text or ""
            }
    
    return users_dict


def get_events_for_recommendation(db: Session) -> Dict[int, dict]:
    """
    Fetch all events with their titles and descriptions for recommendation.
    
    Returns:
        Dictionary mapping event_id to event info:
        {
            event_id: {
                "title": "Event Title",
                "description": "Event description text"
            }
        }
    """
    events = db.query(EventORM).all()
    events_dict = {}
    
    for event in events:
        events_dict[event.id] = {
            "title": event.title or "",
            "description": event.description or ""
        }
    
    return events_dict


def recommend_events_with_llm(
    users_dict: Dict[int, dict],
    events_dict: Dict[int, dict]
) -> Dict[int, List[int]]:
    """
    Use LLM to match events to users based on their interests based on user dictionary and event dictionary.
    Returns a dictionary mapping user_id to list of recommended event_ids:

    {user_id: [event_id1, event_id2, event_id3]}

    """
    if not users_dict or not events_dict:
        print("[recommend_events_with_llm] No users or events to process.")
        return {}
    
    # Build the prompt
    # We are using textwrap.dedent to format the multi-line string properly with
    # {{"user_id": 1, "recommended_event_ids": [5, 12, 3]}}, without confusing the syntax. 
    system_instruction = textwrap.dedent(
        """
        You are an event recommendation system. Your task is to match university events
        to users based on their stated interests.

        You will receive:
        1. A dictionary of USERS with their user_id as key and their interests as value.
           Interests include "interest_keys" (list of keywords) and "interest_text" (free text description of the users interest).
        2. A dictionary of EVENTS with event_id as key and event info (title, description) as value.

        Your task:
        - For each user, analyze their interests and find up to {max_events} events
          that best match their interests.
        - Consider both the interest keywords and the free text description when matching.
        - Only recommend events that are genuinely relevant to the user's interests.
        - If no events match a user's interests well, recommend fewer or no events for that user.

        OUTPUT FORMAT:
        Return a JSON ARRAY where each item is an object with:
        - user_id (integer)
        - recommended_event_ids (array of integers)
        - Maximum {max_events} events per user
        - Order events by relevance (most relevant first)

        Example output:
        [
            {{"user_id": 1, "recommended_event_ids": [5, 12, 3]}},
            {{"user_id": 2, "recommended_event_ids": [7]}},
            {{"user_id": 3, "recommended_event_ids": [12, 5]}}
        ]

        If a user has no good matches, you can return an empty array for them, or omit them entirely.
        """
    ).format(max_events=MAX_RECOMMENDATIONS_PER_USER)
    
    user_prompt = f"""
        USERS (with their interests):
        {json.dumps(users_dict, indent=2)}
        
        EVENTS (available for recommendation):
        {json.dumps(events_dict, indent=2)}
        
        Based on the users' interests, recommend the most relevant events for each user.
        Return ONLY the JSON array with recommendation objects, no additional text.
    """
    
    # Load Gemini API key
    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)
    
    # Create Gemini client and make request
    client = genai.Client(api_key=secrets["GEMINI_API_KEY"])
    
    # Define the response schema (Gemini does not support additionalProperties)
    response_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "user_id": {"type": "INTEGER"},
                "recommended_event_ids": {
                    "type": "ARRAY",
                    "items": {"type": "INTEGER"}
                }
            },
            "required": ["user_id", "recommended_event_ids"]
        }
    }
    
    try:
        resp = client.models.generate_content(
            model=LLM_MODEL,
            contents=f"{system_instruction}\n\n{user_prompt}",
            config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            },
        )
        
        # Parse response
        recommendations_list = json.loads(resp.text)

        recommendations = {}

        # Loop over recommendations
        for item in recommendations_list:

            # Validate item structure
            if not isinstance(item, dict):
                continue

            # Extract user ID and event IDs
            user_id = item.get("user_id")
            event_ids = item.get("recommended_event_ids", [])

            if user_id is None:
                continue

            # Validate event IDs exist and limit to max recommendations
            valid_event_ids = [
                eid for eid in event_ids
                if eid in events_dict
            ][:MAX_RECOMMENDATIONS_PER_USER]

            # Only add if there are valid recommendations
            recommendations[int(user_id)] = valid_event_ids
        
        return recommendations
        
    except Exception as e:  # pylint: disable=broad-except
        print(f"[recommend_events_with_llm] Error calling LLM: {e}")
        return {}


def update_user_recommendations(db: Session, recommendations: Dict[int, List[int]]) -> int:
    """
    Update users' suggested_event_ids column with recommendations.
    """
    updated_count = 0
    
    for user_id, event_ids in recommendations.items():

        # Query user
        user = db.query(UserORM).filter(UserORM.user_id == user_id).first()

        if user:
            # Replace any existing recommendations with new ones
            user.suggested_event_ids = event_ids
            updated_count += 1
    
    db.commit()

    return updated_count


def run_event_recommendations(db: Session) -> None:
    """
    Main function to run the event recommendation pipeline.
    
    Steps:
    1. Get all users with interests
    2. Get all events
    3. Use LLM to generate recommendations
    4. Update user records with recommendations
    """
    print("[run_event_recommendations] Starting event recommendation pipeline...")
    
    # Step 1: Get users with interests
    users_dict = get_users_with_interests(db)
    print(f"[run_event_recommendations] Found {len(users_dict)} users with interests.")
    
    if not users_dict:
        print("[run_event_recommendations] No users with interests found. Skipping recommendations.")
        return
    
    # Step 2: Get all events
    events_dict = get_events_for_recommendation(db)
    print(f"[run_event_recommendations] Found {len(events_dict)} events for recommendation.")
    
    if not events_dict:
        print("[run_event_recommendations] No events found. Skipping recommendations.")
        return
    
    # Step 3: Get recommendations from LLM
    print("[run_event_recommendations] Calling LLM for event recommendations...")
    recommendations = recommend_events_with_llm(users_dict, events_dict)
    print(f"[run_event_recommendations] LLM returned recommendations for {len(recommendations)} users.")
    
    # Step 4: Update user records
    if recommendations:
        updated_count = update_user_recommendations(db, recommendations)
        print(f"[run_event_recommendations] Updated {updated_count} user records with recommendations.")
    else:
        print("[run_event_recommendations] No recommendations generated.")
