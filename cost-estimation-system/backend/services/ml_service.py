"""
Machine Learning service for parameter extraction, operation identification,
and cost prediction.

Integrates:
1. Enhanced OCR extraction (from PDFProcessor)
2. OpenCV diagram analysis (from DiagramDetector)
3. XGBoost cost prediction (from XGBoostPredictor)
"""
import logging
from typing import Dict, List, Any, Optional
import re
from models import ExtractedParameters, DimensionData
from services.diagram_detector import DiagramDetector, DiagramAnalysis
from services.xgboost_predictor import XGBoostPredictor, PredictionResult

logger = logging.getLogger(__name__)


class MLService:
    """
    ML service for intelligent parameter extraction, diagram analysis,
    and cost prediction.

    Pipeline:
    1. Extract parameters from OCR text (dimensions, material, tolerances)
    2. Analyze diagram images with OpenCV (holes, slots, complexity)
    3. Predict cost with XGBoost (combined OCR + OpenCV features)
    """

    def __init__(self):
        self.logger = logger
        self.diagram_detector = DiagramDetector()
        self.xgboost_predictor = XGBoostPredictor()

    def extract_parameters(self, extracted_data: Dict[str, Any]) -> ExtractedParameters:
        """
        Extract manufacturing parameters from PDF content using ML/pattern matching.

        Args:
            extracted_data: Dictionary containing extracted text and images

        Returns:
            ExtractedParameters object
        """
        try:
            text_content = extracted_data.get("text_content", "")
            ocr_result = extracted_data.get("ocr_result", {})

            # Extract dimensions
            dimensions = self._extract_dimensions(extracted_data.get("dimensions", []))

            # Extract material type (check OCR result first, then text)
            material_type = self._extract_material_type(text_content, ocr_result)

            # Extract surface finish
            surface_finish = self._extract_surface_finish(text_content, ocr_result)

            # Extract tolerances
            tolerances = self._extract_tolerances(text_content, ocr_result)

            # Extract geometric features (from text + OCR)
            geometric_features = self._extract_geometric_features(text_content)

            # Estimate weight
            estimated_weight = self._estimate_weight(dimensions, material_type)

            # Override weight if OCR found it in title block
            if ocr_result.get("weight_info"):
                try:
                    import re as _re
                    w_match = _re.search(r'(\d+\.?\d*)', ocr_result["weight_info"])
                    if w_match:
                        estimated_weight = float(w_match.group(1))
                except Exception:
                    pass

            parameters = ExtractedParameters(
                dimensions=dimensions,
                material_type=material_type,
                surface_finish=surface_finish,
                tolerances=tolerances,
                geometric_features=geometric_features,
                estimated_weight=estimated_weight,
                diagram_count=extracted_data.get("diagram_count", 0),
                diagram_area_ratio=extracted_data.get("diagram_area_ratio", 0.0),
                line_density=extracted_data.get("line_density", 0.0),
                diagram_images=extracted_data.get("diagram_images", [])
            )

            self.logger.info("Successfully extracted parameters from PDF")
            return parameters

        except Exception as e:
            self.logger.error(f"Error extracting parameters: {str(e)}")
            raise Exception(f"Parameter extraction error: {str(e)}")

    def analyze_diagram(self, extracted_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Run OpenCV diagram analysis on extracted images.

        Args:
            extracted_data: Dict from PDFProcessor containing 'pil_images'

        Returns:
            DiagramAnalysis dict or None if no images available
        """
        try:
            pil_images = extracted_data.get("pil_images", [])

            if not pil_images:
                self.logger.info("No images available for diagram analysis")
                return None

            # Analyze the first page (primary drawing)
            primary_image = pil_images[0]
            analysis = self.diagram_detector.analyze_image(primary_image)

            # If multiple pages, merge feature counts
            if len(pil_images) > 1:
                for img in pil_images[1:]:
                    additional = self.diagram_detector.analyze_image(img)
                    analysis.hole_count += additional.hole_count
                    analysis.slot_count += additional.slot_count
                    analysis.pocket_count += additional.pocket_count
                    analysis.fillet_count += additional.fillet_count
                    analysis.chamfer_count += additional.chamfer_count
                    # Keep the max complexity
                    analysis.complexity_score = max(
                        analysis.complexity_score, additional.complexity_score
                    )

            result = analysis.to_dict()
            self.logger.info(
                f"Diagram analysis complete: "
                f"{analysis.hole_count} holes, "
                f"{analysis.slot_count} slots, "
                f"complexity={analysis.complexity_score:.1f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error in diagram analysis: {str(e)}")
            return None

    def predict_cost(
        self,
        dimensions: Dict[str, Any],
        material_type: str,
        tolerances: Dict[str, float],
        surface_finish: str,
        operations: List[str],
        diagram_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict manufacturing cost using XGBoost model.

        Args:
            dimensions: Extracted dimensions dict
            material_type: Material type string
            tolerances: Tolerance specifications
            surface_finish: Surface finish type
            operations: Manufacturing operations list
            diagram_analysis: OpenCV analysis results

        Returns:
            Dict with predicted_cost, confidence interval, and feature importance
        """
        try:
            result = self.xgboost_predictor.predict(
                dimensions=dimensions,
                material_type=material_type,
                tolerances=tolerances,
                surface_finish=surface_finish,
                operations=operations,
                diagram_analysis=diagram_analysis
            )

            self.logger.info(
                f"ML prediction: ${result.predicted_cost:.2f} "
                f"({result.model_used})"
            )

            return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error in cost prediction: {str(e)}")
            return {
                "predicted_cost": 0.0,
                "confidence_lower": 0.0,
                "confidence_upper": 0.0,
                "feature_importance": {},
                "model_used": "error",
                "prediction_details": {"error": str(e)}
            }

    def identify_operations(
        self,
        dimensions: Dict[str, Any],
        material_type: str,
        geometric_features: List[str],
        diagram_analysis: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Identify required manufacturing operations based on part characteristics.

        Enhanced with OpenCV diagram analysis for more accurate detection.

        Args:
            dimensions: Part dimensions
            material_type: Material type string
            geometric_features: Text-extracted geometric features
            diagram_analysis: OpenCV analysis results (optional)

        Returns:
            List of identified manufacturing operations
        """
        try:
            operations = []

            # Normalize inputs
            if not dimensions:
                dimensions = {}
            if not geometric_features:
                geometric_features = []

            material_lower = str(material_type).lower() if material_type else "steel"

            # ── Text-based detection ──

            # Basic turning for cylindrical parts
            if isinstance(dimensions, dict) and ("diameter" in dimensions or "radius" in dimensions):
                operations.append("turning")

            # Milling for rectangular features
            if isinstance(dimensions, dict) and ("length" in dimensions and "width" in dimensions):
                operations.append("milling")

            # Feature-based operations
            if isinstance(geometric_features, list):
                for feat in geometric_features:
                    if not isinstance(feat, str):
                        continue
                    feat_lower = feat.lower()
                    if "hole" in feat_lower and "drilling" not in operations:
                        operations.append("drilling")
                    if "thread" in feat_lower and "threading" not in operations:
                        operations.append("threading")
                    if ("smooth" in feat_lower or "finish" in feat_lower) and "grinding" not in operations:
                        operations.append("grinding")
                    if "bore" in feat_lower and "boring" not in operations:
                        operations.append("boring")

            # ── OpenCV-enhanced detection ──
            if diagram_analysis:
                # Holes detected → drilling
                if diagram_analysis.get("hole_count", 0) > 0 and "drilling" not in operations:
                    operations.append("drilling")

                # Slots detected → milling
                if diagram_analysis.get("slot_count", 0) > 0 and "milling" not in operations:
                    operations.append("milling")

                # Pockets detected → milling
                if diagram_analysis.get("pocket_count", 0) > 0 and "milling" not in operations:
                    operations.append("milling")

                # Fillets detected → grinding or finishing
                if diagram_analysis.get("fillet_count", 0) > 0 and "grinding" not in operations:
                    operations.append("grinding")

                # Chamfers detected → chamfering
                if diagram_analysis.get("chamfer_count", 0) > 0 and "chamfering" not in operations:
                    operations.append("chamfering")

                # High complexity → add deburring
                if diagram_analysis.get("complexity_score", 0) > 30 and "deburring" not in operations:
                    operations.append("deburring")

            # ── Material-specific defaults ──
            if "steel" in material_lower or "shaft" in material_lower:
                if "turning" not in operations:
                    operations.append("turning")

            if "aluminum" in material_lower:
                if "milling" not in operations:
                    operations.append("milling")

            # Default operations if none detected
            if not operations:
                if "steel" in material_lower or "shaft" in material_lower:
                    operations = ["turning", "grinding", "deburring"]
                elif "aluminum" in material_lower:
                    operations = ["milling", "drilling", "deburring"]
                else:
                    operations = ["turning", "milling", "drilling"]

            return list(set(operations))

        except Exception as e:
            self.logger.exception(f"Error in identify_operations: {str(e)}")
            return ["turning", "milling"]  # Safe fallback

    # ─── Private Extraction Methods ─────────────────────────────────

    def _extract_dimensions(self, dimension_list: List[Dict]) -> DimensionData:
        """Extract and organize dimension data."""
        dimensions_dict = {
            "length": None, "width": None, "height": None,
            "diameter": None, "radius": None, "thickness": None,
            "unit": "mm"
        }

        if dimension_list:
            # Separate dimensions by type if available
            typed_dims = {"linear": [], "diameter": [], "radius": [], "toleranced": []}

            for dim in dimension_list:
                dim_type = dim.get("type", "linear") if dim else "linear"
                value = dim.get("value", 0) if dim else 0
                if value and value > 0:
                    typed_dims.setdefault(dim_type, []).append(dim)

            # Assign diameter and radius from typed dims
            if typed_dims.get("diameter"):
                dimensions_dict["diameter"] = typed_dims["diameter"][0].get("value")
            if typed_dims.get("radius"):
                dimensions_dict["radius"] = typed_dims["radius"][0].get("value")

            # Assign linear dimensions (sorted by value: largest → length)
            linear_dims = sorted(
                typed_dims.get("linear", []) + typed_dims.get("toleranced", []),
                key=lambda d: d.get("value", 0),
                reverse=True
            )

            if len(linear_dims) >= 1 and linear_dims[0].get("value", 0) > 0:
                dimensions_dict["length"] = linear_dims[0]["value"]
            if len(linear_dims) >= 2 and linear_dims[1].get("value", 0) > 0:
                dimensions_dict["width"] = linear_dims[1]["value"]
            if len(linear_dims) >= 3 and linear_dims[2].get("value", 0) > 0:
                dimensions_dict["height"] = linear_dims[2]["value"]

            # Get unit from first dimension
            if dimension_list and dimension_list[0]:
                dimensions_dict["unit"] = dimension_list[0].get("unit", "mm")

        # Apply defaults for missing dimensions
        if not dimensions_dict["length"]:
            dimensions_dict["length"] = 50
        if not dimensions_dict["width"]:
            dimensions_dict["width"] = 30
        if not dimensions_dict["height"]:
            dimensions_dict["height"] = 20
        if not dimensions_dict["diameter"]:
            dimensions_dict["diameter"] = 25

        return DimensionData(**dimensions_dict)

    def _extract_material_type(
        self, text: str, ocr_result: Optional[Dict] = None
    ) -> str:
        """
        Extract material type from text and OCR results.

        Priority: OCR title block material > text keyword matching
        """
        # Check OCR result for material info first
        if ocr_result and ocr_result.get("material_info"):
            mat_info = ocr_result["material_info"].lower()
            # Map ASTM/standard specs to material types
            if any(kw in mat_info for kw in ["a927", "t410", "410", "stainless"]):
                return "stainless steel"
            if any(kw in mat_info for kw in ["a36", "1018", "1045", "4140"]):
                return "steel"
            if any(kw in mat_info for kw in ["6061", "7075", "aluminum", "aluminium"]):
                return "aluminum"
            if "titanium" in mat_info or "ti-6al" in mat_info:
                return "titanium"
            if "copper" in mat_info:
                return "copper"
            if "brass" in mat_info:
                return "brass"
            if "cast iron" in mat_info:
                return "cast iron"

        # Fallback: keyword matching on full text
        material_keywords = {
            "steel": ["steel", "ms", "mild steel"],
            "stainless steel": ["stainless", "ss", "inox"],
            "aluminum": ["aluminum", "aluminium", "al"],
            "brass": ["brass"],
            "copper": ["copper"],
            "cast iron": ["cast iron", "ci"],
            "titanium": ["titanium", "ti"],
        }

        text_lower = text.lower() if text else ""
        for material, keywords in material_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return material

        return "steel"

    def _extract_surface_finish(
        self, text: str, ocr_result: Optional[Dict] = None
    ) -> str:
        """Extract surface finish specifications."""
        # Check OCR surface finish specs
        if ocr_result and ocr_result.get("surface_finish_specs"):
            specs = ocr_result["surface_finish_specs"]
            # Parse Ra values to determine finish quality
            for spec in specs:
                try:
                    ra_match = re.search(r'Ra\s*(\d+\.?\d*)', spec, re.IGNORECASE)
                    if ra_match:
                        ra_value = float(ra_match.group(1))
                        if ra_value <= 0.8:
                            return "polished"
                        elif ra_value <= 1.6:
                            return "ground"
                        elif ra_value <= 3.2:
                            return "machined"
                        else:
                            return "as cast"
                except Exception:
                    pass

        # Fallback: text keyword matching
        finish_keywords = {
            "polished": ["polished", "mirror finish"],
            "ground": ["ground", "grinding"],
            "machined": ["machined", "machine finish"],
            "as cast": ["as cast", "rough"],
            "brushed": ["brushed"],
            "anodized": ["anodized"],
        }

        text_lower = text.lower() if text else ""
        for finish, keywords in finish_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return finish

        return "machined"

    def _extract_tolerances(
        self, text: str, ocr_result: Optional[Dict] = None
    ) -> Dict[str, float]:
        """Extract tolerance specifications."""
        tolerances = {}

        # Check OCR tolerance specs first
        if ocr_result and ocr_result.get("tolerances"):
            for idx, tol in enumerate(ocr_result["tolerances"][:3]):
                tol_type = ["general", "critical", "surface"][idx]
                if "value" in tol:
                    tolerances[tol_type] = tol["value"]
                elif "upper" in tol:
                    tolerances[tol_type] = tol["upper"]

        # Fallback: regex from text
        if not tolerances and text:
            tolerance_pattern = r'[±]\s*(\d+\.?\d*)'
            matches = re.findall(tolerance_pattern, text)
            for idx, match in enumerate(matches[:3]):
                tol_type = ["general", "critical", "surface"][idx]
                tolerances[tol_type] = float(match)

        # Default tolerances
        if not tolerances:
            tolerances = {
                "general": 0.1,
                "critical": 0.05,
                "surface": 0.01
            }

        return tolerances

    def _extract_geometric_features(self, text: str) -> List[str]:
        """Extract geometric features from text."""
        features = []
        feature_keywords = {
            "holes": ["hole", "holes", "drilling", "thru"],
            "threads": ["thread", "threads", "threading", "m10", "m12"],
            "slots": ["slot", "slots"],
            "edges": ["edge", "edges", "chamfer"],
            "curves": ["curve", "curved", "radius", "fillet"],
            "pockets": ["pocket", "pockets"],
            "boss": ["boss", "bosses"],
            "surfaces": ["surface", "surfaces", "finish"],
        }

        text_lower = text.lower() if text else ""
        for feature, keywords in feature_keywords.items():
            for keyword in keywords:
                if keyword in text_lower and feature not in features:
                    features.append(feature)

        return features if features else ["standard_geometry"]

    def _estimate_weight(self, dimensions: DimensionData, material_type: str) -> float:
        """Estimate part weight based on dimensions and material."""
        densities = {
            "steel": 7.85, "stainless steel": 7.75,
            "aluminum": 2.7, "brass": 8.5, "copper": 8.96,
            "cast iron": 7.3, "titanium": 4.51,
        }

        density = densities.get(material_type.lower(), 7.85)

        length = dimensions.length or 1
        width = dimensions.width or 1
        height = dimensions.height or 1

        volume_cm3 = length * width * height
        estimated_weight = volume_cm3 * density / 1000

        return round(estimated_weight, 2)
