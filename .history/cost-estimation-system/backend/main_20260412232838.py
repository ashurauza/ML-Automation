"""
Main FastAPI application for AI-Driven Cost Estimation System
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
from dotenv import load_dotenv
from routes import estimation, parameters, health
from database import init_db
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Cost Estimation System",
    description="Automated cost estimation for mechanical part manufacturing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")
    init_db()
    logger.info("Database initialized")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cost-estimation-system"}

# Include routers
app.include_router(estimation.router, prefix="/api/estimation", tags=["Estimation"])
app.include_router(parameters.router, prefix="/api/parameters", tags=["Parameters"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])

@app.get("/")
async def root():
    return {
        "message": "AI-Driven Cost Estimation System",
        "version": "1.0.0",
        "endpoints": {
            "estimation": "/api/estimation",
            "parameters": "/api/parameters",
            "health": "/api/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
