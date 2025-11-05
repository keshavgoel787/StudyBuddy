import google.generativeai as genai
import json
from typing import List, Dict, Any
from datetime import datetime
from app.config import get_settings
from app.schemas.calendar import CalendarEvent, FreeBlock, TimeSlot, CommuteSuggestion, Recommendations

settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


def generate_study_material(extracted_text: str) -> Dict[str, Any]:
    """
    Generate study material from extracted notes text using Gemini.

    Returns a dictionary with:
    - summary_short: str
    - summary_detailed: str
    - flashcards: List[Dict]
    - practice_questions: List[Dict]
    """

    prompt = f"""You are a helpful study assistant for a 3rd-year pre-med biochemistry student.

Given the following notes, generate comprehensive study materials.

NOTES:
{extracted_text}

Generate the following in valid JSON format:

1. A short summary (3 sentences or less)
2. A detailed summary (1-2 paragraphs)
3. 10-15 flashcards with concise questions and answers
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

Focus on biochemistry and pre-med level content. Make questions challenging but fair."""

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
        return result

    except Exception as e:
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
