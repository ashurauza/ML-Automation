"""
Sample data for testing and development
"""

# Sample engineering drawing parameters
SAMPLE_DRAWINGS = [
    {
        "name": "Simple_Cylindrical_Part.pdf",
        "dimensions": {
            "diameter": 50,
            "length": 100,
            "unit": "mm"
        },
        "material": "steel",
        "operations": ["turning", "facing"],
        "tolerances": {
            "general": 0.1,
            "critical": 0.05
        }
    },
    {
        "name": "Complex_Bracket.pdf",
        "dimensions": {
            "length": 200,
            "width": 150,
            "height": 75,
            "unit": "mm"
        },
        "material": "aluminum",
        "operations": ["milling", "drilling", "grinding"],
        "tolerances": {
            "general": 0.15,
            "critical": 0.05,
            "surface": 0.01
        },
        "features": ["holes", "slots", "surfaces"]
    }
]

# Sample cost parameters
SAMPLE_COST_PARAMETERS = [
    {
        "parameter_name": "Machining_Rate",
        "parameter_value": 50,
        "description": "Machining cost per hour in USD",
        "is_editable": True
    },
    {
        "parameter_name": "Labor_Rate",
        "parameter_value": 25,
        "description": "Labor cost per hour in USD",
        "is_editable": True
    },
    {
        "parameter_name": "Material_Cost_Multiplier",
        "parameter_value": 1.2,
        "description": "Multiplier for raw material costs",
        "is_editable": True
    },
    {
        "parameter_name": "Overhead_Percentage",
        "parameter_value": 15,
        "description": "Overhead costs as percentage",
        "is_editable": True
    },
    {
        "parameter_name": "Profit_Margin",
        "parameter_value": 20,
        "description": "Profit margin percentage",
        "is_editable": True
    }
]

# Material properties
MATERIAL_PROPERTIES = {
    "steel": {
        "density": 7.85,
        "base_cost_per_kg": 0.8,
        "machinability": "medium"
    },
    "stainless_steel": {
        "density": 7.75,
        "base_cost_per_kg": 2.0,
        "machinability": "low"
    },
    "aluminum": {
        "density": 2.7,
        "base_cost_per_kg": 2.5,
        "machinability": "high"
    },
    "brass": {
        "density": 8.5,
        "base_cost_per_kg": 3.0,
        "machinability": "high"
    },
    "copper": {
        "density": 8.96,
        "base_cost_per_kg": 4.5,
        "machinability": "medium"
    }
}

# Manufacturing operations and their typical times
OPERATION_TIMES = {
    "turning": 15,      # minutes
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
