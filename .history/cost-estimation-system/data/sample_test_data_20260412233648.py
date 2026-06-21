"""
Sample test data for cost estimation system
"""

# Sample cost parameters
SAMPLE_COST_PARAMETERS = {
    "material_costs": {
        "Aluminum": 15.0,  # per kg
        "Steel": 8.0,
        "Copper": 25.0,
        "Plastic": 5.0,
    },
    "labor_rates": {
        "CNC_Milling": 50.0,  # per hour
        "Drilling": 35.0,
        "Turning": 45.0,
        "Anodizing": 30.0,
        "Heat_Treatment": 40.0,
        "Injection_Molding": 60.0,
        "Polishing": 25.0,
    },
    "overhead_percentage": 15.0,  # 15% of total manufacturing cost
    "profit_margin": 25.0,  # 25% profit margin
    "logistics_cost_per_unit": 2.5,
}

# Sample estimation data
SAMPLE_ESTIMATIONS = [
    {
        "filename": "aluminum_bracket.pdf",
        "material": "Aluminum 6061-T6",
        "material_weight": 1.2,  # kg
        "dimensions": {
            "length": 150,
            "width": 100,
            "height": 50,
        },
        "operations": [
            {"name": "CNC_Milling", "time": 2.0},
            {"name": "Drilling", "time": 0.5},
            {"name": "Anodizing", "time": 1.0},
        ],
        "quantity": 100,
    },
    {
        "filename": "steel_shaft.pdf",
        "material": "Carbon Steel AISI 1045",
        "material_weight": 3.5,  # kg
        "dimensions": {
            "diameter": 50,
            "length": 300,
        },
        "operations": [
            {"name": "Turning", "time": 3.0},
            {"name": "Heat_Treatment", "time": 4.0},
        ],
        "quantity": 50,
    },
    {
        "filename": "plastic_housing.pdf",
        "material": "Polycarbonate (PC)",
        "material_weight": 0.5,  # kg
        "dimensions": {
            "length": 200,
            "width": 150,
            "height": 80,
        },
        "operations": [
            {"name": "Injection_Molding", "time": 5.0},
        ],
        "quantity": 500,
    },
]

# Expected cost breakdown for Aluminum Bracket (per unit)
EXPECTED_COST_BREAKDOWN_BRACKET = {
    "raw_material_cost": 18.0,  # 1.2 kg * 15 $/kg
    "machining_cost": 115.0,  # (2*50 + 0.5*35 + 1*30) for CNC, Drilling, Anodizing
    "labor_cost": 30.0,
    "overhead_cost": 17.25,  # 15% of manufacturing
    "logistics_cost": 2.5,
    "subtotal": 182.75,
    "profit_margin": 45.69,  # 25% of subtotal
    "total_cost": 228.44,
}

if __name__ == "__main__":
    print("Sample Cost Parameters:")
    print(f"Material Costs: {SAMPLE_COST_PARAMETERS['material_costs']}")
    print(f"Labor Rates: {SAMPLE_COST_PARAMETERS['labor_rates']}")
    print(f"\nExpected Cost Breakdown (per unit):")
    for key, value in EXPECTED_COST_BREAKDOWN_BRACKET.items():
        print(f"  {key}: ${value:.2f}")
