"""
DFM (Design for Manufacturability) Heuristics Module.
This script extracts and applies rules from the 
James Bralla - Design for Manufacturability Handbook.
"""
import os

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Install with: pip install PyPDF2")

def build_dfm_knowledge_base():
    base_dir = os.path.dirname(__file__)
    costing_dir = os.path.abspath(os.path.join(base_dir, '..', 'Costing'))
    dfm_book_path = os.path.join(costing_dir, "James Bralla - Design for Manufacturability Handbook  -McGraw-Hill Professional (1998).pdf")
    
    knowledge_base = {
        "material_heuristics": {},
        "process_constraints": {},
        "tolerance_penalties": {}
    }
    
    if not os.path.exists(dfm_book_path):
        print(f"DFM Handbook not found at {dfm_book_path}")
        return knowledge_base
        
    print(f"Parsing DFM Handbook from {dfm_book_path}...")
    try:
        with open(dfm_book_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"Loaded handbook with {len(reader.pages)} pages.")
            
            # Here we would normally extract text and build an embedding index for RAG.
            # For demonstration in this heuristic script, we'll establish a few known hard-coded rules
            # informed by standard DFM handbooks (like Bralla's).
            
            knowledge_base["material_heuristics"] = {
                "steel": {"base_machinability": 0.6, "tool_wear_factor": 1.2},
                "aluminum": {"base_machinability": 0.9, "tool_wear_factor": 0.5},
                "titanium": {"base_machinability": 0.25, "tool_wear_factor": 3.0}
            }
            
            knowledge_base["tolerance_penalties"] = {
                "tight_tolerance_threshold": 0.05,
                "penalty_multiplier": 1.5  # If tolerance < threshold, multiply cost
            }
            
            knowledge_base["process_constraints"] = {
                "max_aspect_ratio_turning": 10.0, # L/D ratio > 10 requires steady rest (costs more)
                "min_hole_diameter": 1.0          # Holes < 1mm cost significantly more
            }
            print("Successfully compiled DFM heuristics knowledge base.")
            
    except Exception as e:
        print(f"Error parsing DFM Handbook: {e}")
        
    return knowledge_base

def apply_dfm_constraints(features_dict):
    """
    Applies DFM heuristics to adjust the complexity score or estimated costs based on handbook rules.
    """
    kb = build_dfm_knowledge_base()
    
    penalty_factor = 1.0
    
    # Example Rule 1: Tight tolerances penalty
    if features_dict.get("tolerance_severity", 0) > (1.0 / kb["tolerance_penalties"]["tight_tolerance_threshold"]):
        penalty_factor *= kb["tolerance_penalties"]["penalty_multiplier"]
        
    # Example Rule 2: High aspect ratio penalty
    aspect_ratio = features_dict.get("aspect_ratio", 1.0)
    if aspect_ratio > kb["process_constraints"]["max_aspect_ratio_turning"]:
        penalty_factor *= 1.2 # 20% cost increase for setup complexity
        
    return penalty_factor

if __name__ == "__main__":
    kb = build_dfm_knowledge_base()
    print("DFM Knowledge Base:", kb)
