import pandas as pd
import numpy as np
import os
import sys

# Add backend to path so we can import services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from services.xgboost_predictor import XGBoostPredictor

def evaluate_accuracy():
    print("Loading dataset...")
    data_path = os.path.join(os.path.dirname(__file__), "ml_models", "training_data", "synthetic_drawings_dataset.csv")
    df = pd.read_csv(data_path)
    
    model_dir = os.path.join(os.path.dirname(__file__), "ml_models", "trained_models")
    predictor = XGBoostPredictor(model_dir=model_dir)
    
    material_map = {1: "steel", 2: "stainless steel", 3: "aluminum", 4: "brass", 5: "copper", 6: "cast iron", 7: "titanium"}
    coating_map = {0: "none", 1: "anodizing", 2: "painting", 3: "powder coating", 4: "chrome plating"}
    
    print(f"Evaluating Model Accuracy on all {len(df)} rows...")
    
    errors = []
    
    for idx, row in df.iterrows():
        # Build dimensions dict
        dimensions = {
            "length": row["length"],
            "width": row["width"],
            "height": row["height"],
            "diameter": row["diameter"],
            "thickness": row["thickness"]
        }
        
        mat_type = material_map.get(int(row["material_code"]), "steel")
        coat_type = coating_map.get(int(row["coating_code"]), "none")
        ops = ["milling"] * int(row["num_operations"])
        
        diagram_analysis = {
            "hole_count": row["hole_count"],
            "slot_count": row["slot_count"],
            "pocket_count": row["pocket_count"],
            "fillet_count": row["fillet_count"],
            "chamfer_count": row["chamfer_count"],
            "complexity_score": row["complexity_score"],
            "contour_count": row["contour_count"],
            "symmetry_score": row["symmetry_score"],
            "num_drawing_views": row["num_drawing_views"]
        }
        
        tolerances = {"val": 1.0 / row["tolerance_severity"] if row["tolerance_severity"] > 0 else 0.1}
        actual_cost = row["total_cost"]
        
        result = predictor.predict(
            dimensions=dimensions,
            material_type=mat_type,
            tolerances=tolerances,
            surface_finish="machined",
            operations=ops,
            coating=coat_type,
            diagram_analysis=diagram_analysis
        )
        
        predicted_cost = result.predicted_cost
        diff = predicted_cost - actual_cost
        error_pct = abs(diff) / actual_cost * 100
        errors.append(error_pct)
        
    print(f"\n--- Evaluation Results ---")
    print(f"Overall Model Accuracy: {100 - np.mean(errors):.2f}%")
    print(f"Average Absolute Error: {np.mean(errors):.2f}%")
    print(f"Median Absolute Error:  {np.median(errors):.2f}%")
    print(f"Max Absolute Error:     {np.max(errors):.2f}%")
    print(f"Min Absolute Error:     {np.min(errors):.2f}%")

if __name__ == "__main__":
    evaluate_accuracy()
