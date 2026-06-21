"""
XGBoost-based cost prediction service.

Loads a trained XGBoost model and predicts manufacturing costs
from a combined feature vector (OCR-extracted parameters + OpenCV features).
Falls back to formula-based calculation if the model is unavailable.
"""
import os
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Try to import xgboost — graceful fallback if missing
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("xgboost not installed — ML predictions will use fallback formula")

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


@dataclass
class PredictionResult:
    """Result from XGBoost cost prediction."""
    predicted_cost: float
    confidence_lower: float  # 10th percentile
    confidence_upper: float  # 90th percentile
    feature_importance: Dict[str, float]
    model_used: str  # "xgboost" or "formula_fallback"
    prediction_details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Feature names expected by the model (must match training order)
FEATURE_NAMES = [
    # Dimensional features (from OCR)
    "length",
    "width",
    "height",
    "diameter",
    "thickness",
    "volume",
    "surface_area",
    "aspect_ratio",
    # Material features
    "material_code",
    "density",
    "machinability_index",
    "material_cost_per_kg",
    # Manufacturing features
    "num_operations",
    "tolerance_severity",
    "surface_finish_code",
    "coating_code",
    # OpenCV features
    "hole_count",
    "slot_count",
    "pocket_count",
    "fillet_count",
    "chamfer_count",
    "complexity_score",
    "contour_count",
    "symmetry_score",
    "num_drawing_views",
]

# Material property lookup tables
MATERIAL_PROPERTIES = {
    "steel": {"code": 1, "density": 7.85, "machinability": 0.6, "cost_per_kg": 0.80},
    "stainless steel": {"code": 2, "density": 7.75, "machinability": 0.4, "cost_per_kg": 2.00},
    "stainless_steel": {"code": 2, "density": 7.75, "machinability": 0.4, "cost_per_kg": 2.00},
    "aluminum": {"code": 3, "density": 2.70, "machinability": 0.9, "cost_per_kg": 2.50},
    "brass": {"code": 4, "density": 8.50, "machinability": 0.85, "cost_per_kg": 3.00},
    "copper": {"code": 5, "density": 8.96, "machinability": 0.7, "cost_per_kg": 4.50},
    "cast_iron": {"code": 6, "density": 7.30, "machinability": 0.65, "cost_per_kg": 0.60},
    "cast iron": {"code": 6, "density": 7.30, "machinability": 0.65, "cost_per_kg": 0.60},
    "titanium": {"code": 7, "density": 4.51, "machinability": 0.25, "cost_per_kg": 15.00},
}

SURFACE_FINISH_CODES = {
    "as cast": 1, "rough": 1,
    "machined": 2, "machine finish": 2,
    "ground": 3, "grinding": 3,
    "brushed": 4,
    "polished": 5, "mirror finish": 5,
    "anodized": 6,
}

COATING_CODES = {
    "none": 0,
    "anodizing": 1,
    "painting": 2,
    "powder coating": 3,
    "chrome plating": 4,
}

# Default model path
DEFAULT_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "trained_models"
)


