"""
Database models for cost estimation system
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from database import Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, List, Any

# SQLAlchemy ORM Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    tier = Column(String(50), default="Free")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    estimations = relationship("Estimation", back_populates="owner")
    settings = relationship("UserCostSettings", back_populates="user", uselist=False)

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
    
    # OpenCV Diagram Info
    diagram_count = Column(Integer)
    diagram_area_ratio = Column(Float)
    line_density = Column(Float)
    diagram_images = Column(SQLiteJSON)
    diagram_analysis = Column(SQLiteJSON)
    
    # Additional info
    estimated_cycle_time = Column(Float)
    manufacturing_operations = Column(SQLiteJSON)
    confidence_score = Column(Float)
    notes = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="estimations")

class UserCostSettings(Base):
    __tablename__ = "user_cost_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    material_cost_multiplier = Column(Float, default=1.2)
    machining_rate = Column(Float, default=50.0)
    labor_rate = Column(Float, default=25.0)
    overhead_percentage = Column(Float, default=15.0)
    profit_margin = Column(Float, default=20.0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="settings")


class CostParameter(Base):
    __tablename__ = "cost_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    parameter_name = Column(String(100), unique=True, index=True)
    parameter_value = Column(Float)
    description = Column(String(255))
    is_editable = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    rating = Column(Float, default=5.0)
    location = Column(String(255))
    specialty = Column(String(255))
    is_dummy = Column(Boolean, default=True)
    
    quotes = relationship("SupplierQuote", back_populates="supplier")

class SupplierQuote(Base):
    __tablename__ = "supplier_quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    estimation_id = Column(Integer, ForeignKey("estimations.id"), index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True)
    
    quoted_price = Column(Float)
    lead_time_days = Column(Integer)
    status = Column(String(50), default="pending")  # pending, accepted, rejected
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    estimation = relationship("Estimation")
    supplier = relationship("Supplier", back_populates="quotes")


# Pydantic Request/Response Models
class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    tier: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

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
    diagram_count: Optional[int] = None
    diagram_area_ratio: Optional[float] = None
    line_density: Optional[float] = None
    diagram_images: Optional[List[str]] = None
    diagram_analysis: Optional[Dict[str, Any]] = None


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


class UserCostSettingsUpdate(BaseModel):
    material_cost_multiplier: Optional[float] = None
    machining_rate: Optional[float] = None
    labor_rate: Optional[float] = None
    overhead_percentage: Optional[float] = None
    profit_margin: Optional[float] = None

class UserCostSettingsResponse(BaseModel):
    material_cost_multiplier: float
    machining_rate: float
    labor_rate: float
    overhead_percentage: float
    profit_margin: float
    
    class Config:
        from_attributes = True


class EstimationHistory(BaseModel):
    id: int
    filename: str
    total_cost: float
    upload_date: datetime
    material_type: str
    
    class Config:
        from_attributes = True

class SupplierResponse(BaseModel):
    id: int
    name: str
    rating: float
    location: str
    specialty: str
    
    class Config:
        from_attributes = True

class SupplierQuoteResponse(BaseModel):
    id: int
    estimation_id: int
    supplier_id: int
    quoted_price: float
    lead_time_days: int
    status: str
    created_at: datetime
    supplier: SupplierResponse
    
    class Config:
        from_attributes = True
