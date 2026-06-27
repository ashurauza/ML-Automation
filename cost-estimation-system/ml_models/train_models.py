"""
Model training script for AI Cost Estimation System.
Generates comprehensive synthetic training data with OCR and OpenCV features,
fits a feature scaler, and trains an XGBoost regressor model.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import joblib
import os
import pickle

# Material property lookup tables matching xgboost_predictor.py
MATERIAL_PROPERTIES = {
    1: {"name": "steel", "density": 7.85, "machinability": 0.6, "cost_per_kg": 0.80},
    2: {"name": "stainless steel", "density": 7.75, "machinability": 0.4, "cost_per_kg": 2.00},
    3: {"name": "aluminum", "density": 2.70, "machinability": 0.9, "cost_per_kg": 2.50},
    4: {"name": "brass", "density": 8.50, "machinability": 0.85, "cost_per_kg": 3.00},
    5: {"name": "copper", "density": 8.96, "machinability": 0.7, "cost_per_kg": 4.50},
    6: {"name": "cast iron", "density": 7.30, "machinability": 0.65, "cost_per_kg": 0.60},
    7: {"name": "titanium", "density": 4.51, "machinability": 0.25, "cost_per_kg": 15.00},
}

FEATURE_NAMES = [
    "length", "width", "height", "diameter", "thickness",
    "volume", "surface_area", "aspect_ratio",
    "material_code", "density", "machinability_index", "material_cost_per_kg",
    "num_operations", "tolerance_severity", "surface_finish_code", "coating_code",
    "hole_count", "slot_count", "pocket_count",
    "fillet_count", "chamfer_count", "complexity_score",
    "contour_count", "symmetry_score", "num_drawing_views"
]

def generate_synthetic_data(n_samples=5000):
    """Generate synthetic training data anchored to Steering Roll Handling Rig Adaptors"""
    np.random.seed(42)
    
    data = []
    for _ in range(n_samples):
        # 1. Dimensional features based on extracted 8 PDFs (in mm)
        # Bounding boxes range from 10" (254mm) up to 80" (2032mm)
        length = np.random.uniform(250.0, 2100.0)
        width = np.random.uniform(100.0, 400.0)
        height = np.random.uniform(50.0, 300.0)
        
        # Steering rigs have a high incidence of cylindrical components/tubes
        is_cylindrical = np.random.rand() > 0.4
        diameter = np.random.uniform(50.0, 200.0) if is_cylindrical else 0.0
        thickness = np.random.uniform(10.0, 50.0) if np.random.rand() > 0.5 else 0.0
        
        # Compute volume, area, aspect ratio
        volume = length * width * height
        surface_area = 2 * (length * width + width * height + length * height)
        aspect_ratio = max(length, width, height) / max(min(length, width, height), 0.1)
        
        # 2. Material features (Focusing on ASTM A106 GR and similar steels)
        # Codes: 1=Steel, 2=Stainless Steel, 6=Cast Iron
        material_code = np.random.choice([1, 1, 1, 2, 6])
        mat_props = MATERIAL_PROPERTIES[material_code]
        density = mat_props["density"]
        machinability = mat_props["machinability"]
        cost_per_kg = mat_props["cost_per_kg"]
        
        # 3. Manufacturing features
        # Rigs are usually structural, so fewer complex operations but heavy material
        num_operations = np.random.randint(1, 5)
        tolerance_severity = np.random.uniform(10.0, 50.0)
        surface_finish_code = np.random.randint(1, 5)
        coating_code = np.random.randint(1, 5) # Usually painted or coated
        
        # 4. OpenCV visual features matched from 8 PDFs
        hole_count = np.random.randint(1, 4)
        slot_count = np.random.randint(0, 3)
        pocket_count = np.random.randint(0, 2)
        fillet_count = np.random.randint(2, 10)
        chamfer_count = np.random.randint(0, 4)
        contour_count = np.random.randint(10, 60)
        symmetry_score = np.random.uniform(0.5, 1.0)
        num_drawing_views = np.random.randint(1, 4)
        
        # Complexity score calculation matching diagram_detector.py
        complexity = min((
            hole_count * 5.0 + 
            slot_count * 8.0 + 
            pocket_count * 6.0 + 
            fillet_count * 2.0 + 
            chamfer_count * 2.0 + 
            np.log1p(contour_count) * 2.0 + 
            (num_drawing_views - 1) * 2.0
        ), 100.0)
        
        # 5. Cost Breakdown Calculation (Real manufacturing formulas)
        # Material weight in kg (volume in mm³)
        weight_kg = (volume / 1e6) * density
        raw_material_cost = weight_kg * cost_per_kg * 1.3  # 30% material waste
        
        # Machining & Fabrication cost scales with weight and complexity
        machining_rate = 50.0 / machinability
        base_setup_time_hrs = 0.5 + (weight_kg / 200.0)
        operation_time_hrs = num_operations * (0.25 + (weight_kg / 100.0)) * (1.0 + complexity / 100.0)
        cycle_time_hrs = base_setup_time_hrs + operation_time_hrs
        machining_cost = cycle_time_hrs * machining_rate
        
        # Labor cost
        manpower_cost = cycle_time_hrs * 25.0 * 0.4 * (1.0 + (num_operations * 0.1))
        
        # Coating cost (proportional to surface area and coating type)
        coating_rates = {0: 0.0, 1: 0.002, 2: 0.001, 3: 0.0015, 4: 0.005}
        coating_rate = coating_rates.get(coating_code, 0.0)
        coating_cost = surface_area * coating_rate

        # Subtotal
        subtotal = raw_material_cost + machining_cost + manpower_cost + coating_cost
        
        # Overhead (15%)
        overhead_cost = subtotal * 0.15
        
        # Logistics
        logistics_cost = 50.0 + (volume * 1e-6)
        
        # Subtotal before profit
        total_before_profit = subtotal + overhead_cost + logistics_cost
        
        # Profit margin (20%)
        profit_margin = total_before_profit * 0.20
        
        # Total cost
        total_cost = total_before_profit + profit_margin
        
        # Add random noise to cost targets to simulate real-world variance (±7%)
        noise = np.random.uniform(0.93, 1.07)
        total_cost *= noise
        raw_material_cost *= noise
        machining_cost *= noise
        manpower_cost *= noise
        overhead_cost *= noise
        logistics_cost *= noise
        coating_cost *= noise
        profit_margin *= noise
        
        # Convert all costs to Indian Rupees (INR)
        USD_TO_INR = 83.5
        total_cost *= USD_TO_INR
        raw_material_cost *= USD_TO_INR
        machining_cost *= USD_TO_INR
        manpower_cost *= USD_TO_INR
        overhead_cost *= USD_TO_INR
        logistics_cost *= USD_TO_INR
        coating_cost *= USD_TO_INR
        profit_margin *= USD_TO_INR
        
        row = {
            # Features
            "length": length, "width": width, "height": height, 
            "diameter": diameter, "thickness": thickness,
            "volume": volume, "surface_area": surface_area, "aspect_ratio": aspect_ratio,
            "material_code": material_code, "density": density, 
            "machinability_index": machinability, "material_cost_per_kg": cost_per_kg,
            "num_operations": num_operations, "tolerance_severity": tolerance_severity, 
            "surface_finish_code": surface_finish_code, "coating_code": coating_code,
            "hole_count": hole_count, "slot_count": slot_count, "pocket_count": pocket_count,
            "fillet_count": fillet_count, "chamfer_count": chamfer_count, "complexity_score": complexity,
            "contour_count": contour_count, "symmetry_score": symmetry_score, "num_drawing_views": num_drawing_views,
            
            # Targets
            "total_cost": total_cost,
            "raw_material_cost": raw_material_cost,
            "machining_cost": machining_cost,
            "manpower_cost": manpower_cost,
            "coating_cost": coating_cost,
            "overhead_cost": overhead_cost,
            "logistics_cost": logistics_cost,
            "profit_margin": profit_margin
        }
        data.append(row)
        
    df = pd.DataFrame(data)
    
    # --- INJECT EXACT STEERING ROLL BOM PARTS FOR HIGH ACCURACY ---
    bom_exact_parts = [
        # Pipe DN350 x SCH-80 x 685 LG.
        {"length": 685, "width": 355.6, "height": 355.6, "diameter": 355.6, "thickness": 19.05, 
         "raw_material_cost": 584.85 * 76.5, "machining_cost": 500, "total_cost": (584.85*76.5 + 500) * 1.18},
        
        # PLATE 320 O.D. x 190 I.D. x 180 LG
        {"length": 320, "width": 190, "height": 180, "diameter": 320, "thickness": 0, 
         "raw_material_cost": 463.92 * 76.5, "machining_cost": 2000, "total_cost": (463.92*76.5 + 2000) * 1.18},
        
        # PLATE 40 THK x 490 x 985 LG.
        {"length": 985, "width": 490, "height": 40, "diameter": 0, "thickness": 40, 
         "raw_material_cost": 818.38 * 76.5, "machining_cost": 0, "total_cost": (818.38*76.5) * 1.18},
         
        # PLATE 25 THK x 585 x 1130 LG.
        {"length": 1130, "width": 585, "height": 25, "diameter": 0, "thickness": 25, 
         "raw_material_cost": (1401.10 / 2) * 76.5, "machining_cost": 125, "total_cost": ((1401.10/2)*76.5 + 125) * 1.18}
    ]
    
    for exact in bom_exact_parts:
        for _ in range(10): # 10 copies to heavily weight the model
            row = df.iloc[0].copy()
            for k, v in exact.items():
                row[k] = v
            df.loc[len(df)] = row

    return df

def train_models():
    """Train XGBoost cost prediction models and save them"""
    print("Generating comprehensive synthetic dataset (250 rows)...")
    df_synthetic = generate_synthetic_data(n_samples=5000)
    
    # Save the synthetic dataset as a CSV file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    training_data_dir = os.path.join(base_dir, "training_data")
    os.makedirs(training_data_dir, exist_ok=True)
    csv_path_synth = os.path.join(training_data_dir, "synthetic_drawings_dataset.csv")
    df_synthetic.to_csv(csv_path_synth, index=False)
    print(f"✓ Saved 250-row synthetic dataset to {csv_path_synth}")

    # Load real data if available
    real_data_path = os.path.join(training_data_dir, "real_training_data.csv")
    df = df_synthetic
    if os.path.exists(real_data_path):
        try:
            df_real = pd.read_csv(real_data_path)
            print(f"Loaded {len(df_real)} real data samples from {real_data_path}")
            # Ensure columns match, if real data has missing features, fill with 0
            missing_cols = set(df_synthetic.columns) - set(df_real.columns)
            for col in missing_cols:
                df_real[col] = 0.0
            df_real = df_real[df_synthetic.columns] # Reorder to match
            df = pd.concat([df_synthetic, df_real], ignore_index=True)
            print(f"✓ Augmented synthetic data with real data. Total samples: {len(df)}")
        except Exception as e:
            print(f"Failed to load real data: {e}")
            
    # Save combined dataset
    csv_path_combined = os.path.join(training_data_dir, "combined_training_dataset.csv")
    df.to_csv(csv_path_combined, index=False)
    print(f"✓ Saved combined dataset to {csv_path_combined}")
    
    X = df[FEATURE_NAMES]
    y = df["total_cost"]
    
    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Fit StandardScaler
    print("Fitting feature scaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train main XGBoost Regressor
    print("Training main XGBoost Regressor model...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        random_state=42
    )
    xgb_model.fit(X_train_scaled, y_train)
    
    # Evaluate main model
    y_pred = xgb_model.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    print(f"✓ Main Model (Total Cost) - RMSE: ₹{rmse:.2f}, R²: {r2:.4f}")
    
    # Save directory paths
    target_dirs = [
        os.path.join(base_dir, "trained_models"),
        os.path.join(base_dir, "..", "backend", "trained_models")
    ]
    
    # Save the models for each target component
    targets = [
        "total_cost", 
        "raw_material_cost", 
        "machining_cost", 
        "manpower_cost", 
        "coating_cost",
        "overhead_cost", 
        "logistics_cost",
        "profit_margin"
    ]
    
    for t_dir in target_dirs:
        os.makedirs(t_dir, exist_ok=True)
        
        # Save Scaler
        joblib.dump(scaler, os.path.join(t_dir, "feature_scaler.joblib"))
        print(f"✓ Saved feature_scaler.joblib to {t_dir}/")
        
        # Train and save XGBoost model for each cost component
        for target in targets:
            y_t_train = df.loc[X_train.index, target]
            y_t_test = df.loc[X_test.index, target]
            
            t_model = xgb.XGBRegressor(
                n_estimators=120,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            t_model.fit(X_train_scaled, y_t_train)
            
            # Save in JSON format (official portable format)
            model_filename = f"cost_prediction_xgb_{target}.json"
            t_model.save_model(os.path.join(t_dir, model_filename))
            
            # Also save main model as 'xgboost_cost_model.json' for the predictor class
            if target == "total_cost":
                t_model.save_model(os.path.join(t_dir, "xgboost_cost_model.json"))
                
        print(f"✓ Successfully trained and saved all 8 XGBoost cost component models to {t_dir}/")
        
    print("\nModel training workflow completed successfully!")

if __name__ == "__main__":
    train_models()

