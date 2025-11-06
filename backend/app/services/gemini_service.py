import google.generativeai as genai
import json
import re
from typing import List, Dict, Any
from datetime import datetime
from app.config import get_settings
from app.schemas.calendar import CalendarEvent, FreeBlock, TimeSlot, CommuteSuggestion, Recommendations
from app.services.prompt_builder import build_day_plan_prompt
from app.utils.logger import log_error, log_debug

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


def fix_invalid_escape_sequences(text: str) -> str:
    """
    Fix invalid JSON escape sequences by properly escaping backslashes.

    Args:
        text: String that may contain invalid escape sequences

    Returns:
        String with fixed escape sequences
    """
    # This pattern finds backslashes followed by characters that aren't valid JSON escapes
    # Valid JSON escapes are: \" \\ \/ \b \f \n \r \t \uXXXX
    # We need to escape any backslash that isn't followed by one of these

    result = []
    i = 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            next_char = text[i + 1]
            # Check if this is a valid JSON escape sequence
            if next_char in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u'):
                # Valid escape - keep as is
                result.append(text[i])
                result.append(next_char)
                i += 2
            else:
                # Invalid escape - escape the backslash itself
                result.append('\\\\')
                i += 1
        else:
            result.append(text[i])
            i += 1

    return ''.join(result)


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
        json_text = match.group(0)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            # Strategy 4: Fix invalid escape sequences and try again
            try:
                fixed_text = fix_invalid_escape_sequences(json_text)
                return json.loads(fixed_text)
            except json.JSONDecodeError:
                pass

    # Strategy 5: Try fixing escape sequences on the original cleaned text
    try:
        fixed_text = fix_invalid_escape_sequences(cleaned)
        return json.loads(fixed_text)
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

        # Configure safety settings to be more permissive for educational content
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                response_mime_type="application/json"
            ),
            safety_settings=safety_settings
        )

        # Check if response was blocked or empty
        if not response.candidates:
            raise Exception("Gemini did not return any response. The content may have been blocked by safety filters.")

        # Check for safety ratings that blocked the response
        candidate = response.candidates[0]
        if hasattr(candidate, 'finish_reason') and candidate.finish_reason not in [1, 0]:  # 1 = STOP (normal), 0 = UNSPECIFIED
            finish_reason_name = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
            raise Exception(f"Gemini response was blocked. Finish reason: {finish_reason_name}")

        # Safely extract text from response
        try:
            response_text = response.text
        except (TypeError, AttributeError, ValueError) as e:
            # If response.text fails, try to extract from parts directly
            log_error("gemini_service", "Cannot access response.text", e)
            if response.candidates and response.candidates[0].content.parts:
                try:
                    response_text = response.candidates[0].content.parts[0].text
                    log_debug("gemini_service", "Extracted text from parts", chars=len(response_text))
                except Exception as parts_error:
                    log_error("gemini_service", "Cannot extract text from parts", parts_error)
                    raise Exception(f"Cannot extract text from Gemini response. Original error: {str(e)}")
            else:
                raise Exception(f"Gemini response has no valid content. Error: {str(e)}")

        # Parse JSON response using robust parsing
        try:
            result = parse_gemini_json_response(response_text)
        except Exception as parse_error:
            # Log the full response for debugging
            log_error("gemini_service", "Failed to parse Gemini response", parse_error)
            log_debug("gemini_service", "Response preview",
                     length=len(response_text),
                     preview=response_text[:1000])
            raise Exception(f"Failed to parse Gemini response as JSON: {str(parse_error)}")

        # Validate response structure
        required_keys = ["summary_short", "summary_detailed", "flashcards", "practice_questions"]
        for key in required_keys:
            if key not in result:
                raise Exception(f"Gemini response missing required field: {key}")

        return result

    except Exception as e:
        # Don't wrap exceptions that are already our custom exceptions
        if "Failed to parse Gemini response" in str(e) or "Gemini response missing required field" in str(e) or "Gemini" in str(e):
            raise
        raise Exception(f"Gemini API call failed: {str(e)}")


