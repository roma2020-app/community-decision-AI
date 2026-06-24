from sqlalchemy import Column, Integer, String, Text, Float, DateTime, func
from .connection import Base

class CommunityData(Base):
    __tablename__ = "community_data"

    id = Column(Integer, primary_key=True, index=True)
    area = Column(String(255), nullable=False, index=True)
    complaints = Column(Integer, default=0)
    traffic = Column(String(50))
    aqi = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())


class CommunityInsight(Base):
    __tablename__ = "community_insights"

    id = Column(Integer, primary_key=True, index=True)
    area = Column(String(255), nullable=False, index=True)
    insight = Column(Text, nullable=False)
    priority_score = Column(Float, default=0.0)
    recommendation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
