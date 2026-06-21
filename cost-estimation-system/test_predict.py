import sys
import os
import json

# Add backend to path so we can import services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.xgboost_predictor import XGBoostPredictor

def run_test():
    # Initialize the predictor
    # It expects models in backend/trained_models or similar
    # The default DEFAULT_MODEL_DIR is trained_models one level up from services
    # Let's specify the path to ml_models/trained_models to be sure
    model_dir = os.path.join(os.path.dirname(__file__), "ml_models", "trained_models")
    predictor = XGBoostPredictor(model_dir=model_dir)
    
    # Dummy parameters for prediction
    dimensions = {
        "length": 150.0,
        "width": 100.0,
        "height": 20.0,
        "diameter": 0.0,
        "thickness": 0.0
    }
    material_type = "aluminum"
    tolerances = {"length_tol": 0.05, "width_tol": 0.05}
    surface_finish = "machined"
    coating = "anodizing"
    operations = ["milling", "drilling", "chamfering"]
    diagram_analysis = {
        "hole_count": 4,
        "slot_count": 0,
        "pocket_count": 1,
        "fillet_count": 8,
        "chamfer_count": 4,
        "complexity_score": 45.0,
        "contour_count": 25,
        "symmetry_score": 1.0,
        "num_drawing_views": 3
    }

    print("Running Prediction with XGBoostPredictor...")
    result = predictor.predict(
        dimensions=dimensions,
        material_type=material_type,
        tolerances=tolerances,
        surface_finish=surface_finish,
        operations=operations,
        coating=coating,
        diagram_analysis=diagram_analysis
    )
    
    print("\n" + "="*50)
    print(" 🛠️  AI COST ESTIMATION RESULT (INR)")
    print("="*50)
    print(f"💰 Predicted Total Cost:  ₹ {result.predicted_cost:,.2f}")
    print(f"📊 Confidence Range:      ₹ {result.confidence_lower:,.2f}  to  ₹ {result.confidence_upper:,.2f}")
    print("\n⚙️  Prediction Details:")
    print(f"   Model Engine:          {result.model_used.upper()}")
    print(f"   Features Analyzed:     {result.prediction_details['num_features']}")
    
    print("\n📈 Top 5 Driving Factors:")
    # Sort feature importance dictionary by value
    sorted_features = sorted(result.feature_importance.items(), key=lambda item: item[1], reverse=True)
    for feat, imp in sorted_features[:5]:
        print(f"   - {feat.replace('_', ' ').title().ljust(22)} : {imp*100:0.1f}%")
        
    print("="*50 + "\n")

if __name__ == "__main__":
    run_test()
