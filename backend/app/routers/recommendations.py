from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db, schemas, crud
from app.services import vertex_ai

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"]
)

def calculate_traffic_score(traffic_str: str) -> float:
    """Map traffic value to a numeric scale. If it's already numeric, use its float value. Otherwise, map Low/Medium/High to 10/50/100."""
    if not traffic_str:
        return 10.0
    val = traffic_str.strip().lower()
    if val == "high":
        return 100.0
    elif val == "medium":
        return 50.0
    elif val == "low":
        return 10.0
    try:
        return float(val)
    except ValueError:
        return 10.0  # Default to Low traffic score

@router.get("", response_model=List[schemas.RecommendationResponse], status_code=status.HTTP_200_OK)
def get_prioritized_recommendations(db: Session = Depends(get_db)):
    """
    Fetch raw indicators, compute risk scores using the solution architect formula,
    rank wards by urgency, and query Vertex AI to supply actions and resource allocation plans.
    """
    # 1. Fetch community records
    records = crud.get_all_community_data(db)
    if not records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No community metrics available. Ingest a dataset before compiling recommendations."
        )

    try:
        # 2. Compute risk scores and prepare structural payloads
        scored_areas = []
        for r in records:
            traffic_score = calculate_traffic_score(r.traffic)
            # Solution architect risk formula:
            # Risk Score = 0.4 * complaints + 0.3 * traffic + 0.3 * AQI
            risk_score = (0.4 * r.complaints) + (0.3 * traffic_score) + (0.3 * r.aqi)
            
            scored_areas.append({
                "area": r.area,
                "complaints": r.complaints,
                "traffic": r.traffic or "Low",
                "aqi": r.aqi,
                "risk_score": round(risk_score, 2),
                "rank": 0  # Placeholder to be filled post-sorting
            })
            
        # 3. Sort by risk score descending (Priority Ranking)
        scored_areas.sort(key=lambda x: x["risk_score"], reverse=True)
        
        # 4. Apply priority ranks
        for idx, item in enumerate(scored_areas, start=1):
            item["rank"] = idx

        # 5. Invoke Vertex AI service to append action plans and budgets
        recommendations = vertex_ai.generate_recommendations(scored_areas)
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate decision recommendations: {str(e)}"
        )
