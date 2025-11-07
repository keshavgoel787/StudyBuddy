"""
Tests for planning agent and intelligent scheduling.
"""

import pytest
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock

from app.services.planning_agent import (
    agent_filter_schedule_for_today,
    build_planning_prompt,
    AgentDecision
)
from app.schemas.calendar import CalendarEvent, FreeBlock
from app.models.assignment import Assignment


@pytest.fixture
def est():
    """EST timezone for testing."""
    return ZoneInfo("America/New_York")


@pytest.fixture
def sample_events(est):
    """Sample calendar events."""
    today = datetime.now(est).replace(hour=0, minute=0, second=0, microsecond=0)
    return [
        CalendarEvent(
            id="event1",
            title="Morning Lecture",
            start=today.replace(hour=9),
            end=today.replace(hour=10, minute=30),
            event_type="calendar"
        ),
        CalendarEvent(
            id="event2",
            title="Lab Session",
            start=today.replace(hour=14),
            end=today.replace(hour=16),
            event_type="calendar"
        )
    ]


@pytest.fixture
def sample_free_blocks(est):
    """Sample free time blocks."""
    today = datetime.now(est).replace(hour=0, minute=0, second=0, microsecond=0)
    return [
        FreeBlock(
            start=today.replace(hour=10, minute=30),
            end=today.replace(hour=14),
            duration_minutes=210  # 3.5 hours
        ),
        FreeBlock(
            start=today.replace(hour=16),
            end=today.replace(hour=20),
            duration_minutes=240  # 4 hours
        )
    ]


@pytest.fixture
def sample_assignments(est, test_user):
    """Sample assignments for testing."""
    today = datetime.now(est).replace(hour=0, minute=0, second=0, microsecond=0)
    return [
        Assignment(
            id=1,
            user_id=test_user.id,
            title="Physics Homework",
            due_date=today + timedelta(days=2),
            estimated_hours=2.0,
            priority=3,
            completed=False
        ),
        Assignment(
            id=2,
            user_id=test_user.id,
            title="Chemistry Lab Report",
            due_date=today + timedelta(days=5),
            estimated_hours=3.0,
            priority=2,
            completed=False
        )
    ]


