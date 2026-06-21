"""
Initialize database with default cost parameters
"""
from backend.database import SessionLocal, init_db
from backend.models import CostParameter
from data.sample_data import SAMPLE_COST_PARAMETERS

def init_default_parameters():
    """Initialize database with default cost parameters"""
    init_db()
    
    db = SessionLocal()
    
    try:
        # Check if parameters already exist
        existing_count = db.query(CostParameter).count()
        
        if existing_count == 0:
            print("Initializing default cost parameters...")
            
            for param in SAMPLE_COST_PARAMETERS:
                cost_param = CostParameter(
                    parameter_name=param["parameter_name"],
                    parameter_value=param["parameter_value"],
                    description=param["description"],
                    is_editable=param["is_editable"]
                )
                db.add(cost_param)
            
            db.commit()
            print(f"✓ Initialized {len(SAMPLE_COST_PARAMETERS)} cost parameters")
        else:
            print("Cost parameters already initialized")
    
    finally:
        db.close()

if __name__ == "__main__":
    init_default_parameters()
