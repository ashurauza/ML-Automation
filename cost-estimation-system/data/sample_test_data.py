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

# Steering Roll Handling Assembly - Complex Dataset based on Excel sample
STEERING_ROLL_HANDLING_DATA = {
    "assy_no": "2118 626 01A1",
    "product_name": "STEERING ROLL HANDLING RIG ADAPTOR ASSEMBLY",
    "moq_qty": 5,
    "rm_cost": {
        "rm_gross_weight": 5091.15,
        "rm_net_weight": 3281.90,
        "raw_material": 389673,
        "bop_fastener": 0,
        "total_rm_cost": 389673
    },
    "process_cost": {
        "assy_cost": 0,
        "fabrication_process_cost": 572827,
        "inspection_testing": 26255,
        "painting": 32819,
        "packaging": 0,
        "total_basic_cost": 1021573
    },
    "fixed_cost": {
        "icc_cost": 10478,
        "rejection": 15717,
        "transportation": 0,
        "sub_total": 1047767
    },
    "variable_cost": {
        "contingency_warranty": 12935,
        "overheads": 103483,
        "contribution_profit": 129354,
        "total_price_x_parts": 1293540,
        "total_price_per_part": 258708
    },
    "non_recurring_cost": {
        "engineering_charges": 50000,
        "jig_fixtures_development": 199868,
        "sub_cost": 249868,
        "contingency": 6350,
        "overheads": 25400,
        "contribution_profit": 35877,
        "total_nrc_cost": 317494
    },
    "bom": [
        {
            "s_no": 1, "level": 0, "drawing_no": "2118 626 01A1", 
            "description": "STEERING ROLL HANDLING RIG ADAPTOR ASSEMBLY", "qty": 5, "total_qty": 5,
            "net_weight": 659.39, "total_wt": 3296.95, "type": "Final Assy",
            "material_grade": "", "is_size": "", "width": "", "length": "",
            "gross_wt": "", "total_gross_wt": "", "machining_time": 5250, "machining_cost": 272750
        },
        {
            "s_no": 2, "level": 1, "drawing_no": "", 
            "description": "PIPE DN350 x SCH-80 x 685 LG. ENDS SQ.", "qty": 1, "total_qty": 5,
            "net_weight": 104.73, "total_wt": 523.65, "type": "Pipe",
            "material_grade": "ASTM A106 GR.B", "is_size": "OD 355.6 x 19.05 thk", "width": "", "length": 685,
            "gross_wt": 584.85, "total_gross_wt": 948.66, "machining_time": 60, "machining_cost": 500
        },
        {
            "s_no": 3, "level": 2, "drawing_no": "", 
            "description": "PLATE 320 O.D. x 190 I.D. x 180 LG. ENDS SQ.", "qty": 1, "total_qty": 5,
            "net_weight": 62.2, "total_wt": 311.05, "type": "Block",
            "material_grade": "IS2062 : E250A", "is_size": "180", "width": 190, "length": 320,
            "gross_wt": 463.92, "total_gross_wt": 556.70, "machining_time": 240, "machining_cost": 2000
        },
        {
            "s_no": 4, "level": 3, "drawing_no": "", 
            "description": "PLATE 40 THK x 490 x 985 LG.", "qty": 1, "total_qty": 5,
            "net_weight": 119.9, "total_wt": 599.25, "type": "Plate",
            "material_grade": "IS2062 : E250A", "is_size": "40", "width": 490, "length": 985,
            "gross_wt": 818.38, "total_gross_wt": 818.38, "machining_time": "", "machining_cost": ""
        },
        {
            "s_no": 5, "level": 4, "drawing_no": "", 
            "description": "PLATE 20 THK x 610 x 1150 LG.", "qty": 1, "total_qty": 5,
            "net_weight": 113.8, "total_wt": 568.85, "type": "Plate",
            "material_grade": "IS2062 : E250A", "is_size": "20", "width": 610, "length": 1150,
            "gross_wt": 951.57, "total_gross_wt": 951.57, "machining_time": "", "machining_cost": ""
        },
        {
            "s_no": 6, "level": 5, "drawing_no": "", 
            "description": "PLATE 25 THK x 585 x 1130 LG.", "qty": 2, "total_qty": 10,
            "net_weight": 121.6, "total_wt": 1216.30, "type": "Plate",
            "material_grade": "IS2062 : E250A", "is_size": "25", "width": 585, "length": 1130,
            "gross_wt": 1401.10, "total_gross_wt": 1401.10, "machining_time": 15, "machining_cost": 250
        },
        {
            "s_no": 7, "level": 6, "drawing_no": "", 
            "description": "PLATE 20 THK x 220 x 220 LG.", "qty": 1, "total_qty": 5,
            "net_weight": 4.8, "total_wt": 23.90, "type": "Plate",
            "material_grade": "IS2062 : E250A", "is_size": "20", "width": 220, "length": 220,
            "gross_wt": 41.03, "total_gross_wt": 41.03, "machining_time": "", "machining_cost": ""
        }
    ]
}
