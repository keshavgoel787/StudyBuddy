from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional


class NoteDocumentResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    has_study_material: bool = False

    class Config:
        from_attributes = True


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


class CombineNotesRequest(BaseModel):
    note_document_ids: List[UUID]
    combined_title: Optional[str] = None
    topic_hint: Optional[str] = None
