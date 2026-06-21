"""
Main FastAPI application for AI-Driven Cost Estimation System
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from routes import estimation, parameters, auth, health, marketplace
from models import Base, User, Estimation, UserCostSettings, Supplier
from database import engine, get_db
from services.auth_service import get_password_hash
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

# Ensure uploads directory exists and mount it
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")
    from database import init_db
    init_db()
    logger.info("Database initialized")
    # Database migration for existing records
    db = next(get_db())
    try:
        from sqlalchemy import text
        try:
            db.execute(text("ALTER TABLE estimations ADD COLUMN user_id INTEGER REFERENCES users(id)"))
            db.commit()
            logger.info("Added user_id column to estimations table.")
        except Exception:
            db.rollback()
            pass # Column already exists
            
        # Check if admin user exists
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                tier="Pro"
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
        # Assign all unassigned estimations to admin
        unassigned = db.query(Estimation).filter(Estimation.user_id == None).all()
        if unassigned:
            for est in unassigned:
                est.user_id = admin.id
            db.commit()
            logger.info(f"Assigned {len(unassigned)} existing estimations to admin user.")
            
        # Ensure all users have default cost settings
        users = db.query(User).all()
        settings_created = 0
        for user in users:
            settings = db.query(UserCostSettings).filter(UserCostSettings.user_id == user.id).first()
            if not settings:
                default_settings = UserCostSettings(user_id=user.id)
                db.add(default_settings)
                settings_created += 1
        if settings_created > 0:
            db.commit()
            logger.info(f"Created default UserCostSettings for {settings_created} users.")
            
        # Seed dummy suppliers for marketplace
        supplier_count = db.query(Supplier).count()
        if supplier_count == 0:
            dummy_suppliers = [
                Supplier(name="FastTurn CNC", rating=4.8, location="San Jose, CA", specialty="Rapid Prototyping", is_dummy=True),
                Supplier(name="Precision Machining Co", rating=4.5, location="Detroit, MI", specialty="High Volume Milling", is_dummy=True),
                Supplier(name="Global Fab Solutions", rating=4.2, location="Shenzhen, China", specialty="Low Cost Assembly", is_dummy=True),
            ]
            for s in dummy_suppliers:
                db.add(s)
            db.commit()
            logger.info("Seeded 3 dummy suppliers for the marketplace.")
            
    except Exception as e:
        logger.error(f"Error during startup migration: {e}")
    finally:
        db.close()

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cost-estimation-system"}

# Include routers
app.include_router(estimation.router, prefix="/api/estimation", tags=["estimation"])
app.include_router(parameters.router, prefix="/api/parameters", tags=["parameters"])
app.include_router(marketplace.router, prefix="/api/marketplace", tags=["marketplace"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
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