def generate_day_plan(
    date: str,
    events: List[CalendarEvent],
    free_blocks: List[FreeBlock],
    commute_duration_minutes: int = 30,
    morning_bus_time: str = None,
    evening_bus_time: str = None,
    planning_mode: str = None,
    planning_reason: str = None
) -> Recommendations:
    """
    Generate day plan recommendations using Gemini AI.

    Returns Recommendations object with lunch slots, study slots, commute suggestion, and summary.
    """

    # Build optimized prompt using modular builder
    prompt = build_day_plan_prompt(
        date=date,
        events=events,
        free_blocks=free_blocks,
        morning_bus_time=morning_bus_time,
        evening_bus_time=evening_bus_time,
        planning_mode=planning_mode,
        planning_reason=planning_reason
    )

    try:
        model = genai.GenerativeModel('gemini-flash-latest')

        # Configure safety settings to be more permissive
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                response_mime_type="application/json"
            ),
            safety_settings=safety_settings
        )

        # Check if response was blocked or empty
        if not response.candidates:
            raise Exception("Gemini did not return any response. The content may have been blocked by safety filters.")

        # Check for safety ratings that blocked the response
        candidate = response.candidates[0]
        if hasattr(candidate, 'finish_reason') and candidate.finish_reason not in [1, 0]:  # 1 = STOP (normal), 0 = UNSPECIFIED
            finish_reason_name = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
            raise Exception(f"Gemini response was blocked. Finish reason: {finish_reason_name}")

        # Safely extract text from response
        try:
            response_text = response.text
        except (TypeError, AttributeError, ValueError) as e:
            # If response.text fails, try to extract from parts directly
            log_error("gemini_service", "Cannot access response.text in generate_day_plan", e)
            if response.candidates and response.candidates[0].content.parts:
                try:
                    response_text = response.candidates[0].content.parts[0].text
                    log_debug("gemini_service", "Extracted text from parts in generate_day_plan",
                             chars=len(response_text))
                except Exception as parts_error:
                    log_error("gemini_service", "Cannot extract text from parts in generate_day_plan", parts_error)
                    raise Exception(f"Cannot extract text from Gemini response. Original error: {str(e)}")
            else:
                raise Exception(f"Gemini response has no valid content. Error: {str(e)}")

        # Parse JSON response
        result = json.loads(response_text)

        # Convert to Pydantic models
        lunch_slots = [TimeSlot(**slot) for slot in result.get("lunch_slots", [])]
        study_slots = [TimeSlot(**slot) for slot in result.get("study_slots", [])]

        # Handle commute_suggestion - fix leave_by if it's just a time string
        commute = None
        if result.get("commute_suggestion"):
            commute_data = result["commute_suggestion"]
            # If leave_by is just a time (e.g., "09:25 AM"), convert to full datetime
            if "leave_by" in commute_data:
                leave_by_str = commute_data["leave_by"]
                # Check if it's just a time (no date component)
                if "T" not in leave_by_str and len(leave_by_str) < 12:
                    # Parse the date from the prompt context
                    from datetime import datetime as dt
                    from zoneinfo import ZoneInfo
                    # Use the date parameter passed to the function
                    target_date = dt.fromisoformat(date).date()
                    # Parse the time and combine with date
                    try:
                        time_obj = dt.strptime(leave_by_str.strip(), "%I:%M %p").time()
                    except ValueError:
                        # Try without space
                        time_obj = dt.strptime(leave_by_str.strip(), "%I:%M%p").time()
                    # Combine and make timezone-aware
                    est = ZoneInfo("America/New_York")
                    leave_by_dt = dt.combine(target_date, time_obj).replace(tzinfo=est)
                    commute_data["leave_by"] = leave_by_dt.isoformat()
            commute = CommuteSuggestion(**commute_data)

        return Recommendations(
            lunch_slots=lunch_slots,
            study_slots=study_slots,
            commute_suggestion=commute,
            summary=result.get("summary", "")
        )

    except Exception as e:
        # Don't wrap exceptions that are already our custom exceptions
        if "Gemini" in str(e):
            raise
        raise Exception(f"Gemini API call failed: {str(e)}")
