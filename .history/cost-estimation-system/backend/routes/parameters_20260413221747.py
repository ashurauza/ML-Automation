"""
Routes for managing cost parameters
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import CostParameter, CostParameterUpdate
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_all_parameters(db: Session = Depends(get_db)):
    """
    Get all cost parameters
    """
    try:
        parameters = db.query(CostParameter).all()
        return {
            "status": "success",
            "total": len(parameters),
            "parameters": [
                {
                    "id": p.id,
                    "parameter_name": p.parameter_name,
                    "parameter_value": p.parameter_value,
                    "description": p.description,
                    "is_editable": p.is_editable
                }
                for p in parameters
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving parameters: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving parameters")


@router.get("/{parameter_name}")
async def get_parameter(
    parameter_name: str,
    db: Session = Depends(get_db)
):
    """
    Get specific cost parameter
    """
    try:
        parameter = db.query(CostParameter).filter(
            CostParameter.parameter_name == parameter_name
        ).first()
        
        if not parameter:
            raise HTTPException(status_code=404, detail="Parameter not found")
        
        return {
            "status": "success",
            "parameter": {
                "id": parameter.id,
                "parameter_name": parameter.parameter_name,
                "parameter_value": parameter.parameter_value,
                "description": parameter.description,
                "is_editable": parameter.is_editable
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving parameter: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving parameter")


@router.post("/")
async def create_parameter(
    param: CostParameterUpdate,
    db: Session = Depends(get_db)
):
    """
    Create new cost parameter
    """
    try:
        # Check if parameter already exists
        existing = db.query(CostParameter).filter(
            CostParameter.parameter_name == param.parameter_name
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Parameter already exists")
        
        new_param = CostParameter(
            parameter_name=param.parameter_name,
            parameter_value=param.parameter_value,
            description=param.description
        )
        
        db.add(new_param)
        db.commit()
        db.refresh(new_param)
        
        logger.info(f"Parameter created: {param.parameter_name}")
        
        return {
            "status": "success",
            "message": "Parameter created successfully",
            "parameter_id": new_param.id
        }
    except Exception as e:
        logger.error(f"Error creating parameter: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating parameter")


@router.put("/{parameter_name}")
async def update_parameter(
    parameter_name: str,
    param: CostParameterUpdate,
    db: Session = Depends(get_db)
):
    """
    Update cost parameter
    """
    try:
        parameter = db.query(CostParameter).filter(
            CostParameter.parameter_name == parameter_name
        ).first()
        
        if not parameter:
            raise HTTPException(status_code=404, detail="Parameter not found")
        
        if not parameter.is_editable:
            raise HTTPException(status_code=403, detail="Parameter is not editable")
        
        parameter.parameter_value = param.parameter_value
        if param.description:
            parameter.description = param.description
        
        db.commit()
        db.refresh(parameter)
        
        logger.info(f"Parameter updated: {parameter_name}")
        
        return {
            "status": "success",
            "message": "Parameter updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating parameter: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating parameter")


@router.delete("/{parameter_name}")
async def delete_parameter(
    parameter_name: str,
    db: Session = Depends(get_db)
):
    """
    Delete cost parameter
    """
    try:
        parameter = db.query(CostParameter).filter(
            CostParameter.parameter_name == parameter_name
        ).first()
        
        if not parameter:
            raise HTTPException(status_code=404, detail="Parameter not found")
        
        db.delete(parameter)
        db.commit()
        
        logger.info(f"Parameter deleted: {parameter_name}")
        
        return {
            "status": "success",
            "message": "Parameter deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting parameter: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting parameter")
