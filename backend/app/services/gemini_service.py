import google.generativeai as genai
import json
import re
from typing import List, Dict, Any
from datetime import datetime
from app.config import get_settings
from app.schemas.calendar import CalendarEvent, FreeBlock, TimeSlot, CommuteSuggestion, Recommendations

settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


def sanitize_text_for_prompt(text: str) -> str:
    """
    Sanitize extracted text to prevent JSON formatting issues in prompts.
    Handles special characters that could break JSON structure.
    """
    if not text:
        return text

    # Replace problematic characters that could interfere with JSON
    # This doesn't escape them for JSON, just makes them safe for the prompt
    sanitized = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove null bytes and other control characters except newlines and tabs
    sanitized = ''.join(char for char in sanitized if char == '\n' or char == '\t' or ord(char) >= 32)

    return sanitized


def parse_gemini_json_response(response_text: str) -> Dict[str, Any]:
    """
    Robustly parse JSON from Gemini response, handling various edge cases.

    Args:
        response_text: Raw response text from Gemini

    Returns:
        Parsed JSON dictionary

    Raises:
        Exception: If JSON cannot be parsed after all attempts
    """
    # Strategy 1: Try direct parsing
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code fences
    # Gemini sometimes wraps JSON in ```json ... ``` despite response_mime_type
    cleaned = response_text.strip()
    if cleaned.startswith('```'):
        # Remove opening fence (```json or just ```)
        lines = cleaned.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        # Remove closing fence
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        cleaned = '\n'.join(lines)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    # Strategy 3: Extract JSON from text (find first { to last })
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # All strategies failed - provide detailed error
    preview = response_text[:500] + ('...' if len(response_text) > 500 else '')
    raise Exception(f"Failed to parse Gemini response as JSON after multiple attempts. Response preview: {preview}")


def generate_study_material(extracted_text: str, topic_hint: str = None) -> Dict[str, Any]:
    """
    Generate study material from extracted notes text using Gemini.

    Args:
        extracted_text: The notes text to process
        topic_hint: Optional hint about the topic (e.g., "Physics - 2D Kinematics", "Organic Chemistry")

    Returns a dictionary with:
    - summary_short: str
    - summary_detailed: str
    - flashcards: List[Dict]
    - practice_questions: List[Dict]
    """

    # Validate input
    if not extracted_text or len(extracted_text.strip()) < 10:
        raise Exception("Extracted text is too short or empty. Need at least 10 characters.")

    # Sanitize extracted text to prevent prompt injection and JSON issues
    sanitized_text = sanitize_text_for_prompt(extracted_text)

    # Build the prompt with topic awareness
    topic_context = ""
    if topic_hint:
        topic_context = f"\n\nTOPIC HINT: The user indicated this is about: {topic_hint}\nUse this as context, but also analyze the notes to understand the specific concepts covered."
    else:
        topic_context = "\n\nFirst, analyze the notes to identify the subject area and main topics covered. Then generate study materials appropriate for that subject."

    prompt = f"""You are an intelligent study assistant that helps students master any subject.

Given the following notes, generate comprehensive study materials.{topic_context}

NOTES:
{sanitized_text}

Generate the following in valid JSON format:

1. A short summary (3 sentences or less) - identify the main topic and key concepts
2. A detailed summary (1-2 paragraphs) - comprehensive overview with subject-appropriate terminology
3. 10-15 flashcards with concise questions and answers relevant to the subject matter
4. 5-8 multiple choice practice questions with 4 options each, the correct answer index (0-3), and a brief explanation

Return ONLY valid JSON in this exact format:
{{
  "summary_short": "Brief 3-sentence summary here",
  "summary_detailed": "Detailed 1-2 paragraph summary here",
  "flashcards": [
    {{"question": "Question here?", "answer": "Answer here"}},
    ...
  ],
  "practice_questions": [
    {{
      "question": "Question here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "explanation": "Brief explanation of why this is correct"
    }},
    ...
  ]
}}

Make the questions challenging but fair, appropriate for the academic level and subject area."""

    try:
        model = genai.GenerativeModel('gemini-flash-latest')

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                response_mime_type="application/json"
            )
        )

        # Parse JSON response using robust parsing
        try:
            result = parse_gemini_json_response(response.text)
        except Exception as parse_error:
            # Log the full response for debugging
            print(f"ERROR: Failed to parse Gemini response")
            print(f"Response length: {len(response.text)} chars")
            print(f"Response preview: {response.text[:1000]}")
            raise Exception(f"Failed to parse Gemini response as JSON: {str(parse_error)}")

        # Validate response structure
        required_keys = ["summary_short", "summary_detailed", "flashcards", "practice_questions"]
        for key in required_keys:
            if key not in result:
                raise Exception(f"Gemini response missing required field: {key}")

        return result

    except Exception as e:
        # Don't wrap exceptions that are already our custom exceptions
        if "Failed to parse Gemini response" in str(e) or "Gemini response missing required field" in str(e):
            raise
        raise Exception(f"Gemini API call failed: {str(e)}")


