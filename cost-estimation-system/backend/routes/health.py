"""
Health check routes
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/status")
async def health_status():
    """
    Get system health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "cost-estimation-system",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check():
    """
    Check if system is ready to accept requests
    """
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }
