"""
Estimation routes for handling PDF/image uploads and cost calculation.

Enhanced with:
- Image upload support (JPEG/PNG)
- OpenCV diagram analysis
- XGBoost ML cost prediction
- Enriched API responses with diagram features and ML insights
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import os
import logging
from datetime import datetime
from database import get_db
from models import Estimation, ExtractedParameters, CostBreakdown
from services.pdf_processor import PDFProcessor
from services.cost_calculator import CostCalculator
from services.ml_service import MLService

router = APIRouter()
logger = logging.getLogger(__name__)

pdf_processor = PDFProcessor()
cost_calculator = CostCalculator()
ml_service = MLService()

# Supported file types
ALLOWED_PDF_TYPES = {"application/pdf"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/tiff", "image/bmp"}
ALLOWED_TYPES = ALLOWED_PDF_TYPES | ALLOWED_IMAGE_TYPES


@router.post("/upload")
async def upload_drawing(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload engineering drawing (PDF or image) and extract parameters.

    Supports: PDF, JPEG, PNG, TIFF, BMP

    Returns extracted parameters, OCR results, and diagram analysis.
    """
    content_type = file.content_type or ""

    # Determine file type from extension if content_type is generic
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    is_pdf = content_type in ALLOWED_PDF_TYPES or ext == ".pdf"
    is_image = content_type in ALLOWED_IMAGE_TYPES or ext in {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}

    if not is_pdf and not is_image:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{content_type}'. "
                   f"Supported: PDF, JPEG, PNG, TIFF, BMP"
        )

    try:
        # Read and save file
        contents = await file.read()
        os.makedirs("./uploads", exist_ok=True)
        filepath = f"./uploads/{datetime.now().timestamp()}_{filename}"
        with open(filepath, "wb") as f:
            f.write(contents)

        # ── Phase 1: Extract text + images ──
        if is_pdf:
            extracted_data = pdf_processor.process_pdf(filepath)
        else:
            extracted_data = pdf_processor.process_image(filepath)

        # ── Phase 2: Extract parameters using ML ──
        parameters = ml_service.extract_parameters(extracted_data)

        # ── Phase 3: OpenCV diagram analysis ──
        diagram_analysis = ml_service.analyze_diagram(extracted_data)

        # Get OCR result
        ocr_result = extracted_data.get("ocr_result", {})
        ocr_confidence = ocr_result.get("confidence_score", 0.0)

        # Create estimation record
        estimation = Estimation(
            filename=filename,
            dimensions=parameters.dimensions.dict(),
            material_type=parameters.material_type,
            surface_finish=parameters.surface_finish,
            tolerances=parameters.tolerances,
            geometric_features=parameters.geometric_features,
            confidence_score=ocr_confidence
        )

        db.add(estimation)
        db.commit()
        db.refresh(estimation)

        logger.info(f"Successfully processed drawing: {filename}")

        return {
            "status": "success",
            "estimation_id": estimation.id,
            "filename": filename,
            "extracted_parameters": parameters.dict(),
            "ocr_result": {
                "confidence_score": ocr_confidence,
                "dimensions_found": len(ocr_result.get("dimensions", [])),
                "thread_specs": ocr_result.get("thread_specs", []),
                "surface_finish_specs": ocr_result.get("surface_finish_specs", []),
                "material_info": ocr_result.get("material_info"),
                "weight_info": ocr_result.get("weight_info"),
                "part_number": ocr_result.get("part_number"),
            },
            "diagram_analysis": diagram_analysis,
            "message": "Drawing processed successfully. Parameters extracted."
        }

    except Exception as e:
        logger.exception(f"Error processing drawing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing drawing: {str(e)}")