class TestAgentFilterSchedule:
    """Test suite for agent_filter_schedule_for_today function."""

    @patch('app.services.planning_agent.genai.GenerativeModel')
    def test_agent_off_mode(self, mock_model_class, est, sample_events, sample_free_blocks, sample_assignments):
        """Test agent deciding OFF mode (no study blocks)."""
        # Mock Gemini response for OFF mode
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"mode": "OFF", "kept_block_ids": [], "reason": "Light day, take a break"}'
        mock_response.candidates = [MagicMock()]
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        today = date.today()
        kept_blocks, decision = agent_filter_schedule_for_today(
            today=today,
            events=sample_events,
            free_blocks=sample_free_blocks,
            assignments=sample_assignments
        )

        assert decision.mode == "OFF"
        assert len(kept_blocks) == 0
        assert "break" in decision.reason.lower()

    @patch('app.services.planning_agent.genai.GenerativeModel')
    def test_agent_light_mode(self, mock_model_class, est, sample_events, sample_free_blocks, sample_assignments):
        """Test agent deciding LIGHT mode (1 study block)."""
        # Mock Gemini response for LIGHT mode
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"mode": "LIGHT", "kept_block_ids": ["assignment-1-0"], "reason": "One focused session"}'
        mock_response.candidates = [MagicMock()]
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        today = date.today()
        kept_blocks, decision = agent_filter_schedule_for_today(
            today=today,
            events=sample_events,
            free_blocks=sample_free_blocks,
            assignments=sample_assignments
        )

        assert decision.mode == "LIGHT"
        assert len(decision.kept_block_ids) == 1
        # Note: actual kept_blocks depends on scheduler proposing blocks with these IDs

    @patch('app.services.planning_agent.genai.GenerativeModel')
    def test_agent_normal_mode(self, mock_model_class, est, sample_events, sample_free_blocks, sample_assignments):
        """Test agent deciding NORMAL mode (2-3 study blocks)."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"mode": "NORMAL", "kept_block_ids": ["assignment-1-0", "assignment-2-0"], "reason": "Balanced schedule"}'
        mock_response.candidates = [MagicMock()]
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        today = date.today()
        kept_blocks, decision = agent_filter_schedule_for_today(
            today=today,
            events=sample_events,
            free_blocks=sample_free_blocks,
            assignments=sample_assignments
        )

        assert decision.mode == "NORMAL"
        assert len(decision.kept_block_ids) == 2

    @patch('app.services.planning_agent.genai.GenerativeModel')
    def test_agent_high_mode_exam_prep(self, mock_model_class, est, sample_events, sample_free_blocks, sample_assignments):
        """Test agent deciding HIGH mode during exam prep."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"mode": "HIGH", "kept_block_ids": ["assignment-1-0", "assignment-1-1", "assignment-2-0"], "reason": "Exam tomorrow, intensive prep"}'
        mock_response.candidates = [MagicMock()]
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        today = date.today()

        # Add exam event
        exam_event = CalendarEvent(
            id="exam1",
            title="Physics Exam",
            start=datetime.now(est) + timedelta(days=1),
            end=datetime.now(est) + timedelta(days=1) + timedelta(hours=2),
            event_type="calendar"
        )

        kept_blocks, decision = agent_filter_schedule_for_today(
            today=today,
            events=sample_events,
            free_blocks=sample_free_blocks,
            assignments=sample_assignments,
            exams=[exam_event]
        )

        assert decision.mode == "HIGH"
        assert "exam" in decision.reason.lower()

    def test_agent_no_assignments(self, est, sample_events, sample_free_blocks):
        """Test agent with no assignments."""
        today = date.today()
        kept_blocks, decision = agent_filter_schedule_for_today(
            today=today,
            events=sample_events,
            free_blocks=sample_free_blocks,
            assignments=[]
        )

        assert decision.mode == "OFF"
        assert len(kept_blocks) == 0
        assert "no assignments" in decision.reason.lower() or "no study blocks" in decision.reason.lower()

    def test_agent_no_free_time(self, est, sample_assignments):
        """Test agent with no free time available."""
        today = datetime.now(est).replace(hour=0, minute=0, second=0, microsecond=0)

        # Create events that fill the entire day
        busy_events = [
            CalendarEvent(
                id=f"event{i}",
                title=f"Event {i}",
                start=today.replace(hour=8+i*2),
                end=today.replace(hour=10+i*2),
                event_type="calendar"
            )
            for i in range(6)
        ]

        kept_blocks, decision = agent_filter_schedule_for_today(
            today=today.date(),
            events=busy_events,
            free_blocks=[],
            assignments=sample_assignments
        )

        assert decision.mode == "OFF"
        assert len(kept_blocks) == 0

    @patch('app.services.planning_agent.genai.GenerativeModel')
    def test_agent_gemini_failure_fallback(self, mock_model_class, est, sample_events, sample_free_blocks, sample_assignments):
        """Test fallback behavior when Gemini API fails."""
        # Mock Gemini to raise an exception
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model

        today = date.today()
        kept_blocks, decision = agent_filter_schedule_for_today(
            today=today,
            events=sample_events,
            free_blocks=sample_free_blocks,
            assignments=sample_assignments
        )

        # Fallback should keep all proposed blocks
        assert decision.mode == "NORMAL"
        assert "Gemini unavailable" in decision.reason
        # Blocks should be kept (exact count depends on scheduler)

    @patch('app.services.planning_agent.genai.GenerativeModel')
    def test_agent_preserves_block_ids(self, mock_model_class, est, sample_events, sample_free_blocks, sample_assignments):
        """Test that agent correctly filters blocks by ID."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        # Keep only specific block IDs
        mock_response.text = '{"mode": "LIGHT", "kept_block_ids": ["assignment-1-0"], "reason": "Focus on urgent task"}'
        mock_response.candidates = [MagicMock()]
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        today = date.today()
        kept_blocks, decision = agent_filter_schedule_for_today(
            today=today,
            events=sample_events,
            free_blocks=sample_free_blocks,
            assignments=sample_assignments
        )

        # Verify only blocks with kept IDs are returned
        kept_ids = {block.id for block in kept_blocks}
        assert all(block_id in decision.kept_block_ids for block_id in kept_ids)


class TestBuildPlanningPrompt:
    """Test suite for build_planning_prompt function."""

    def test_prompt_includes_context(self, est):
        """Test that prompt includes day context information."""
        from app.services.day_context import DayContext

        context = DayContext(
            date="2025-11-07",
            total_awake_hours=16.0,
            total_busy_hours=8.0,
            total_study_hours_if_applied=2.0,
            free_hours_if_applied=6.0,
            has_exam_within_2_days=False,
            days_until_next_exam=5,
            assignments_summary=[
                {
                    "title": "Physics Homework",
                    "due_in_days": 2,
                    "estimated_hours": 2.0,
                    "priority": 3
                }
            ]
        )

        today = datetime.now(est).replace(hour=0, minute=0, second=0, microsecond=0)
        candidate_blocks = [
            CalendarEvent(
                id="assignment-1-0",
                title="📚 Work on Physics Homework",
                start=today.replace(hour=10),
                end=today.replace(hour=11),
                description="Study session for Physics Homework\nDue in 2 days",
                event_type="assignment_block"
            )
        ]

        prompt = build_planning_prompt(context, candidate_blocks)

        # Verify key information is in prompt
        assert "2025-11-07" in prompt
        assert "16h" in prompt or "Awake:" in prompt
        assert "Physics Homework" in prompt
        assert "assignment-1-0" in prompt
        assert "OFF" in prompt and "LIGHT" in prompt and "NORMAL" in prompt and "HIGH" in prompt

    def test_prompt_format_json_response(self, est):
        """Test that prompt requests JSON format."""
        from app.services.day_context import DayContext

        context = DayContext(
            date="2025-11-07",
            total_awake_hours=16.0,
            total_busy_hours=8.0,
            total_study_hours_if_applied=2.0,
            free_hours_if_applied=6.0,
            has_exam_within_2_days=False,
            days_until_next_exam=None,
            assignments_summary=[]
        )

        prompt = build_planning_prompt(context, [])

        assert "JSON" in prompt
        assert "mode" in prompt
        assert "kept_block_ids" in prompt
        assert "reason" in prompt

    def test_prompt_highlights_exam_pressure(self, est):
        """Test that prompt highlights exam within 2 days."""
        from app.services.day_context import DayContext

        context = DayContext(
            date="2025-11-07",
            total_awake_hours=16.0,
            total_busy_hours=8.0,
            total_study_hours_if_applied=4.0,
            free_hours_if_applied=4.0,
            has_exam_within_2_days=True,
            days_until_next_exam=1,
            assignments_summary=[]
        )

        prompt = build_planning_prompt(context, [])

        assert "Exam <2d: YES" in prompt or "Exam" in prompt
        assert "1d" in prompt or "next exam" in prompt.lower()

    def test_prompt_compact_format(self, est):
        """Test that prompt uses compact formatting."""
        from app.services.day_context import DayContext

        context = DayContext(
            date="2025-11-07",
            total_awake_hours=16.0,
            total_busy_hours=8.0,
            total_study_hours_if_applied=2.0,
            free_hours_if_applied=6.0,
            has_exam_within_2_days=False,
            days_until_next_exam=5,
            assignments_summary=[
                {
                    "title": "Physics Homework",
                    "due_in_days": 2,
                    "estimated_hours": 2.0,
                    "priority": 3
                }
            ]
        )

        today = datetime.now(est).replace(hour=0, minute=0, second=0, microsecond=0)
        candidate_blocks = [
            CalendarEvent(
                id="assignment-1-0",
                title="📚 Work on Physics Homework",
                start=today.replace(hour=10),
                end=today.replace(hour=11),
                description="Study session for Physics Homework\nDue in 2 days",
                event_type="assignment_block"
            )
        ]

        prompt = build_planning_prompt(context, candidate_blocks)

        # Verify compact format (using abbreviations)
        assert "P3" in prompt or "priority" in prompt.lower()  # Priority format
        assert "2h" in prompt  # Hours format


class TestAgentDecisionModel:
    """Test suite for AgentDecision Pydantic model."""

    def test_valid_decision(self):
        """Test creating a valid AgentDecision."""
        decision = AgentDecision(
            mode="NORMAL",
            kept_block_ids=["assignment-1-0", "assignment-2-0"],
            reason="Balanced workload"
        )

        assert decision.mode == "NORMAL"
        assert len(decision.kept_block_ids) == 2
        assert decision.reason == "Balanced workload"

    def test_decision_modes(self):
        """Test all valid decision modes."""
        modes = ["OFF", "LIGHT", "NORMAL", "HIGH"]

        for mode in modes:
            decision = AgentDecision(
                mode=mode,
                kept_block_ids=[],
                reason=f"Testing {mode} mode"
            )
            assert decision.mode == mode

    def test_decision_empty_blocks(self):
        """Test decision with no kept blocks."""
        decision = AgentDecision(
            mode="OFF",
            kept_block_ids=[],
            reason="No study needed"
        )

        assert len(decision.kept_block_ids) == 0

    def test_decision_multiple_blocks(self):
        """Test decision with multiple kept blocks."""
        block_ids = [f"assignment-{i}-0" for i in range(5)]

        decision = AgentDecision(
            mode="HIGH",
            kept_block_ids=block_ids,
            reason="Intensive study session"
        )

        assert len(decision.kept_block_ids) == 5
        assert all(f"assignment-{i}-0" in decision.kept_block_ids for i in range(5))
