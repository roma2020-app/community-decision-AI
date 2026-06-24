from sqlalchemy.orm import Session
from .models import CommunityData, CommunityInsight
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

# ==========================================
# CRUD Operations for Community Data
# ==========================================

def create_community_data(
    db: Session, 
    area: str, 
    complaints: int = 0, 
    traffic: str = "Low", 
    aqi: int = 0,
    timestamp: Optional[datetime] = None
) -> CommunityData:
    """Create a new community data record."""
    db_data = CommunityData(
        area=area,
        complaints=complaints,
        traffic=traffic,
        aqi=aqi,
        timestamp=timestamp or datetime.now(timezone.utc)
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

def get_community_data_by_id(db: Session, data_id: int) -> Optional[CommunityData]:
    """Retrieve a single community data record by its ID."""
    return db.query(CommunityData).filter(CommunityData.id == data_id).first()

def get_all_community_data(
    db: Session, 
    limit: int = 100, 
    skip: int = 0
) -> List[CommunityData]:
    """Retrieve list of community data records with pagination."""
    return db.query(CommunityData).offset(skip).limit(limit).all()

def get_community_data_by_area(db: Session, area: str) -> List[CommunityData]:
    """Retrieve community data records filtered by area name."""
    return db.query(CommunityData).filter(CommunityData.area.ilike(area)).all()

def update_community_data(
    db: Session, 
    data_id: int, 
    updates: Dict[str, Any]
) -> Optional[CommunityData]:
    """Update field values of a community data record."""
    db_data = get_community_data_by_id(db, data_id)
    if not db_data:
        return None
    
    for key, value in updates.items():
        if hasattr(db_data, key):
            setattr(db_data, key, value)
            
    db.commit()
    db.refresh(db_data)
    return db_data

def delete_community_data(db: Session, data_id: int) -> bool:
    """Delete a community data record."""
    db_data = get_community_data_by_id(db, data_id)
    if not db_data:
        return False
    db.delete(db_data)
    db.commit()
    return True


# ==========================================
# CRUD Operations for Community Insights
# ==========================================

def create_community_insight(
    db: Session, 
    area: str, 
    insight: str, 
    priority_score: float = 0.0, 
    recommendation: str = "",
    created_at: Optional[datetime] = None
) -> CommunityInsight:
    """Create a new AI-generated community insight record."""
    db_insight = CommunityInsight(
        area=area,
        insight=insight,
        priority_score=priority_score,
        recommendation=recommendation,
        created_at=created_at or datetime.now(timezone.utc)
    )
    db.add(db_insight)
    db.commit()
    db.refresh(db_insight)
    return db_insight

def get_community_insight_by_id(db: Session, insight_id: int) -> Optional[CommunityInsight]:
    """Retrieve a single community insight record by its ID."""
    return db.query(CommunityInsight).filter(CommunityInsight.id == insight_id).first()

def get_all_insights(
    db: Session, 
    limit: int = 100, 
    skip: int = 0
) -> List[CommunityInsight]:
    """Retrieve list of community insights with pagination."""
    return db.query(CommunityInsight).order_by(CommunityInsight.priority_score.desc()).offset(skip).limit(limit).all()

def get_insights_by_area(db: Session, area: str) -> List[CommunityInsight]:
    """Retrieve community insights filtered by area name."""
    return db.query(CommunityInsight).filter(CommunityInsight.area.ilike(area)).all()

def update_community_insight(
    db: Session, 
    insight_id: int, 
    updates: Dict[str, Any]
) -> Optional[CommunityInsight]:
    """Update field values of a community insight record."""
    db_insight = get_community_insight_by_id(db, insight_id)
    if not db_insight:
        return None
    
    for key, value in updates.items():
        if hasattr(db_insight, key):
            setattr(db_insight, key, value)
            
    db.commit()
    db.refresh(db_insight)
    return db_insight

def delete_community_insight(db: Session, insight_id: int) -> bool:
    """Delete a community insight record."""
    db_insight = get_community_insight_by_id(db, insight_id)
    if not db_insight:
        return False
    db.delete(db_insight)
    db.commit()
    return True
