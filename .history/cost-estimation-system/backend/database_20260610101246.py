"""
Database configuration and initialization
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cost_estimation.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DATABASE_ECHO", "False").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency injection for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _migrate_sqlite_schema():
    """Apply lightweight SQLite schema migrations for missing columns."""
    if "sqlite" not in DATABASE_URL:
        return

    with engine.connect() as conn:
        existing_columns = {row[1] for row in conn.execute("PRAGMA table_info('estimations')")}
        migration_sql = []

        if "diagram_count" not in existing_columns:
            migration_sql.append("ALTER TABLE estimations ADD COLUMN diagram_count INTEGER")
        if "diagram_area_ratio" not in existing_columns:
            migration_sql.append("ALTER TABLE estimations ADD COLUMN diagram_area_ratio FLOAT")
        if "line_density" not in existing_columns:
            migration_sql.append("ALTER TABLE estimations ADD COLUMN line_density FLOAT")
        if "diagram_images" not in existing_columns:
            migration_sql.append("ALTER TABLE estimations ADD COLUMN diagram_images JSON")

        for sql in migration_sql:
            conn.execute(sql)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_schema()
