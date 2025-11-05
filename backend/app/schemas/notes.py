from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class NoteUploadResponse(BaseModel):
    note_document_id: UUID
    extracted_text: str


class Flashcard(BaseModel):
    question: str
    answer: str


class PracticeQuestion(BaseModel):
    question: str
    options: List[str]  # 4 options
    correct_index: int
    explanation: str


class StudyMaterialResponse(BaseModel):
    summary_short: str
    summary_detailed: str
    flashcards: List[Flashcard]
    practice_questions: List[PracticeQuestion]


class GenerateStudyRequest(BaseModel):
    note_document_id: UUID
    topic_hint: Optional[str] = None


class TextNoteRequest(BaseModel):
    text: str
    title: str = "Untitled Notes"