class XGBoostPredictor:
    """
    Production inference service for cost prediction.

    Loads a trained XGBoost model and scaler, builds feature vectors
    from OCR + OpenCV data, and returns predictions with confidence intervals.
    """

    def __init__(self, model_dir: Optional[str] = None):
        self.logger = logger
        self.model_dir = model_dir or DEFAULT_MODEL_DIR
        self.model = None
        self.scaler = None
        self.model_loaded = False
        self._load_model()

    def _load_model(self) -> None:
        """Load the trained XGBoost model and scaler from disk."""
        if not HAS_XGBOOST:
            self.logger.warning("XGBoost not available, using fallback")
            return

        model_path = os.path.join(self.model_dir, "xgboost_cost_model.json")
        scaler_path = os.path.join(self.model_dir, "feature_scaler.joblib")

        try:
            if os.path.exists(model_path):
                self.model = xgb.XGBRegressor()
                self.model.load_model(model_path)
                self.logger.info(f"XGBoost model loaded from {model_path}")

                if HAS_JOBLIB and os.path.exists(scaler_path):
                    self.scaler = joblib.load(scaler_path)
                    self.logger.info(f"Feature scaler loaded from {scaler_path}")

                self.model_loaded = True
            else:
                self.logger.warning(
                    f"Model file not found at {model_path}. "
                    "Run train_models.py first. Using fallback formula."
                )
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            self.model_loaded = False

    def build_feature_vector(
        self,
        dimensions: Dict[str, Any],
        material_type: str,
        tolerances: Dict[str, float],
        surface_finish: str,
        operations: List[str],
        coating: str = "none",
        diagram_analysis: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """
        Build the full feature vector from extracted parameters.

        Args:
            dimensions: Dict with length, width, height, diameter, etc.
            material_type: Material name string
            tolerances: Dict with tolerance values
            surface_finish: Surface finish description
            operations: List of manufacturing operations
            diagram_analysis: Dict from DiagramAnalysis.to_dict()

        Returns:
            numpy array of shape (1, num_features)
        """
        # ── Dimensional features ──
        length = self._safe_float(dimensions.get("length"), 50.0)
        width = self._safe_float(dimensions.get("width"), 30.0)
        height = self._safe_float(dimensions.get("height"), 20.0)
        diameter = self._safe_float(dimensions.get("diameter"), 0.0)
        thickness = self._safe_float(dimensions.get("thickness"), 0.0)

        volume = length * width * height
        surface_area = 2 * (length * width + width * height + length * height)
        aspect_ratio = max(length, width, height) / max(
            min(length, width, height), 0.1
        )

        # ── Material features ──
        mat_key = material_type.lower().strip() if material_type else "steel"
        mat_props = MATERIAL_PROPERTIES.get(mat_key, MATERIAL_PROPERTIES["steel"])
        material_code = mat_props["code"]
        density = mat_props["density"]
        machinability_index = mat_props["machinability"]
        material_cost_per_kg = mat_props["cost_per_kg"]

        # ── Manufacturing features ──
        num_operations = len(operations) if operations else 1

        # Tolerance severity (lower tolerance → higher severity)
        tol_values = [v for v in tolerances.values() if isinstance(v, (int, float))]
        if tol_values:
            min_tol = min(tol_values)
            tolerance_severity = 1.0 / max(min_tol, 0.001)
            tolerance_severity = min(tolerance_severity, 100.0)
        else:
            tolerance_severity = 10.0  # Default medium

        # Surface finish code
        sf_key = surface_finish.lower().strip() if surface_finish else "machined"
        surface_finish_code = SURFACE_FINISH_CODES.get(sf_key, 2)

        coat_key = coating.lower().strip() if coating else "none"
        coating_code = COATING_CODES.get(coat_key, 0)

        # ── OpenCV features ──
        da = diagram_analysis or {}
        hole_count = da.get("hole_count", 0)
        slot_count = da.get("slot_count", 0)
        pocket_count = da.get("pocket_count", 0)
        fillet_count = da.get("fillet_count", 0)
        chamfer_count = da.get("chamfer_count", 0)
        complexity_score = da.get("complexity_score", 0.0)
        contour_count = da.get("contour_count", 0)
        symmetry_score = da.get("symmetry_score", 0.5)
        num_drawing_views = da.get("num_drawing_views", 1)

        # ── Assemble vector ──
        features = np.array([[
            length, width, height, diameter, thickness,
            volume, surface_area, aspect_ratio,
            material_code, density, machinability_index, material_cost_per_kg,
            num_operations, tolerance_severity, surface_finish_code, coating_code,
            hole_count, slot_count, pocket_count,
            fillet_count, chamfer_count, complexity_score,
            contour_count, symmetry_score, num_drawing_views,
        ]])

        return features

    def predict(
        self,
        dimensions: Dict[str, Any],
        material_type: str,
        tolerances: Dict[str, float],
        surface_finish: str,
        operations: List[str],
        coating: str = "none",
        diagram_analysis: Optional[Dict[str, Any]] = None
    ) -> PredictionResult:
        """
        Predict manufacturing cost from extracted parameters.

        Args:
            dimensions: Extracted dimensions dict
            material_type: Material type string
            tolerances: Tolerance specifications
            surface_finish: Surface finish type
            operations: Manufacturing operations list
            diagram_analysis: OpenCV analysis results dict

        Returns:
            PredictionResult with cost, confidence interval, and importance
        """
        features = self.build_feature_vector(
            dimensions, material_type, tolerances,
            surface_finish, operations, coating, diagram_analysis
        )

        if self.model_loaded and self.model is not None:
            return self._predict_xgboost(features, diagram_analysis or {})
        else:
            return self._predict_fallback(features, material_type, operations)

    def _predict_xgboost(
        self, features: np.ndarray, diagram_analysis: Dict
    ) -> PredictionResult:
        """Run XGBoost prediction with confidence interval."""
        try:
            # Scale features if scaler is available
            if self.scaler is not None:
                features_scaled = self.scaler.transform(features)
            else:
                features_scaled = features

            # Point prediction
            predicted_cost = float(self.model.predict(features_scaled)[0])

            # Confidence interval via heuristic (±15% for now)
            # In production, use quantile regression or bootstrap
            margin = predicted_cost * 0.15
            confidence_lower = max(0, predicted_cost - margin)
            confidence_upper = predicted_cost + margin

            # Feature importance
            importance = {}
            if hasattr(self.model, "feature_importances_"):
                importances = self.model.feature_importances_
                for i, name in enumerate(FEATURE_NAMES):
                    if i < len(importances):
                        importance[name] = round(float(importances[i]), 4)

            return PredictionResult(
                predicted_cost=round(predicted_cost, 2),
                confidence_lower=round(confidence_lower, 2),
                confidence_upper=round(confidence_upper, 2),
                feature_importance=importance,
                model_used="xgboost",
                prediction_details={
                    "features_used": FEATURE_NAMES,
                    "num_features": len(FEATURE_NAMES),
                    "scaler_applied": self.scaler is not None,
                }
            )

        except Exception as e:
            self.logger.error(f"XGBoost prediction failed: {e}, using fallback")
            return self._predict_fallback(
                features, "steel", ["turning", "milling"]
            )

    def _predict_fallback(
        self, features: np.ndarray, material_type: str, operations: List[str]
    ) -> PredictionResult:
        """
        Formula-based fallback when model is unavailable.

        Uses a simplified cost model similar to the existing CostCalculator.
        """
        # Extract key values from feature vector
        f = features[0]
        length, width, height = f[0], f[1], f[2]
        volume = f[5]
        surface_area = f[6]
        material_code = f[8]
        density = f[9]
        machinability = f[10]
        cost_per_kg = f[11]
        num_ops = f[12]
        coating_code = f[15]
        complexity = f[21]

        # Material cost
        weight_kg = (volume / 1e6) * density  # mm³ to cm³ to weight
        material_cost = weight_kg * cost_per_kg * 1.3  # 30% waste

        # Machining & Fabrication cost scales with weight and complexity
        machining_rate = 50.0 / max(machinability, 0.1)
        base_setup_time_hrs = 0.5 + (weight_kg / 200.0)
        operation_time_hrs = num_ops * (0.25 + (weight_kg / 100.0)) * (1.0 + complexity / 100.0)
        cycle_time_hrs = base_setup_time_hrs + operation_time_hrs
        machining_cost = cycle_time_hrs * machining_rate

        # Labor
        labor_cost = cycle_time_hrs * 25.0 * 0.4 * (1.0 + (num_ops * 0.1))
        
        # Coating cost
        coating_rates = {0: 0.0, 1: 0.002, 2: 0.001, 3: 0.0015, 4: 0.005}
        coating_rate = coating_rates.get(coating_code, 0.0)
        coating_cost = surface_area * coating_rate

        # Overhead + logistics + profit
        subtotal = material_cost + machining_cost + labor_cost + coating_cost
        overhead = subtotal * 0.15
        logistics = 50 + volume * 1e-6
        total = (subtotal + overhead + logistics) * 1.2  # 20% profit

        predicted_cost = max(total, 10.0)

        return PredictionResult(
            predicted_cost=round(predicted_cost, 2),
            confidence_lower=round(predicted_cost * 0.7, 2),
            confidence_upper=round(predicted_cost * 1.3, 2),
            feature_importance={},
            model_used="formula_fallback",
            prediction_details={
                "reason": "XGBoost model not loaded, using formula-based estimation",
                "material_cost": round(material_cost, 2),
                "machining_cost": round(machining_cost, 2),
                "labor_cost": round(labor_cost, 2),
                "coating_cost": round(coating_cost, 2),
            }
        )

    @staticmethod
    def _safe_float(value, default: float = 0.0) -> float:
        """Safely convert a value to float."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                v = value.strip().lower()
                for unit in ["mm", "cm", "inches", "in", '"']:
                    v = v.replace(unit, "")
                v = v.replace(",", "")
                return float(v)
            return float(value)
        except (ValueError, TypeError):
            return default
