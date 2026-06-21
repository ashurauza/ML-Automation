from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import random
import logging
from database import get_db
from models import User, Estimation, Supplier, SupplierQuote, SupplierQuoteResponse, SupplierResponse
from routes.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/suppliers", response_model=List[SupplierResponse])
def get_suppliers(db: Session = Depends(get_db)):
    """Get list of available suppliers."""
    return db.query(Supplier).all()

@router.post("/estimate/{estimation_id}/request_quotes", response_model=List[SupplierQuoteResponse])
def request_quotes(
    estimation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate simulated marketplace quotes for a given estimation."""
    estimation = db.query(Estimation).filter(
        Estimation.id == estimation_id, 
        Estimation.user_id == current_user.id
    ).first()
    
    if not estimation:
        raise HTTPException(status_code=404, detail="Estimation not found")
        
    if not estimation.total_cost or estimation.total_cost <= 0:
        raise HTTPException(status_code=400, detail="Estimation must have a calculated cost first")

    # Check if quotes already exist
    existing_quotes = db.query(SupplierQuote).filter(SupplierQuote.estimation_id == estimation_id).all()
    if existing_quotes:
        return existing_quotes

    # Get all dummy suppliers
    suppliers = db.query(Supplier).filter(Supplier.is_dummy == True).all()
    if not suppliers:
        raise HTTPException(status_code=500, detail="No marketplace suppliers available")

    # Generate simulated bids based on the estimated cost
    base_cost = estimation.total_cost
    generated_quotes = []
    
    for supplier in suppliers:
        # FastTurn CNC: Expensive but fast
        if "FastTurn" in supplier.name:
            price_multiplier = random.uniform(1.10, 1.25)
            lead_time = random.randint(3, 7)
        # Global Fab Solutions: Cheap but slow
        elif "Global" in supplier.name:
            price_multiplier = random.uniform(0.75, 0.90)
            lead_time = random.randint(21, 35)
        # Precision Machining Co: Balanced
        else:
            price_multiplier = random.uniform(0.95, 1.05)
            lead_time = random.randint(10, 15)
            
        quote = SupplierQuote(
            estimation_id=estimation.id,
            supplier_id=supplier.id,
            quoted_price=round(base_cost * price_multiplier, 2),
            lead_time_days=lead_time,
            status="pending"
        )
        db.add(quote)
        generated_quotes.append(quote)
        
    db.commit()
    for q in generated_quotes:
        db.refresh(q)
        
    return generated_quotes

@router.get("/estimate/{estimation_id}/quotes", response_model=List[SupplierQuoteResponse])
def get_quotes(
    estimation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all quotes for a given estimation."""
    # Ensure user owns this estimation
    estimation = db.query(Estimation).filter(
        Estimation.id == estimation_id, 
        Estimation.user_id == current_user.id
    ).first()
    
    if not estimation:
        raise HTTPException(status_code=404, detail="Estimation not found")
        
    return db.query(SupplierQuote).filter(SupplierQuote.estimation_id == estimation_id).all()

@router.post("/quotes/{quote_id}/accept", response_model=SupplierQuoteResponse)
def accept_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a specific quote and reject others for the same estimation."""
    quote = db.query(SupplierQuote).filter(SupplierQuote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
        
    # Verify ownership
    estimation = db.query(Estimation).filter(
        Estimation.id == quote.estimation_id, 
        Estimation.user_id == current_user.id
    ).first()
    
    if not estimation:
        raise HTTPException(status_code=403, detail="Not authorized to accept this quote")
        
    # Accept this quote
    quote.status = "accepted"
    
    # Reject all other quotes for this estimation
    other_quotes = db.query(SupplierQuote).filter(
        SupplierQuote.estimation_id == quote.estimation_id,
        SupplierQuote.id != quote.id
    ).all()
    
    for other in other_quotes:
        other.status = "rejected"
        
    db.commit()
    db.refresh(quote)
    return quote
