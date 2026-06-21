"""
Routes for managing cost parameters and user settings
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import UserCostSettings, UserCostSettingsUpdate, UserCostSettingsResponse, User
from routes.auth import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/settings", response_model=UserCostSettingsResponse)
async def get_user_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the custom cost settings for the authenticated user.
    """
    try:
        settings = db.query(UserCostSettings).filter(UserCostSettings.user_id == current_user.id).first()
        if not settings:
            # Fallback to defaults if missing for some reason
            settings = UserCostSettings(user_id=current_user.id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
            
        return settings
    except Exception as e:
        logger.error(f"Error retrieving user settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving user settings")


@router.put("/settings", response_model=UserCostSettingsResponse)
async def update_user_settings(
    settings_update: UserCostSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the custom cost settings for the authenticated user.
    """
    try:
        settings = db.query(UserCostSettings).filter(UserCostSettings.user_id == current_user.id).first()
        if not settings:
            settings = UserCostSettings(user_id=current_user.id)
            db.add(settings)
            
        # Update only provided fields
        if settings_update.material_cost_multiplier is not None:
            settings.material_cost_multiplier = settings_update.material_cost_multiplier
        if settings_update.machining_rate is not None:
            settings.machining_rate = settings_update.machining_rate
        if settings_update.labor_rate is not None:
            settings.labor_rate = settings_update.labor_rate
        if settings_update.overhead_percentage is not None:
            settings.overhead_percentage = settings_update.overhead_percentage
        if settings_update.profit_margin is not None:
            settings.profit_margin = settings_update.profit_margin
            
        db.commit()
        db.refresh(settings)
        
        logger.info(f"Updated settings for user {current_user.id}")
        return settings
    except Exception as e:
        logger.error(f"Error updating user settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating user settings")
