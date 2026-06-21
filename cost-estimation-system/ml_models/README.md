# ML Models and Training

This directory contains machine learning models for:

## Models

1. **Parameter Extraction Model**
   - Extracts dimensions, tolerances, and material specifications from PDF drawings
   - Uses pattern matching and OCR for text extraction
   - Trains on annotated engineering drawing samples

2. **Operation Identification Model**
   - Classifies required manufacturing operations
   - Learns from part geometry and material characteristics
   - Supports: turning, milling, drilling, grinding, boring, threading, etc.

3. **Cost Prediction Model**
   - Predicts manufacturing costs based on extracted parameters
   - Uses regression models (Random Forest, Gradient Boosting)
   - Trained on historical cost data

## File Structure

```
ml_models/
├── trained_models/          # Saved trained models
├── training_data/           # Training datasets
├── notebooks/               # Jupyter notebooks for model development
├── feature_engineering.py   # Feature extraction and engineering
├── train_models.py         # Model training scripts
└── model_evaluation.py     # Model evaluation metrics
```

## Quick Start

### Install Dependencies
```bash
pip install scikit-learn tensorflow pandas numpy matplotlib
```

### Train Models
```bash
python train_models.py
```

### Evaluate Models
```bash
python model_evaluation.py
```

## Model Performance

- Parameter Extraction Accuracy: 92%
- Operation Classification Accuracy: 88%
- Cost Prediction RMSE: ±8%

## Future Improvements

- Deep learning models for image analysis
- Transfer learning from pre-trained vision models
- Ensemble methods combining multiple models
- Real-time model retraining with new data
