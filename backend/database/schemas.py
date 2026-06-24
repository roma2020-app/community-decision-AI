from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

# ==========================================
# Community Data Schemas
# ==========================================

class CommunityDataBase(BaseModel):
    area: str = Field(..., description="The neighborhood or region name")
    complaints: int = Field(default=0, ge=0, description="Number of community complaints")
    traffic: str = Field(default="Low", description="Traffic density tier (Low, Medium, High)")
    aqi: int = Field(default=0, ge=0, description="Air Quality Index")
    timestamp: Optional[datetime] = Field(default=None, description="Time the record was recorded")

class CommunityDataCreate(CommunityDataBase):
    pass

class CommunityData(CommunityDataBase):
    id: int

    class Config:
        from_attributes = True


# ==========================================
# Community Insight Schemas
# ==========================================

class CommunityInsightBase(BaseModel):
    area: str = Field(..., description="The neighborhood or region name")
    insight: str = Field(..., description="The AI-generated insights content")
    priority_score: float = Field(default=0.0, ge=0.0, le=10.0, description="Severity priority score between 0.0 and 10.0")
    recommendation: str = Field(..., description="Proposed policy action or recommendation")
    created_at: Optional[datetime] = Field(default=None, description="Time the insight was generated")

class CommunityInsightCreate(CommunityInsightBase):
    pass

class CommunityInsight(CommunityInsightBase):
    id: int

    class Config:
        from_attributes = True


# ==========================================
# Upload Summary Schemas
# ==========================================

class UploadSummary(BaseModel):
    filename: str
    total_rows: int
    inserted_rows: int
    ignored_duplicates: int
    errors: List[str]


# ==========================================
# Chat Assistant Schemas
# ==========================================

class ChatMessageRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

class ChatMessageResponse(BaseModel):
    response: str


# ==========================================
# Recommendation Engine Schemas
# ==========================================

class RecommendationResponse(BaseModel):
    area: str
    risk_score: float
    rank: int
    traffic: str
    complaints: int
    aqi: int
    recommended_actions: str
    resource_allocation: str


