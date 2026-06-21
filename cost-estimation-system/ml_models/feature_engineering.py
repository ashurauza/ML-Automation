"""
Feature engineering for ML models.

Builds a comprehensive feature vector from:
- OCR-extracted dimensions and parameters
- OpenCV-detected diagram features (holes, slots, complexity)
- Material properties (density, machinability, cost)
- Manufacturing parameters (operations, tolerances, surface finish)
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Dict, List, Any, Optional, Tuple


# ─── Material Properties Lookup ─────────────────────────────────

MATERIAL_ENCODING = {
    "steel": 1,
    "stainless_steel": 2,
    "stainless steel": 2,
    "aluminum": 3,
    "brass": 4,
    "copper": 5,
    "cast_iron": 6,
    "cast iron": 6,
    "titanium": 7,
}

MATERIAL_DENSITY = {
    "steel": 7.85, "stainless_steel": 7.75, "stainless steel": 7.75,
    "aluminum": 2.70, "brass": 8.50, "copper": 8.96,
    "cast_iron": 7.30, "cast iron": 7.30, "titanium": 4.51,
}

MATERIAL_MACHINABILITY = {
    "steel": 0.60, "stainless_steel": 0.40, "stainless steel": 0.40,
    "aluminum": 0.90, "brass": 0.85, "copper": 0.70,
    "cast_iron": 0.65, "cast iron": 0.65, "titanium": 0.25,
}

MATERIAL_COST_PER_KG = {
    "steel": 0.80, "stainless_steel": 2.00, "stainless steel": 2.00,
    "aluminum": 2.50, "brass": 3.00, "copper": 4.50,
    "cast_iron": 0.60, "cast iron": 0.60, "titanium": 15.00,
}

OPERATION_ENCODING = {
    "turning": 1, "milling": 2, "drilling": 3,
    "grinding": 4, "boring": 5, "threading": 6,
    "honing": 7, "facing": 8, "chamfering": 9,
    "deburring": 10,
}

SURFACE_FINISH_ENCODING = {
    "as cast": 1, "rough": 1,
    "machined": 2, "machine finish": 2,
    "ground": 3, "grinding": 3,
    "brushed": 4,
    "polished": 5, "mirror finish": 5,
    "anodized": 6,
}

COATING_ENCODING = {
    "none": 0,
    "anodizing": 1,
    "painting": 2,
    "powder coating": 3,
    "chrome plating": 4,
}

# Feature names for the full 25-feature vector
FEATURE_NAMES = [
    "length", "width", "height", "diameter", "thickness",
    "volume", "surface_area", "aspect_ratio",
    "material_code", "density", "machinability_index", "material_cost_per_kg",
    "num_operations", "tolerance_severity", "surface_finish_code", "coating_code",
    "hole_count", "slot_count", "pocket_count",
    "fillet_count", "chamfer_count", "complexity_score",
    "contour_count", "symmetry_score", "num_drawing_views",
]


def extract_numerical_features(dimensions: Dict[str, Any]) -> List[float]:
    """
    Extract numerical features from dimension data.

    Returns:
        [length, width, height, diameter, thickness,
         volume, surface_area, aspect_ratio]
    """
    length = _safe_float(dimensions.get("length"), 50.0)
    width = _safe_float(dimensions.get("width"), 30.0)
    height = _safe_float(dimensions.get("height"), 20.0)
    diameter = _safe_float(dimensions.get("diameter"), 0.0)
    thickness = _safe_float(dimensions.get("thickness"), 0.0)

    # Derived features
    volume = length * width * height
    surface_area = 2.0 * (length * width + width * height + length * height)
    aspect_ratio = max(length, width, height) / max(
        min(length, width, height), 0.1
    )

    return [
        length, width, height, diameter, thickness,
        volume, surface_area, aspect_ratio
    ]


def extract_material_features(material_type: str) -> List[float]:
    """
    Extract material-related features.

    Returns:
        [material_code, density, machinability_index, material_cost_per_kg]
    """
    mat_key = material_type.lower().strip() if material_type else "steel"

    material_code = MATERIAL_ENCODING.get(mat_key, 0)
    density = MATERIAL_DENSITY.get(mat_key, 7.85)
    machinability = MATERIAL_MACHINABILITY.get(mat_key, 0.6)
    cost_per_kg = MATERIAL_COST_PER_KG.get(mat_key, 1.5)

    return [material_code, density, machinability, cost_per_kg]


def extract_manufacturing_features(
    operations: List[str],
    tolerances: Dict[str, float],
    surface_finish: str
) -> List[float]:
    """
    Extract manufacturing-related features.

    Returns:
        [num_operations, tolerance_severity, surface_finish_code]
    """
    num_operations = len(operations) if operations else 1

    # Tolerance severity: lower tolerance → higher severity → higher cost
    tol_values = []
    if tolerances:
        for v in tolerances.values():
            try:
                val = float(v)
                if val > 0:
                    tol_values.append(val)
            except (ValueError, TypeError):
                pass

    if tol_values:
        min_tol = min(tol_values)
        tolerance_severity = min(1.0 / max(min_tol, 0.001), 100.0)
    else:
        tolerance_severity = 10.0

    sf_key = surface_finish.lower().strip() if surface_finish else "machined"
    surface_finish_code = SURFACE_FINISH_ENCODING.get(sf_key, 2)

    return [num_operations, tolerance_severity, surface_finish_code]


def extract_coating_features(coating_type: str) -> List[float]:
    """
    Extract coating-related features.

    Returns:
        [coating_code]
    """
    coat_key = coating_type.lower().strip() if coating_type else "none"
    coating_code = COATING_ENCODING.get(coat_key, 0)
    
    return [coating_code]


def extract_opencv_features(
    diagram_analysis: Optional[Dict[str, Any]] = None
) -> List[float]:
    """
    Extract OpenCV-derived features from diagram analysis.

    Returns:
        [hole_count, slot_count, pocket_count,
         fillet_count, chamfer_count, complexity_score,
         contour_count, symmetry_score, num_drawing_views]
    """
    if not diagram_analysis:
        return [0, 0, 0, 0, 0, 0.0, 0, 0.5, 1]

    return [
        diagram_analysis.get("hole_count", 0),
        diagram_analysis.get("slot_count", 0),
        diagram_analysis.get("pocket_count", 0),
        diagram_analysis.get("fillet_count", 0),
        diagram_analysis.get("chamfer_count", 0),
        diagram_analysis.get("complexity_score", 0.0),
        diagram_analysis.get("contour_count", 0),
        diagram_analysis.get("symmetry_score", 0.5),
        diagram_analysis.get("num_drawing_views", 1),
    ]


def create_feature_vector(
    dimensions: Dict[str, Any],
    material_type: str,
    operations: List[str],
    tolerances: Dict[str, float],
    surface_finish: str = "machined",
    coating_type: str = "none",
    diagram_analysis: Optional[Dict[str, Any]] = None,
) -> np.ndarray:
    """
    Create complete feature vector for XGBoost model input.

    Combines all feature groups into a single 25-element vector.

    Args:
        dimensions: Dict with length, width, height, diameter, etc.
        material_type: Material name string
        operations: List of manufacturing operations
        tolerances: Tolerance specifications dict
        surface_finish: Surface finish description
        coating_type: Coating / Plating type description
        diagram_analysis: Dict from DiagramAnalysis.to_dict()

    Returns:
        numpy array of shape (1, 25)
    """
    numerical = extract_numerical_features(dimensions)
    material = extract_material_features(material_type)
    manufacturing = extract_manufacturing_features(
        operations, tolerances, surface_finish
    )
    coating = extract_coating_features(coating_type)
    opencv = extract_opencv_features(diagram_analysis)

    features = numerical + material + manufacturing + coating + opencv
    return np.array([features])


def create_feature_dataframe(
    feature_vector: np.ndarray
) -> pd.DataFrame:
    """
    Convert a feature vector to a named DataFrame.

    Useful for XGBoost which benefits from named features.
    """
    return pd.DataFrame(feature_vector, columns=FEATURE_NAMES)


# ─── Legacy API (backward compatibility) ────────────────────────

def extract_categorical_features(
    material_type: str, operations: List[str]
) -> List[float]:
    """Legacy: extract categorical features."""
    material_code = MATERIAL_ENCODING.get(material_type.lower(), 0)
    operation_codes = [
        OPERATION_ENCODING.get(op.lower(), 0) for op in operations
    ]
    return [material_code] + operation_codes


def normalize_features(features: List[float]) -> np.ndarray:
    """Legacy: normalize feature values."""
    scaler = StandardScaler()
    return scaler.fit_transform(np.array(features).reshape(1, -1))


# ─── Utilities ──────────────────────────────────────────────────

def _safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float."""
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
