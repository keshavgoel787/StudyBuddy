"""
Unit tests for utility functions.
"""

import pytest
from datetime import datetime, time
from app.utils.time_utils import calculate_free_blocks
from app.schemas.calendar import CalendarEvent


@pytest.mark.unit
def test_calculate_free_blocks_empty_schedule():
    """Test free block calculation with no events."""
    events = []
    free_blocks = calculate_free_blocks(events)

    # Should have one large free block for the entire day
    assert len(free_blocks) >= 1
    assert free_blocks[0].duration_minutes > 600  # More than 10 hours


@pytest.mark.unit
def test_calculate_free_blocks_with_events():
    """Test free block calculation with events."""
    events = [
        CalendarEvent(
            id="1",
            title="Morning Class",
            start="2025-11-05T09:00:00-05:00",
            end="2025-11-05T10:00:00-05:00",
            location="SCI 120"
        ),
        CalendarEvent(
            id="2",
            title="Afternoon Lab",
            start="2025-11-05T14:00:00-05:00",
            end="2025-11-05T16:00:00-05:00",
            location="LAB 201"
        )
    ]

    free_blocks = calculate_free_blocks(events)

    # Should have free blocks between events
    assert len(free_blocks) >= 1

    # Check that there's a free block between 10 AM and 2 PM
    lunch_block = None
    for block in free_blocks:
        start_hour = block.start.hour
        if 10 <= start_hour < 14:
            lunch_block = block
            break

    assert lunch_block is not None
    assert lunch_block.duration_minutes > 0


@pytest.mark.unit
def test_calculate_free_blocks_overlapping_events():
    """Test free block calculation with overlapping events."""
    events = [
        CalendarEvent(
            id="1",
            title="Event 1",
            start="2025-11-05T09:00:00-05:00",
            end="2025-11-05T11:00:00-05:00"
        ),
        CalendarEvent(
            id="2",
            title="Event 2",
            start="2025-11-05T10:00:00-05:00",
            end="2025-11-05T12:00:00-05:00"
        )
    ]

    free_blocks = calculate_free_blocks(events)

    # Should handle overlapping events gracefully
    assert isinstance(free_blocks, list)


@pytest.mark.unit
def test_error_handler():
    """Test centralized error handling utility."""
    from app.utils.rate_limiter import get_user_id_or_ip
    from unittest.mock import MagicMock

    # Test with authenticated request
    request = MagicMock()
    request.headers.get.return_value = "Bearer test_token_123456789012345"

    key = get_user_id_or_ip(request)
    assert key.startswith("user:")

    # Test with unauthenticated request
    request.headers.get.return_value = None
    request.client.host = "192.168.1.1"  # Mock the IP address
    key = get_user_id_or_ip(request)
    assert not key.startswith("user:")
    assert key == "192.168.1.1"  # Verify it returns the IP
