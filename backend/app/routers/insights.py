from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db, schemas, crud, CommunityInsight
from app.services import vertex_ai

router = APIRouter(
    prefix="/insights",
    tags=["insights"]
)

@router.post("/generate", response_model=List[schemas.CommunityInsight], status_code=status.HTTP_201_CREATED)
def generate_and_store_insights(db: Session = Depends(get_db)):
    """
    Fetch raw community indicators from AlloyDB, pass to Vertex AI Gemini to generate
    trends, health scores, resource allocation plans, and sustainability recommendations,
    and save the results back into AlloyDB.
    """
    # 1. Fetch community data
    records = crud.get_all_community_data(db)
    if not records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No community records found in database. Ingest a dataset before generating insights."
        )

    try:
        # 2. Call Vertex AI service to generate structured insights
        generated = vertex_ai.generate_insights(records)
        
        if not generated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vertex AI failed to generate any valid insights."
            )
            
        # 3. Clear existing insights to keep recommendations fresh
        db.query(CommunityInsight).delete()
        db.commit()
        
        # 4. Save new insights to database
        stored_insights = []
        for item in generated:
            db_insight = crud.create_community_insight(
                db=db,
                area=item["area"],
                insight=item["insight"],
                priority_score=item["priority_score"],
                recommendation=item["recommendation"]
            )
            stored_insights.append(db_insight)
            
        return stored_insights
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insight generation failed: {str(e)}"
        )

@router.get("", response_model=List[schemas.CommunityInsight])
def list_insights(db: Session = Depends(get_db)):
    """
    Retrieve all stored community insights, ordered by priority score descending.
    """
    try:
        return crud.get_all_insights(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch insights: {str(e)}"
        )
