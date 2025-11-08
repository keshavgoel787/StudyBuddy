from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.note_document import NoteDocument
from app.models.study_material import StudyMaterial
from app.schemas.notes import (
    NoteUploadResponse,
    StudyMaterialResponse,
    GenerateStudyRequest,
    CombineNotesRequest,
    NoteDocumentResponse
)
from app.utils.auth_middleware import get_current_user
from app.utils.rate_limiter import limiter
from app.services.storage import save_uploaded_file, get_file_path
from app.services.ocr_service import extract_text_from_image
from app.services.gemini_service import generate_study_material, generate_combined_study_guide

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=List[NoteDocumentResponse])
async def get_all_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all notes for the current user.
    Optimized with LEFT JOIN to avoid N+1 queries.
    """
    from sqlalchemy import case

    # Single query with LEFT JOIN to get notes and check for study materials
    results = db.query(
        NoteDocument.id,
        NoteDocument.title,
        NoteDocument.created_at,
        case(
            (StudyMaterial.id.isnot(None), True),
            else_=False
        ).label('has_study_material')
    ).outerjoin(
        StudyMaterial,
        StudyMaterial.note_document_id == NoteDocument.id
    ).filter(
        NoteDocument.user_id == current_user.id
    ).order_by(NoteDocument.created_at.desc()).all()

    # Convert to response models
    return [
        NoteDocumentResponse(
            id=row.id,
            title=row.title,
            created_at=row.created_at,
            has_study_material=row.has_study_material
        )
        for row in results
    ]


@router.delete("/{note_document_id}")
async def delete_note(
    note_document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a note document and its associated study materials.
    """
    note_doc = db.query(NoteDocument).filter(
        NoteDocument.id == note_document_id,
        NoteDocument.user_id == current_user.id
    ).first()

    if not note_doc:
        raise HTTPException(status_code=404, detail="Note document not found")

    db.delete(note_doc)
    db.commit()

    return {"message": "Note deleted successfully"}


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
                # Perform OCR (async wrapper for blocking Tesseract call)
                import asyncio
                full_path = get_file_path(file_url)
                extracted_text = await asyncio.to_thread(extract_text_from_image, full_path)

                if not extracted_text or len(extracted_text.strip()) < 10:
                    raise HTTPException(
                        status_code=400,
                        detail="No meaningful text could be extracted from the image. Please ensure the image is clear and contains readable text."
                    )
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
@limiter.limit("10/hour")  # Limit to 10 generations per hour per user
async def generate_study(
    request: Request,
    body: GenerateStudyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate study material (summaries, flashcards, practice questions) from a note document.
    Rate limited to prevent API abuse (10 requests per hour).
    """
    try:
        # Get note document
        note_doc = db.query(NoteDocument).filter(
            NoteDocument.id == body.note_document_id,
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

        # Generate new study material using Gemini (async wrapper for blocking call)
        import asyncio
        topic_hint = body.topic_hint if hasattr(body, 'topic_hint') else None
        material_data = await asyncio.to_thread(
            generate_study_material,
            note_doc.extracted_text,
            topic_hint
        )

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

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Log the full error for debugging
        import traceback
        print(f"ERROR in generate_study: {str(e)}")
        print(traceback.format_exc())
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


@router.post("/combine-notes", response_model=StudyMaterialResponse)
@limiter.limit("5/hour")  # Limit to 5 combinations per hour per user (more expensive operation)
async def combine_notes(
    request: Request,
    body: CombineNotesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Combine multiple notes into one comprehensive study guide.

    This endpoint generates a unified study guide that synthesizes information
    from multiple note documents, showing connections between concepts.

    Rate limited to 5 requests per hour to prevent API abuse.
    """
    try:
        # Validate that at least 2 notes are provided
        if len(body.note_document_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="Please provide at least 2 notes to combine"
            )

        if len(body.note_document_ids) > 10:
            raise HTTPException(
                status_code=400,
                detail="Cannot combine more than 10 notes at once"
            )

        # Fetch all note documents and verify ownership
        note_docs = []
        for note_id in body.note_document_ids:
            note_doc = db.query(NoteDocument).filter(
                NoteDocument.id == note_id,
                NoteDocument.user_id == current_user.id
            ).first()

            if not note_doc:
                raise HTTPException(
                    status_code=404,
                    detail=f"Note document {note_id} not found or you don't have access"
                )

            note_docs.append(note_doc)

        # Extract texts and titles
        note_texts = [doc.extracted_text for doc in note_docs]
        note_titles = [doc.title for doc in note_docs]

        # Validate that all notes have content
        for i, text in enumerate(note_texts):
            if not text or len(text.strip()) < 10:
                raise HTTPException(
                    status_code=400,
                    detail=f"Note '{note_titles[i]}' has insufficient content to combine"
                )

        # Generate combined study guide using Gemini (async wrapper)
        import asyncio
        topic_hint = body.topic_hint if hasattr(body, 'topic_hint') else None
        combined_material = await asyncio.to_thread(
            generate_combined_study_guide,
            note_texts,
            note_titles,
            topic_hint
        )

        # If user wants to save to library, create a new note document and study material
        if body.save_to_library:
            # Generate combined title
            combined_title = body.combined_title if body.combined_title else f"Combined: {', '.join(note_titles[:3])}{'...' if len(note_titles) > 3 else ''}"

            # Create combined text from all notes
            combined_text = "\n\n=== COMBINED NOTES ===\n\n"
            for title, text in zip(note_titles, note_texts):
                combined_text += f"\n--- {title} ---\n{text}\n"

            # Create note document
            note_doc = NoteDocument(
                user_id=current_user.id,
                title=combined_title,
                original_file_url=None,  # No file for combined notes
                extracted_text=combined_text
            )
            db.add(note_doc)
            db.flush()  # Get the ID without committing

            # Save study material
            study_material = StudyMaterial(
                note_document_id=note_doc.id,
                summary_short=combined_material['summary_short'],
                summary_detailed=combined_material['summary_detailed'],
                flashcards=combined_material['flashcards'],
                practice_questions=combined_material['practice_questions']
            )
            db.add(study_material)
            db.commit()
            db.refresh(note_doc)

        # Return the combined study guide
        return StudyMaterialResponse(
            summary_short=combined_material['summary_short'],
            summary_detailed=combined_material['summary_detailed'],
            flashcards=combined_material['flashcards'],
            practice_questions=combined_material['practice_questions']
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"ERROR in combine_notes: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to combine notes: {str(e)}"
        )
