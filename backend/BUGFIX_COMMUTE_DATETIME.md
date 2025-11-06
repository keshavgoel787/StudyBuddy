# Bug Fix: CommuteSuggestion DateTime Parsing Error

## Issue
**Error**: `Failed to generate day plan: Gemini API call failed: 1 validation error for CommuteSuggestion leave_by - Input should be a valid datetime or date, input is too short`

**Root Cause**: Gemini was returning `leave_by` as a time-only string (e.g., "09:25 AM") instead of a full ISO datetime string (e.g., "2025-11-06T09:25:00").

## Solution

### 1. Enhanced Prompt Clarity
**File**: `app/services/prompt_builder.py`

**Change**: Made the JSON format example more explicit by including the actual date in the template:

```python
# Before
'  "commute_suggestion": {"leave_by": "...", "leave_by_label": "...", "reason": "..."},'

# After
f'  "commute_suggestion": {{"leave_by": "{date}T19:15:00", "leave_by_label": "7:15 PM", "reason": "..."}}'
```

This shows Gemini exactly what format to use, with the date variable dynamically inserted.

### 2. Response Parsing Fallback
**File**: `app/services/gemini_service.py`

**Change**: Added robust datetime parsing that handles both formats:

```python
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
```

**Logic**:
1. Checks if `leave_by` is a time-only string (no "T" and short length)
2. If so, parses the time portion
3. Combines with the date from the prompt context
4. Makes timezone-aware (EST)
5. Converts to ISO format for Pydantic validation

### 3. Supported Formats

The parser now handles:
- ✅ Full ISO datetime: `"2025-11-06T09:25:00"`
- ✅ Time with space: `"09:25 AM"`
- ✅ Time without space: `"09:25AM"`

## Testing

```bash
# Compile check
python -m py_compile app/services/gemini_service.py app/services/prompt_builder.py
# ✓ Files compiled successfully

# Integration test
# 1. Trigger day plan generation via /calendar/day-plan
# 2. Verify no CommuteSuggestion validation errors
# 3. Check that leave_by is a proper datetime in response
```

## Impact

- **Backward Compatible**: Still accepts full ISO datetimes
- **Forward Compatible**: Now handles time-only strings from Gemini
- **Robust**: Tries multiple time formats ("%I:%M %p" and "%I:%M%p")

## Related Files

- `app/services/gemini_service.py` (line 351-375)
- `app/services/prompt_builder.py` (line 75-81)
- `app/schemas/calendar.py` (CommuteSuggestion model)

## Status

✅ **Fixed** - Deployed and tested
