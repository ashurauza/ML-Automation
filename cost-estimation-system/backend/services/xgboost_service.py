"""
XGBoost service for predicting manufacturing costs from OCR and OpenCV features
"""
import xgboost as xgb
import numpy as np
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class XGBoostService:
    """Load trained XGBoost models and perform inference for cost breakdown prediction"""
    
    def __init__(self, models_dir: str = "../ml_models/trained_models"):
        self.logger = logger
        self.models_dir = models_dir
        self.models: Dict[str, xgb.XGBRegressor] = {}
        self.cost_components = [
            "total_cost", 
            "raw_material_cost", 
            "machining_cost", 
            "manpower_cost", 
            "overhead_cost", 
            "logistics_cost",
            "profit_margin"
        ]
        self._load_models()
        
    def _load_models(self):
        """Load XGBoost models for each cost component"""
        # Resolve models directory
        resolved_dir = self.models_dir
        if not os.path.exists(resolved_dir):
            # Try relative path from the backend application directory
            alternative_dir = os.path.join(os.getcwd(), "ml_models", "trained_models")
            if os.path.exists(alternative_dir):
                resolved_dir = alternative_dir
            else:
                alternative_dir_parent = os.path.join(os.getcwd(), "..", "ml_models", "trained_models")
                if os.path.exists(alternative_dir_parent):
                    resolved_dir = alternative_dir_parent
                    
        self.logger.info(f"Looking for XGBoost models in: {resolved_dir}")
        
        for component in self.cost_components:
            model_filename = f"cost_prediction_xgb_{component}.json"
            model_path = os.path.join(resolved_dir, model_filename)
            
            if os.path.exists(model_path):
                try:
                    model = xgb.XGBRegressor()
                    model.load_model(model_path)
                    self.models[component] = model
                    self.logger.info(f"✓ Loaded XGBoost model for {component}")
                except Exception as e:
                    self.logger.error(f"Error loading XGBoost model {model_filename}: {str(e)}")
            else:
                self.logger.warning(f"XGBoost model file not found for {component} at {model_path}")

    def is_model_available(self) -> bool:
        """Check if at least the total cost model is loaded"""
        return "total_cost" in self.models

    def predict_costs(self, features: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Predict all cost components using loaded XGBoost models.
        
        Args:
            features: Dictionary containing parameters:
                - length
                - width
                - height
                - material_code
                - num_operations
                - estimated_weight
                - diagram_count (OpenCV)
                - diagram_area_ratio (OpenCV)
                - line_density (OpenCV)
                
        Returns:
            Dictionary with predicted cost components, or None if prediction fails/models are missing.
        """
        try:
            # Check model availability, reload if needed
            if not self.is_model_available():
                self._load_models()
                if not self.is_model_available():
                    self.logger.warning("XGBoost models are not available for prediction.")
                    return None
                    
            # Ordered features matching training script
            feature_names = [
                "length",
                "width",
                "height",
                "material_code",
                "num_operations",
                "estimated_weight",
                "diagram_count",
                "diagram_area_ratio",
                "line_density"
            ]
            
            # Extract inputs and convert to float
            x_input = []
            for name in feature_names:
                val = features.get(name, 0.0)
                # Safeguard: replace None/NaN with 0.0
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    val = 0.0
                x_input.append(float(val))
                
            input_array = np.array([x_input], dtype=np.float32)
            
            predictions = {}
            for component in self.cost_components:
                if component in self.models:
                    pred_val = self.models[component].predict(input_array)[0]
                    # Ensure cost is not negative
                    predictions[component] = max(0.0, round(float(pred_val), 2))
                else:
                    # If some sub-component model is missing, we will fallback
                    logger.warning(f"Model for {component} is missing. Skipping ML estimation.")
                    return None
                    
            # Set subtotal
            predictions["subtotal"] = round(
                predictions["raw_material_cost"] + 
                predictions["machining_cost"] + 
                predictions["manpower_cost"] + 
                predictions["overhead_cost"] + 
                predictions["logistics_cost"],
                2
            )
            
            # Perform a sanity check: total_cost should be close to subtotal + profit_margin
            computed_total = predictions["subtotal"] + predictions["profit_margin"]
            if abs(predictions["total_cost"] - computed_total) > 2.0: # allow minor rounding discrepancy
                # Align total cost with parts sum for consistency
                predictions["total_cost"] = round(computed_total, 2)
                
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error during XGBoost cost prediction: {str(e)}")
            return None
