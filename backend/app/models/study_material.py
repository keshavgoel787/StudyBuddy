import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base


class StudyMaterial(Base):
    __tablename__ = "study_material"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_document_id = Column(UUID(as_uuid=True), ForeignKey("note_documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    summary_short = Column(Text, nullable=False)
    summary_detailed = Column(Text, nullable=False)
    flashcards = Column(JSONB, nullable=False)  # [{"question": "...", "answer": "..."}]
    practice_questions = Column(JSONB, nullable=False)  # [{"question": "...", "options": [...], "correct_index": 0, "explanation": "..."}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
