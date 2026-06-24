from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, schemas, crud
from app.services import vertex_ai

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

@router.post("/message", response_model=schemas.ChatMessageResponse, status_code=status.HTTP_200_OK)
def send_assistant_message(
    payload: schemas.ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a user natural language query, fetch community records from AlloyDB,
    formulate the context, and return the AI Assistant evaluation using Vertex AI / Gemini.
    """
    try:
        # 1. Fetch community data context from database
        records = crud.get_all_community_data(db)
        
        # 2. Query Gemini / Vertex AI service
        ai_response = vertex_ai.get_gemini_response(
            db_records=records,
            question=payload.message,
            chat_history=payload.history
        )
        
        return schemas.ChatMessageResponse(response=ai_response)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the assistant response: {str(e)}"
        )
