from backend.services.xgboost_predictor import XGBoostPredictor

predictor = XGBoostPredictor(model_dir="backend/trained_models")
res = predictor.predict(
    dimensions={"length": 2000, "width": 400, "height": 300}, # approx 240,000 cm3 -> ~1800kg
    material_type="steel",
    tolerances={"general": 0.1},
    surface_finish="machined",
    operations=["turning", "milling", "drilling", "boring"],
    diagram_analysis={"complexity_score": 50, "hole_count": 5}
)
print(f"Predicted Cost: INR {res.predicted_cost}")
