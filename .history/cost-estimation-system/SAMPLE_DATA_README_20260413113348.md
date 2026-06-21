# Sample PDF and Test Data Documentation

## Sample PDFs Created

Four sample engineering drawing PDFs have been created for testing the cost estimation system:

### 1. **sample_aluminum_bracket.pdf**
- **Material**: Aluminum 6061-T6
- **Part Type**: Precision Bracket
- **Dimensions**:
  - Length: 150 mm ± 0.5 mm
  - Width: 100 mm ± 0.3 mm
  - Height: 50 mm ± 0.2 mm
  - Hole Diameter: 10 mm ± 0.1 mm
- **Manufacturing Processes**:
  - CNC Milling (2 hours)
  - Drilling (30 minutes)
  - Deburring (15 minutes)
  - Anodizing (1 hour)

### 2. **sample_steel_shaft.pdf**
- **Material**: Carbon Steel AISI 1045
- **Part Type**: Rotating Shaft
- **Dimensions**:
  - Diameter: 50 mm ± 0.2 mm
  - Length: 300 mm ± 0.5 mm
  - Thread: M20x2.5 - 6H
- **Manufacturing Processes**:
  - Turning (3 hours)
  - Threading (1 hour)
  - Grinding (1.5 hours)
  - Heat Treatment (4 hours)

### 3. **sample_plastic_housing.pdf**
- **Material**: Polycarbonate (PC)
- **Part Type**: Equipment Housing
- **Dimensions**:
  - Length: 200 mm ± 1 mm
  - Width: 150 mm ± 1 mm
  - Height: 80 mm ± 0.5 mm
  - Wall Thickness: 3 mm ± 0.2 mm
- **Manufacturing Processes**:
  - Injection Molding (5 hours)
  - Trimming (30 minutes)
  - Quality Check (30 minutes)

### 4. **sample_copper_plate.pdf**
- **Material**: Pure Copper
- **Part Type**: Heat Sink Plate
- **Dimensions**:
  - Length: 120 mm ± 0.3 mm
  - Width: 80 mm ± 0.3 mm
  - Thickness: 10 mm ± 0.2 mm
- **Manufacturing Processes**:
  - Cutting (30 minutes)
  - Milling (1 hour)
  - Polishing (1 hour)
  - Passivation (2 hours)

## Using the Sample PDFs

### Method 1: Upload via Web Interface
1. Open http://localhost:3000
2. Go to "Upload Drawing" section
3. Select any of the sample PDFs
4. View extracted parameters and cost estimation

### Method 2: Using the API
```bash
# Upload a PDF
curl -X POST "http://localhost:8000/api/estimation/upload" \
  -F "file=@data/sample_aluminum_bracket.pdf"

# Get the estimation ID from the response, then estimate:
curl -X POST "http://localhost:8000/api/estimation/estimate/1"
```

### Method 3: Run the Test Suite
```bash
# From the project root directory
source backend/venv/bin/activate
python3 test_api.py
```

## Sample Test Data (test_api.py)

A comprehensive test suite has been created to verify:
- ✓ Backend health check
- ✓ Cost parameter retrieval
- ✓ PDF upload functionality
- ✓ Cost estimation generation
- ✓ Estimation history retrieval

Run the tests with:
```bash
python3 test_api.py
```

## Expected Readings from PDF Processing

When you upload the sample PDFs, the system should:

1. **Extract Text Data**:
   - Part name and material
   - Dimensions with tolerances
   - Manufacturing processes
   - Estimated timeframes

2. **Calculate Cost Breakdown**:
   - Raw Material Cost: Based on weight × material rate
   - Machining Cost: Based on operation hours × labor rates
   - Labor Cost: Additional labor overhead
   - Overhead Cost: 15% of manufacturing cost
   - Logistics Cost: $2.50 per unit
   - Profit Margin: 25% of total

3. **Generate Estimation**:
   - Total cost per unit
   - Extended cost for quantity
   - Cost breakdown summary
   - Confidence score

## Cost Parameter Defaults

The system is initialized with default cost parameters:

| Parameter | Value |
|-----------|-------|
| Aluminum Material | $15/kg |
| Steel Material | $8/kg |
| Copper Material | $25/kg |
| Plastic Material | $5/kg |
| CNC Milling Labor | $50/hour |
| Drilling Labor | $35/hour |
| Turning Labor | $45/hour |
| Overhead Percentage | 15% |
| Profit Margin | 25% |
| Logistics Cost | $2.50/unit |

## Troubleshooting

### PDF Upload Fails
- Ensure poppler is installed: `which pdftoppm`
- Ensure tesseract is installed: `which tesseract`
- PDFs must be in valid format

### OCR Not Working
Install additional language packs if needed:
```bash
brew install tesseract-lang
```

### Missing Dependencies
Reinstall backend dependencies:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

## Notes

- All sample PDFs are created with ReportLab and contain valid text data
- The system uses OCR (Tesseract) as a fallback for image-based PDFs
- Extracted parameters are stored in the database for future reference
- Cost calculations are based on configured parameters (editable via API)