def generate_day_plan(
    date: str,
    events: List[CalendarEvent],
    free_blocks: List[FreeBlock],
    commute_duration_minutes: int = 30
) -> Recommendations:
    """
    Generate day plan recommendations using Gemini AI.

    Returns Recommendations object with lunch slots, study slots, commute suggestion, and summary.
    """

    # Format events for prompt
    events_text = "\n".join([
        f"- {e.title}: {e.start.strftime('%I:%M %p')} - {e.end.strftime('%I:%M %p')}"
        for e in events
    ])

    # Format free blocks
    free_blocks_text = "\n".join([
        f"- {fb.start.strftime('%I:%M %p')} - {fb.end.strftime('%I:%M %p')} ({fb.duration_minutes} min)"
        for fb in free_blocks
    ])

    prompt = f"""You are a helpful personal assistant for a busy pre-med student.

Today is {date}. Here is the student's schedule:

EVENTS:
{events_text if events_text else "No events scheduled"}

FREE TIME BLOCKS:
{free_blocks_text if free_blocks_text else "Entire day is free"}

Based on this schedule, recommend:
1. 1-2 good lunch time windows (30-60 minutes each, ideally between 11 AM - 2 PM)
2. 1-2 study blocks (60-120 minutes each, when they can focus)
3. A time to leave for commute home (assuming {commute_duration_minutes} minute commute)
4. A friendly natural language summary of the day and your suggestions

Return ONLY valid JSON in this exact format:
{{
  "lunch_slots": [
    {{"start": "2025-11-08T12:00:00", "end": "2025-11-08T13:00:00", "label": "12:00 PM - 1:00 PM"}}
  ],
  "study_slots": [
    {{"start": "2025-11-08T15:00:00", "end": "2025-11-08T17:00:00", "label": "3:00 PM - 5:00 PM"}}
  ],
  "commute_suggestion": {{
    "leave_by": "2025-11-08T19:30:00",
    "leave_by_label": "7:30 PM",
    "reason": "To get home by 8:00 PM"
  }},
  "summary": "Natural language summary of the day and recommendations"
}}

Make sure all times are in ISO format and within the free blocks available."""

    try:
        model = genai.GenerativeModel('gemini-flash-latest')

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                response_mime_type="application/json"
            )
        )

        # Parse JSON response
        result = json.loads(response.text)

        # Convert to Pydantic models
        lunch_slots = [TimeSlot(**slot) for slot in result.get("lunch_slots", [])]
        study_slots = [TimeSlot(**slot) for slot in result.get("study_slots", [])]
        commute = CommuteSuggestion(**result["commute_suggestion"]) if result.get("commute_suggestion") else None

        return Recommendations(
            lunch_slots=lunch_slots,
            study_slots=study_slots,
            commute_suggestion=commute,
            summary=result.get("summary", "")
        )

    except Exception as e:
        raise Exception(f"Gemini API call failed: {str(e)}")