@router.post("/estimate/{estimation_id}")
async def generate_estimate(
    estimation_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate cost estimation for an uploaded drawing.

    Returns both formula-based and ML-predicted costs with comparison.
    """
    try:
        estimation = db.query(Estimation).filter(Estimation.id == estimation_id).first()
        if not estimation:
            raise HTTPException(status_code=404, detail="Estimation not found")

        # Extract parameters
        dimensions = estimation.dimensions
        material_type = estimation.material_type
        geometric_features = estimation.geometric_features
        tolerances = estimation.tolerances or {"general": 0.1, "critical": 0.05, "surface": 0.01}
        surface_finish = estimation.surface_finish or "machined"

        logger.info(f"Estimation {estimation_id} dimensions: {dimensions}, type: {type(dimensions)}")
        logger.info(f"Material: {material_type}, Features: {geometric_features}")

        # ── Identify manufacturing operations ──
        try:
            operations = ml_service.identify_operations(
                dimensions,
                material_type,
                geometric_features
            )
        except Exception as e:
            logger.exception(f"Error in identify_operations: {str(e)}")
            if material_type and "steel" in material_type.lower():
                operations = ["turning", "grinding", "deburring"]
            else:
                operations = ["turning", "milling", "drilling"]

        # ── Formula-based cost estimation ──
        cycle_time = cost_calculator.estimate_cycle_time(operations, dimensions)
        logger.info(f"Estimated cycle time: {cycle_time} (type: {type(cycle_time)})")

        costs = cost_calculator.calculate_costs(
            material_type=material_type,
            operations=operations,
            cycle_time=cycle_time,
            dimensions=dimensions
        )
        logger.info(f"Calculated costs: {costs}")

        # ── XGBoost ML prediction ──
        ml_prediction = ml_service.predict_cost(
            dimensions=dimensions,
            material_type=material_type,
            tolerances=tolerances,
            surface_finish=surface_finish,
            operations=operations,
            diagram_analysis=None  # Would need to re-analyze; use cached if available
        )

        # ── Update estimation record ──
        try:
            estimation.raw_material_cost = float(costs.get("raw_material_cost", 0.0))
            estimation.machining_cost = float(costs.get("machining_cost", 0.0))
            estimation.manpower_cost = float(costs.get("manpower_cost", 0.0))
            estimation.overhead_cost = float(costs.get("overhead_cost", 0.0))
            estimation.logistics_cost = float(costs.get("logistics_cost", 0.0))
            estimation.profit_margin = float(costs.get("profit_margin", 0.0))
            estimation.total_cost = float(costs.get("total_cost", 0.0))
        except Exception as e:
            logger.exception(f"Error converting costs to float: {str(e)}")
            raise

        estimation.estimated_cycle_time = float(cycle_time)
        estimation.manufacturing_operations = operations
        estimation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(estimation)

        logger.info(f"Cost estimation completed for ID: {estimation_id}")

        return {
            "status": "success",
            "estimation_id": estimation.id,
            "cost_breakdown": {
                "raw_material_cost": estimation.raw_material_cost,
                "machining_cost": estimation.machining_cost,
                "manpower_cost": estimation.manpower_cost,
                "overhead_cost": estimation.overhead_cost,
                "logistics_cost": estimation.logistics_cost,
                "subtotal": (estimation.raw_material_cost or 0.0) +
                            (estimation.machining_cost or 0.0) +
                            (estimation.manpower_cost or 0.0) +
                            (estimation.overhead_cost or 0.0) +
                            (estimation.logistics_cost or 0.0),
                "profit_margin": estimation.profit_margin,
                "total_cost": estimation.total_cost
            },
            "ml_prediction": {
                "predicted_cost": ml_prediction.get("predicted_cost", 0.0),
                "confidence_lower": ml_prediction.get("confidence_lower", 0.0),
                "confidence_upper": ml_prediction.get("confidence_upper", 0.0),
                "model_used": ml_prediction.get("model_used", "unknown"),
                "feature_importance": ml_prediction.get("feature_importance", {}),
            },
            "manufacturing_operations": operations,
            "estimated_cycle_time": cycle_time
        }

    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        logger.exception(f"Error generating estimate: {str(e)}")
        logger.error(f"Full traceback:\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Error generating estimate: {str(e)}")


@router.get("/history")
async def get_estimation_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get estimation history."""
    try:
        estimations = db.query(Estimation).offset(skip).limit(limit).all()
        total = db.query(Estimation).count()

        return {
            "status": "success",
            "total": total,
            "estimations": [
                {
                    "id": e.id,
                    "filename": e.filename,
                    "total_cost": e.total_cost,
                    "material_type": e.material_type,
                    "upload_date": e.upload_date,
                    "estimated_cycle_time": e.estimated_cycle_time
                }
                for e in estimations
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving history")


@router.get("/{estimation_id}")
async def get_estimation(
    estimation_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed estimation by ID."""
    try:
        estimation = db.query(Estimation).filter(Estimation.id == estimation_id).first()
        if not estimation:
            raise HTTPException(status_code=404, detail="Estimation not found")

        return {
            "status": "success",
            "estimation": {
                "id": estimation.id,
                "filename": estimation.filename,
                "extracted_parameters": {
                    "dimensions": estimation.dimensions,
                    "material_type": estimation.material_type,
                    "tolerances": estimation.tolerances,
                    "geometric_features": estimation.geometric_features
                },
                "cost_breakdown": {
                    "raw_material_cost": estimation.raw_material_cost,
                    "machining_cost": estimation.machining_cost,
                    "manpower_cost": estimation.manpower_cost,
                    "overhead_cost": estimation.overhead_cost,
                    "logistics_cost": estimation.logistics_cost,
                    "profit_margin": estimation.profit_margin,
                    "total_cost": estimation.total_cost
                },
                "manufacturing_operations": estimation.manufacturing_operations,
                "estimated_cycle_time": estimation.estimated_cycle_time,
                "confidence_score": estimation.confidence_score,
                "upload_date": estimation.upload_date
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving estimation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving estimation")
