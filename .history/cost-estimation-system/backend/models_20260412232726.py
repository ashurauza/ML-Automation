"""
Database models for cost estimation system
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from .database import Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, List

# SQLAlchemy ORM Models
class Estimation(Base):
    __tablename__ = "estimations"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    # Extracted parameters
    dimensions = Column(SQLiteJSON)
    material_type = Column(String(100))
    surface_finish = Column(String(100))
    tolerances = Column(SQLiteJSON)
    geometric_features = Column(SQLiteJSON)
    
    # Cost breakdown
    raw_material_cost = Column(Float)
    machining_cost = Column(Float)
    manpower_cost = Column(Float)
    overhead_cost = Column(Float)
    logistics_cost = Column(Float)
    profit_margin = Column(Float)
    total_cost = Column(Float)
    
    # Additional info
    estimated_cycle_time = Column(Float)
    manufacturing_operations = Column(SQLiteJSON)
    confidence_score = Column(Float)
    notes = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CostParameter(Base):
    __tablename__ = "cost_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    parameter_name = Column(String(100), unique=True, index=True)
    parameter_value = Column(Float)
    description = Column(String(255))
    is_editable = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Request/Response Models
class DimensionData(BaseModel):
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    diameter: Optional[float] = None
    radius: Optional[float] = None
    thickness: Optional[float] = None
    unit: str = "mm"


class ExtractedParameters(BaseModel):
    dimensions: DimensionData
    material_type: str
    surface_finish: Optional[str] = None
    tolerances: Dict[str, float]
    geometric_features: List[str]
    estimated_weight: Optional[float] = None


class CostBreakdown(BaseModel):
    raw_material_cost: float
    machining_cost: float
    manpower_cost: float
    overhead_cost: float
    logistics_cost: float
    subtotal: float
    profit_margin: float
    total_cost: float


class EstimationResponse(BaseModel):
    id: Optional[int] = None
    filename: str
    extracted_parameters: ExtractedParameters
    cost_breakdown: CostBreakdown
    estimated_cycle_time: float
    manufacturing_operations: List[str]
    confidence_score: float
    notes: str
    
    class Config:
        from_attributes = True


class CostParameterUpdate(BaseModel):
    parameter_name: str
    parameter_value: float
    description: Optional[str] = None


class EstimationHistory(BaseModel):
    id: int
    filename: str
    total_cost: float
    upload_date: datetime
    material_type: str
    
    class Config:
        from_attributes = True
