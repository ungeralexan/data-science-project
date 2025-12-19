import json
from typing import Dict, List
import textwrap
#from google import genai
from openai import OpenAI
from sqlalchemy.orm import Session

from data.database.database_events import UserORM, MainEventORM  # pylint: disable=import-error
from config import RECOMMENDATION_LLM_MODEL  # pylint: disable=import-error


#   Event Recommender Service
#
#   This service uses an LLM (Gemini) to recommend events to users based on their
#   provided interests (interest_keys and interest_text columns in the users table).
#
#   The recommendation process:
#   1. Collect all users with interests (either interest_keys or interest_text)
#   2. Collect all main_events (not sub_events) with their titles and descriptions
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
    Fetch all non-archived main_events (not sub_events) with their titles and descriptions for recommendation.
    
    Returns:
        Dictionary mapping event_id to event info:
        {
            event_id: {
                "title": "Event Title",
                "description": "Event description text"
            }
        }
    """
    # Only query non-archived main_events, not sub_events
    events = db.query(MainEventORM).filter(MainEventORM.archived_event == False).all()
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
        - If no events match a user's interests very well, recommend fewer or no events for that user.

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
    #client = genai.Client(api_key=secrets["GEMINI_API_KEY"])
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=secrets["OPENROUTER_API_KEY"],
    )

    # Define the response schema (Gemini does not support additionalProperties)
    
    try:
        # Call OpenRouter / Gemini 2.0 Flash Experimental (free)
        completion = client.chat.completions.create(
            model=RECOMMENDATION_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            # You *can* try to enforce JSON with response_format, but it's optional:
            response_format={"type": "json_object"},
            extra_body={"reasoning": {"enabled": True}},
        )

        raw_content = completion.choices[0].message.content

        # Defensive cleanup: strip possible code fences if the model ignores instructions
        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            # Handle ```json ... ``` or ``` ... ```
            cleaned = cleaned.strip("`")
            # In case the first line is 'json'
            cleaned_lines = cleaned.splitlines()
            if cleaned_lines and cleaned_lines[0].strip().lower() == "json":
                cleaned = "\n".join(cleaned_lines[1:]).strip()

        # Parse JSON
        recommendations_list = json.loads(cleaned)

        recommendations: Dict[int, List[int]] = {}

        # Loop over recommendations
        for item in recommendations_list:
            # Validate item structure
            if not isinstance(item, dict):
                continue

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
    3. Loop over users one at a time, generating recommendations for each
    4. Update each user's record after processing
    
    This approach processes users individually to avoid overwhelming the LLM
    with too many users at once and to provide more focused recommendations.
    """
    print("[run_event_recommendations] Starting event recommendation pipeline...")
    
    # Step 1: Get users with interests
    users_dict = get_users_with_interests(db)
    print(f"[run_event_recommendations] Found {len(users_dict)} users with interests.")
    
    if not users_dict:
        print("[run_event_recommendations] No users with interests found. Skipping recommendations.")
        return
    
    # Step 2: Get all events (shared across all users)
    events_dict = get_events_for_recommendation(db)
    print(f"[run_event_recommendations] Found {len(events_dict)} events for recommendation.")
    
    if not events_dict:
        print("[run_event_recommendations] No events found. Skipping recommendations.")
        return
    
    # Step 3: Process each user individually
    total_updated = 0
    total_users = len(users_dict)
    
    for idx, (user_id, user_interests) in enumerate(users_dict.items(), 1):
        print(f"[run_event_recommendations] Processing user {user_id} ({idx}/{total_users})...")
        
        # Create single-user dictionary for LLM
        single_user_dict = {user_id: user_interests}
        
        try:
            # Get recommendations from LLM for this single user
            recommendations = recommend_events_with_llm(single_user_dict, events_dict)
            
            # Update user record
            recommended_ids = recommendations.get(user_id, [])
            user = db.query(UserORM).filter(UserORM.user_id == user_id).first()
            
            if user:
                user.suggested_event_ids = recommended_ids
                db.commit()
                total_updated += 1
                print(f"[run_event_recommendations] User {user_id} got {len(recommended_ids)} recommendations.")
            
        except Exception as e:  # pylint: disable=broad-except
            print(f"[run_event_recommendations] Error processing user {user_id}: {e}")
            continue
    
    print(f"[run_event_recommendations] Pipeline complete. Updated {total_updated}/{total_users} users.")


def run_single_user_recommendations(db: Session, user_id: int) -> dict:
    """
    Run event recommendations for a single user (on-demand).
    
    Args:
        db: Database session
        user_id: ID of the user to generate recommendations for
        
    Returns:
        Dictionary with status and message:
        {
            "success": bool,
            "message": str,
            "has_events": bool,
            "recommended_event_ids": list
        }
    """
    print(f"[run_single_user_recommendations] Starting recommendations for user {user_id}...")
    
    # Step 1: Get the user's interests
    user = db.query(UserORM).filter(UserORM.user_id == user_id).first()
    
    if not user:
        return {
            "success": False,
            "message": "User not found",
            "has_events": False,
            "recommended_event_ids": []
        }
    
    # Check if user has interests
    has_keys = user.interest_keys and len(user.interest_keys) > 0
    has_text = user.interest_text and len(user.interest_text.strip()) > 0
    
    if not has_keys and not has_text:
        # Clear any existing recommendations
        user.suggested_event_ids = []
        db.commit()
        return {
            "success": True,
            "message": "No interests defined. Please add interests in settings.",
            "has_events": False,
            "recommended_event_ids": []
        }
    
    users_dict = {
        user_id: {
            "interest_keys": user.interest_keys or [],
            "interest_text": user.interest_text or ""
        }
    }
    
    # Step 2: Get all non-archived events
    events_dict = get_events_for_recommendation(db)
    print(f"[run_single_user_recommendations] Found {len(events_dict)} events for recommendation.")
    
    if not events_dict:
        # Clear any existing recommendations
        user.suggested_event_ids = []
        db.commit()
        return {
            "success": True,
            "message": "No events available for recommendation.",
            "has_events": False,
            "recommended_event_ids": []
        }
    
    # Step 3: Get recommendations from LLM
    print(f"[run_single_user_recommendations] Calling LLM for user {user_id}...")
    recommendations = recommend_events_with_llm(users_dict, events_dict)

    # Step 4: Update user record
    recommended_ids = recommendations.get(user_id, [])
    user.suggested_event_ids = recommended_ids
    db.commit()
    
    print(f"[run_single_user_recommendations] User {user_id} got {len(recommended_ids)} recommendations.")
    
    return {
        "success": True,
        "message": f"Generated {len(recommended_ids)} recommendations.",
        "has_events": len(recommended_ids) > 0,
        "recommended_event_ids": recommended_ids
    }
