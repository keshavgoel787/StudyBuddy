from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.note_document import NoteDocument
from app.models.study_material import StudyMaterial
from app.schemas.notes import (
    NoteUploadResponse,
    StudyMaterialResponse,
    GenerateStudyRequest,
    TextNoteRequest
)
from app.utils.auth_middleware import get_current_user
from app.services.storage import save_uploaded_file, get_file_path
from app.services.ocr_service import extract_text_from_image
from app.services.gemini_service import generate_study_material

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/upload", response_model=NoteUploadResponse)
async def upload_note(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    title: str = Form("Untitled Notes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload notes - either as an image file (for OCR) or as plain text.
    """
    # Debug logging
    print(f"DEBUG: file={file}, text={text}, title={title}")

    if not file and (not text or text.strip() == ""):
        raise HTTPException(status_code=400, detail="Either file or text must be provided")

    if file and text and text.strip() != "":
        raise HTTPException(status_code=400, detail="Provide either file or text, not both")

    try:
        extracted_text = ""
        file_url = None

        if file:
            # Save uploaded file
            file_url = save_uploaded_file(file, subfolder="notes")

            # Check if it's an image (for OCR)
            if file.content_type and file.content_type.startswith("image/"):
                # Perform OCR
                full_path = get_file_path(file_url)
                extracted_text = extract_text_from_image(full_path)

                if not extracted_text:
                    raise HTTPException(status_code=400, detail="No text could be extracted from the image")
            else:
                raise HTTPException(status_code=400, detail="Only image files are supported for upload")

        else:
            # Use provided text
            extracted_text = text

        # Create note document
        note_doc = NoteDocument(
            user_id=current_user.id,
            title=title,
            original_file_url=file_url,
            extracted_text=extracted_text
        )
        db.add(note_doc)
        db.commit()
        db.refresh(note_doc)

        return NoteUploadResponse(
            note_document_id=note_doc.id,
            extracted_text=extracted_text
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload note: {str(e)}")


@router.post("/generate-study", response_model=StudyMaterialResponse)
async def generate_study(
    request: GenerateStudyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate study material (summaries, flashcards, practice questions) from a note document.
    """
    try:
        # Get note document
        note_doc = db.query(NoteDocument).filter(
            NoteDocument.id == request.note_document_id,
            NoteDocument.user_id == current_user.id
        ).first()

        if not note_doc:
            raise HTTPException(status_code=404, detail="Note document not found")

        # Check if study material already exists
        existing_material = db.query(StudyMaterial).filter(
            StudyMaterial.note_document_id == note_doc.id
        ).first()

        if existing_material:
            # Return existing material
            return StudyMaterialResponse(
                summary_short=existing_material.summary_short,
                summary_detailed=existing_material.summary_detailed,
                flashcards=existing_material.flashcards,
                practice_questions=existing_material.practice_questions
            )

        # Generate new study material using Gemini
        topic_hint = request.topic_hint if hasattr(request, 'topic_hint') else None
        material_data = generate_study_material(note_doc.extracted_text, topic_hint)

        # Save to database
        study_material = StudyMaterial(
            note_document_id=note_doc.id,
            summary_short=material_data['summary_short'],
            summary_detailed=material_data['summary_detailed'],
            flashcards=material_data['flashcards'],
            practice_questions=material_data['practice_questions']
        )
        db.add(study_material)
        db.commit()
        db.refresh(study_material)

        return StudyMaterialResponse(
            summary_short=study_material.summary_short,
            summary_detailed=study_material.summary_detailed,
            flashcards=study_material.flashcards,
            practice_questions=study_material.practice_questions
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate study material: {str(e)}")


@router.get("/{note_document_id}/study", response_model=StudyMaterialResponse)
async def get_study_material(
    note_document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get study material for a specific note document.
    """
    try:
        # Verify note belongs to user
        note_doc = db.query(NoteDocument).filter(
            NoteDocument.id == note_document_id,
            NoteDocument.user_id == current_user.id
        ).first()

        if not note_doc:
            raise HTTPException(status_code=404, detail="Note document not found")

        # Get study material
        study_material = db.query(StudyMaterial).filter(
            StudyMaterial.note_document_id == note_document_id
        ).first()

        if not study_material:
            raise HTTPException(status_code=404, detail="Study material not found. Generate it first.")

        return StudyMaterialResponse(
            summary_short=study_material.summary_short,
            summary_detailed=study_material.summary_detailed,
            flashcards=study_material.flashcards,
            practice_questions=study_material.practice_questions
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch study material: {str(e)}")
