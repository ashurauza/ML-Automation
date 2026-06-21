"""
Cost calculation service for computing component costs
"""
import logging
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculate manufacturing costs based on extracted parameters"""
    
    def __init__(self):
        self.logger = logger
        
        # Load default cost parameters
        self.material_cost_multiplier = float(os.getenv("DEFAULT_MATERIAL_COST_MULTIPLIER", 1.2))
        self.machining_rate = float(os.getenv("DEFAULT_MACHINING_RATE", 50))  # per hour
        self.labor_rate = float(os.getenv("DEFAULT_LABOR_RATE", 25))  # per hour
        self.overhead_percentage = float(os.getenv("DEFAULT_OVERHEAD_PERCENTAGE", 15))
        self.profit_margin = float(os.getenv("DEFAULT_PROFIT_MARGIN", 20))
    
    def calculate_costs(
        self,
        material_type: str,
        operations: List[str],
        cycle_time: float,
        dimensions: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate all cost components
        
        Args:
            material_type: Type of material
            operations: List of manufacturing operations
            cycle_time: Estimated cycle time in hours
            dimensions: Dictionary containing part dimensions
            
        Returns:
            Dictionary with cost breakdown
        """
        try:
            # Calculate raw material cost
            raw_material_cost = self._calculate_material_cost(material_type, dimensions)
            
            # Calculate machining cost
            machining_cost = self._calculate_machining_cost(operations, cycle_time)
            
            # Calculate manpower cost
            manpower_cost = self._calculate_manpower_cost(cycle_time, len(operations))
            
            # Calculate overhead cost
            subtotal = raw_material_cost + machining_cost + manpower_cost
            overhead_cost = subtotal * (self.overhead_percentage / 100)
            
            # Calculate logistics cost
            logistics_cost = self._calculate_logistics_cost(dimensions)
            
            # Calculate total before profit
            total_before_profit = raw_material_cost + machining_cost + manpower_cost + overhead_cost + logistics_cost
            
            # Calculate profit margin
            profit_margin = total_before_profit * (self.profit_margin / 100)
            
            # Total cost
            total_cost = total_before_profit + profit_margin
            
            return {
                "raw_material_cost": round(raw_material_cost, 2),
                "machining_cost": round(machining_cost, 2),
                "manpower_cost": round(manpower_cost, 2),
                "overhead_cost": round(overhead_cost, 2),
                "logistics_cost": round(logistics_cost, 2),
                "profit_margin": round(profit_margin, 2),
                "total_cost": round(total_cost, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating costs: {str(e)}")
            raise Exception(f"Cost calculation error: {str(e)}")
    
    def _calculate_material_cost(self, material_type: str, dimensions: Dict[str, Any]) -> float:
        """
        Calculate raw material cost based on material type and volume
        """
        # Material base costs per kg (simplified)
        material_costs = {
            "steel": 0.8,
            "aluminum": 2.5,
            "brass": 3.0,
            "copper": 4.5,
            "stainless_steel": 2.0,
            "stainless steel": 2.0,
            "cast_iron": 0.6,
            "titanium": 15.0,
            "default": 1.5
        }
        
        # Get material cost
        material_name = material_type.lower().replace(" ", "_") if material_type else "default"
        base_cost_per_kg = material_costs.get(material_name, material_costs.get(material_type.lower() if material_type else "default", material_costs["default"]))
        
        # Estimate volume (simplified calculation)
        volume = self._estimate_volume(dimensions)  # in cm³
        
        # Ensure minimum volume for cost calculation
        if volume <= 0:
            volume = 100  # Default volume in cm³ for small parts
        
        # Density estimation (kg/cm³)
        densities = {
            "steel": 0.0079,
            "aluminum": 0.0027,
            "brass": 0.0085,
            "copper": 0.0089,
            "stainless_steel": 0.0075,
            "stainless steel": 0.0075,
            "cast_iron": 0.0073,
            "titanium": 0.0045,
            "default": 0.006
        }
        
        density = densities.get(material_name, densities.get(material_type.lower() if material_type else "default", densities["default"]))
        estimated_weight = volume * density  # in kg
        
        # Ensure minimum weight
        if estimated_weight <= 0:
            estimated_weight = 0.5  # Default minimum weight in kg
        
        # Add material utilization factor (material waste)
        utilization_factor = 1.3  # 30% waste
        
        material_cost = (estimated_weight * utilization_factor * base_cost_per_kg * self.material_cost_multiplier)
        
        return material_cost
    
    def _calculate_machining_cost(self, operations: List[str], cycle_time: float) -> float:
        """
        Calculate machining cost based on operations and cycle time
        """
        # Add setup time (fixed cost)
        setup_time = 0.5  # hours
        total_time = setup_time + cycle_time
        
        # Machining cost
        machining_cost = total_time * self.machining_rate
        
        return machining_cost
    
    def _calculate_manpower_cost(self, cycle_time: float, num_operations: int) -> float:
        """
        Calculate labor cost based on cycle time and operation complexity
        """
        # Complexity factor based on number of operations
        complexity_factor = 1.0 + (num_operations * 0.1)
        
        # Operator engagement (not 100% during entire cycle)
        engagement_factor = 0.4
        
        manpower_cost = cycle_time * engagement_factor * self.labor_rate * complexity_factor
        
        return manpower_cost
    
    def _calculate_logistics_cost(self, dimensions: Dict[str, Any]) -> float:
        """
        Calculate logistics and transportation cost
        """
        # Base logistics cost
        base_logistics_cost = 50  # Fixed component
        
        # Volume-based component
        volume = self._estimate_volume(dimensions)
        volume_based_cost = volume * 0.01  # Cost per cm³
        
        total_logistics_cost = base_logistics_cost + volume_based_cost
        
        return total_logistics_cost
    
    def _estimate_volume(self, dimensions: Dict[str, Any]) -> float:
        """
        Estimate part volume from dimensions
        """
        length = dimensions.get("length", 1)
        width = dimensions.get("width", 1)
        height = dimensions.get("height", 1)
        
        # Simple rectangular volume estimation
        volume = length * width * height
        
        return volume
    
    def estimate_cycle_time(self, operations: List[str], dimensions: Dict[str, Any]) -> float:
        """
        Estimate manufacturing cycle time based on operations
        """
        # Base times for operations (in minutes)
        operation_times = {
            "turning": 15,
            "milling": 20,
            "drilling": 10,
            "grinding": 12,
            "honing": 8,
            "boring": 15,
            "threading": 10,
            "facing": 8,
            "chamfering": 5,
            "deburring": 5
        }
        
        total_time = 0
        
        for operation in operations:
            operation_lower = operation.lower()
            if operation_lower in operation_times:
                total_time += operation_times[operation_lower]
            else:
                total_time += 10  # default time
        
        # Convert to hours
        cycle_time_hours = total_time / 60
        
        # Add complexity factor based on dimensions
        complexity_factor = 1.0 + (len(dimensions) * 0.05)
        
        return cycle_time_hours * complexity_factor
