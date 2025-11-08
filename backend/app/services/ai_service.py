"""
Unified AI service that supports multiple providers with fallback.
Priority: Groq (fastest) → GPT (reliable) → Gemini (fallback)
"""

import json
from typing import Any
from groq import Groq
from openai import OpenAI
import google.generativeai as genai

from app.config import get_settings
from app.utils.logger import log_error, log_info

settings = get_settings()

# Initialize clients lazily to avoid initialization errors
_groq_client = None
_openai_client = None
_groq_initialized = False
_openai_initialized = False

def _get_groq_client():
    global _groq_client, _groq_initialized
    if not _groq_initialized:
        if settings.groq_api_key and settings.groq_api_key != "your-groq-api-key-here":
            try:
                _groq_client = Groq(api_key=settings.groq_api_key)
                log_info("ai_service", "Groq client initialized")
            except Exception as e:
                log_error("ai_service", f"Failed to initialize Groq client: {str(e)}")
        _groq_initialized = True
    return _groq_client

def _get_openai_client():
    global _openai_client, _openai_initialized
    if not _openai_initialized:
        if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here":
            try:
                _openai_client = OpenAI(api_key=settings.openai_api_key)
                log_info("ai_service", "OpenAI client initialized")
            except Exception as e:
                log_error("ai_service", f"Failed to initialize OpenAI client: {str(e)}")
        _openai_initialized = True
    return _openai_client

# Configure Gemini as fallback
genai.configure(api_key=settings.gemini_api_key)


def generate_completion(
    prompt: str,
    response_format: str = "json",
    temperature: float = 0.7
) -> str:
    """
    Generate AI completion with automatic fallback between providers.

    Priority order:
    1. Groq (llama-3.1-70b-versatile) - Fastest
    2. OpenAI (gpt-4o-mini) - Reliable
    3. Gemini (gemini-1.5-flash-8b) - Fallback

    Args:
        prompt: The prompt to send to the AI
        response_format: "json" or "text"
        temperature: Response randomness (0.0-1.0)

    Returns:
        Generated text response

    Raises:
        Exception: If all providers fail
    """

    # Try Groq first (fastest)
    groq_client = _get_groq_client()
    if groq_client:
        try:
            log_info("ai_service", "Attempting Groq API call")
            response = groq_client.chat.completions.create(
                model="groq/compound",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                response_format={"type": "json_object"} if response_format == "json" else {"type": "text"}
            )
            log_info("ai_service", "Groq API call successful")
            return response.choices[0].message.content
        except Exception as e:
            log_error("ai_service", f"Groq API failed: {str(e)}")
            raise Exception(f"Groq API failed: {str(e)}")

    # # Try OpenAI GPT-4o-mini (reliable)
    # openai_client = _get_openai_client()
    # if openai_client:
    #     try:
    #         log_info("ai_service", "Attempting OpenAI API call")
    #         response = openai_client.chat.completions.create(
    #             model="gpt-4o-mini",
    #             messages=[{"role": "user", "content": prompt}],
    #             temperature=temperature,
    #             response_format={"type": "json_object"} if response_format == "json" else {"type": "text"}
    #         )
    #         log_info("ai_service", "OpenAI API call successful")
    #         return response.choices[0].message.content
    #     except Exception as e:
    #         log_error("ai_service", f"OpenAI API failed: {str(e)}")

    # # Fallback to Gemini
    # try:
    #     log_info("ai_service", "Attempting Gemini API call (fallback)")
    #     model = genai.GenerativeModel(
    #         model_name='gemini-flash-latest',
    #         generation_config={
    #             "temperature": temperature,
    #             "response_mime_type": "application/json" if response_format == "json" else "text/plain"
    #         }
    #     )
    #     response = model.generate_content(prompt)
    #     log_info("ai_service", "Gemini API call successful")
    #     return response.text
    # except Exception as e:
    #     log_error("ai_service", f"Gemini API failed: {str(e)}")
    #     raise Exception(f"All AI providers failed. Last error: {str(e)}")


def generate_json_completion(prompt: str, temperature: float = 0.7) -> dict[str, Any]:
    """
    Generate JSON completion from AI.

    Args:
        prompt: The prompt (should request JSON response)
        temperature: Response randomness

    Returns:
        Parsed JSON dict
    """
    response_text = generate_completion(prompt, response_format="json", temperature=temperature)

    # Clean up response (remove markdown code fences if present)
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    # Parse JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        log_error("ai_service", f"Failed to parse JSON response: {str(e)}")
        log_error("ai_service", f"Response was: {response_text}")
        raise Exception(f"Failed to parse AI JSON response: {str(e)}")
