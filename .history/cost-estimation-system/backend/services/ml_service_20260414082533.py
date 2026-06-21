"""
Machine Learning service for parameter extraction and operation identification
"""
import logging
from typing import Dict, List, Any
import re
from models import ExtractedParameters, DimensionData

logger = logging.getLogger(__name__)


class MLService:
    """ML service for intelligent parameter extraction and analysis"""
    
    def __init__(self):
        self.logger = logger
    
    def extract_parameters(self, extracted_data: Dict[str, Any]) -> ExtractedParameters:
        """
        Extract manufacturing parameters from PDF content using ML/pattern matching
        
        Args:
            extracted_data: Dictionary containing extracted text and images
            
        Returns:
            ExtractedParameters object
        """
        try:
            text_content = extracted_data.get("text_content", "")
            
            # Extract dimensions
            dimensions = self._extract_dimensions(extracted_data.get("dimensions", []))
            
            # Extract material type
            material_type = self._extract_material_type(text_content)
            
            # Extract surface finish
            surface_finish = self._extract_surface_finish(text_content)
            
            # Extract tolerances
            tolerances = self._extract_tolerances(text_content)
            
            # Extract geometric features
            geometric_features = self._extract_geometric_features(text_content)
            
            # Estimate weight
            estimated_weight = self._estimate_weight(dimensions, material_type)
            
            parameters = ExtractedParameters(
                dimensions=dimensions,
                material_type=material_type,
                surface_finish=surface_finish,
                tolerances=tolerances,
                geometric_features=geometric_features,
                estimated_weight=estimated_weight
            )
            
            self.logger.info("Successfully extracted parameters from PDF")
            return parameters
            
        except Exception as e:
            self.logger.error(f"Error extracting parameters: {str(e)}")
            raise Exception(f"Parameter extraction error: {str(e)}")
    
    def identify_operations(
        self,
        dimensions: Dict[str, Any],
        material_type: str,
        geometric_features: List[str]
    ) -> List[str]:
        """
        Identify required manufacturing operations based on part characteristics
        
        Args:
            dimensions: Part dimensions
            material_type: Type of material
            geometric_features: List of geometric features
            
        Returns:
            List of required manufacturing operations
        """
        operations = []
        
        # Normalize dimensions and features
        if not dimensions:
            dimensions = {}
        if not geometric_features:
            geometric_features = []
        
        material_lower = material_type.lower() if material_type else "steel"
        
        # Basic turning for cylindrical parts
        if "diameter" in dimensions or "radius" in dimensions:
            operations.append("turning")
        
        # Milling for rectangular features
        if "length" in dimensions and "width" in dimensions:
            operations.append("milling")
        
        # Drilling for holes (if mentioned in features)
        if any("hole" in f.lower() for f in geometric_features):
            operations.append("drilling")
        
        # Threading if detected
        if any("thread" in f.lower() for f in geometric_features):
            operations.append("threading")
        
        # Grinding for finishing
        if any("smooth" in f.lower() or "finish" in f.lower() for f in geometric_features):
            operations.append("grinding")
        
        # Boring for large holes
        if any("bore" in f.lower() for f in geometric_features):
            operations.append("boring")
        
        # Material-specific operations
        if "steel" in material_lower or "shaft" in material_lower.lower():
            if "turning" not in operations:
                operations.append("turning")
        
        if "aluminum" in material_lower:
            if "milling" not in operations:
                operations.append("milling")
        
        # Default operations if none detected
        if not operations:
            # For steel shaft/parts - use turning and grinding
            if "steel" in material_lower or "shaft" in material_lower.lower():
                operations = ["turning", "grinding", "deburring"]
            # For aluminum - use milling
            elif "aluminum" in material_lower:
                operations = ["milling", "drilling", "deburring"]
            # For general parts - use turning and milling
            else:
                operations = ["turning", "milling", "drilling"]
        
        return list(set(operations))  # Remove duplicates
    
    def _extract_dimensions(self, dimension_list: List[Dict]) -> DimensionData:
        """
        Extract and organize dimension data
        """
        # Initialize with defaults
        dimensions_dict = {
            "length": None,
            "width": None,
            "height": None,
            "diameter": None,
            "radius": None,
            "thickness": None,
            "unit": "mm"
        }
        
        # Process extracted dimensions
        for idx, dim in enumerate(dimension_list[:6]):  # Limit to 6 dimensions
            value = dim.get("value", 0)
            unit = dim.get("unit", "mm")
            
            # Assign to appropriate field based on order
            if idx == 0 and value > 0:
                dimensions_dict["length"] = value
            elif idx == 1 and value > 0:
                dimensions_dict["width"] = value
            elif idx == 2 and value > 0:
                dimensions_dict["height"] = value
            elif idx == 3 and value > 0:
                dimensions_dict["diameter"] = value
            elif idx == 4 and value > 0:
                dimensions_dict["radius"] = value
            elif idx == 5 and value > 0:
                dimensions_dict["thickness"] = value
            
            dimensions_dict["unit"] = unit
        
        return DimensionData(**dimensions_dict)
    
    def _extract_material_type(self, text: str) -> str:
        """
        Extract material type from text using pattern matching
        """
        material_keywords = {
            "steel": ["steel", "ms", "mild steel"],
            "stainless_steel": ["stainless", "ss", "inox"],
            "aluminum": ["aluminum", "aluminium", "al"],
            "brass": ["brass"],
            "copper": ["copper"],
            "cast_iron": ["cast iron", "ci"],
            "titanium": ["titanium", "ti"]
        }
        
        text_lower = text.lower()
        
        for material, keywords in material_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return material.replace("_", " ")
        
        return "steel"  # Default material
    
    def _extract_surface_finish(self, text: str) -> str:
        """
        Extract surface finish specifications
        """
        finish_keywords = {
            "polished": ["polished", "mirror finish"],
            "ground": ["ground", "grinding"],
            "machined": ["machined", "machine finish"],
            "as_cast": ["as cast", "rough"],
            "brushed": ["brushed"],
            "anodized": ["anodized"]
        }
        
        text_lower = text.lower()
        
        for finish, keywords in finish_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return finish.replace("_", " ")
        
        return "machined"  # Default finish
    
    def _extract_tolerances(self, text: str) -> Dict[str, float]:
        """
        Extract tolerance specifications
        """
        tolerances = {}
        
        # Pattern for tolerance notation (e.g., ±0.1mm)
        tolerance_pattern = r'±\s*(\d+\.?\d*)'
        matches = re.findall(tolerance_pattern, text)
        
        for idx, match in enumerate(matches[:3]):  # Extract up to 3 tolerances
            tolerance_type = ["general", "critical", "surface"][idx]
            tolerances[tolerance_type] = float(match)
        
        # Default tolerances if none found
        if not tolerances:
            tolerances = {
                "general": 0.1,
                "critical": 0.05,
                "surface": 0.01
            }
        
        return tolerances
    
    def _extract_geometric_features(self, text: str) -> List[str]:
        """
        Extract geometric features from text
        """
        features = []
        
        feature_keywords = {
            "holes": ["hole", "holes", "drilling"],
            "threads": ["thread", "threads", "threading", "m10", "m12"],
            "slots": ["slot", "slots"],
            "edges": ["edge", "edges", "chamfer"],
            "curves": ["curve", "curved", "radius"],
            "pockets": ["pocket", "pockets"],
            "boss": ["boss", "bosses"],
            "surfaces": ["surface", "surfaces", "finish"]
        }
        
        text_lower = text.lower()
        
        for feature, keywords in feature_keywords.items():
            for keyword in keywords:
                if keyword in text_lower and feature not in features:
                    features.append(feature)
        
        return features if features else ["standard_geometry"]
    
    def _estimate_weight(self, dimensions: DimensionData, material_type: str) -> float:
        """
        Estimate part weight based on dimensions and material
        """
        # Density values (g/cm³)
        densities = {
            "steel": 7.85,
            "stainless steel": 7.75,
            "aluminum": 2.7,
            "brass": 8.5,
            "copper": 8.96,
            "cast iron": 7.3,
            "titanium": 4.51
        }
        
        density = densities.get(material_type.lower(), 7.85)
        
        # Calculate volume (simplified rectangular)
        length = dimensions.length or 1
        width = dimensions.width or 1
        height = dimensions.height or 1
        
        volume_cm3 = length * width * height  # Assuming dimensions in cm
        estimated_weight = volume_cm3 * density / 1000  # Convert to kg
        
        return round(estimated_weight, 2)
