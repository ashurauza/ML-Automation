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
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import os
import io
import pandas as pd
import logging
from datetime import datetime
from database import get_db
from models import Estimation, ExtractedParameters, CostBreakdown, User, UserCostSettings
from services.pdf_processor import PDFProcessor
from services.cost_calculator import CostCalculator
from services.ml_service import MLService
from services.excel_exporter import generate_complex_excel
from routes.auth import get_current_user

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
def upload_drawing(
    files: List[UploadFile] = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload engineering drawings (PDFs or images) and extract parameters as a single assembly.

    Supports: PDF, JPEG, PNG, TIFF, BMP

    Returns extracted parameters, OCR results, and diagram analysis.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    aggregated_dimensions = {}
    primary_material = None
    aggregated_features = []
    aggregated_diagram_count = 0
    max_diagram_area_ratio = 0.0
    aggregated_line_density = 0.0
    aggregated_diagram_images = []
    min_confidence_score = 1.0
    
    # Diagram analysis metrics
    total_hole_count = 0
    total_slot_count = 0
    total_fillet_count = 0
    
    filenames = []
    file_breakdown = []
    all_thread_specs = []
    all_surface_finish_specs = []

    for file in files:
        content_type = file.content_type or ""
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()
        filenames.append(filename)

        is_pdf = content_type in ALLOWED_PDF_TYPES or ext == ".pdf"
        is_image = content_type in ALLOWED_IMAGE_TYPES or ext in {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}

        if not is_pdf and not is_image:
            logger.warning(f"Unsupported file type: {filename}. Skipping.")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}. Please upload a PDF or image.")

        try:
            # Read and save file
            contents = file.file.read()
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
            
            # ── Store Individual Sub-Component Breakdown ──
            file_breakdown.append({
                "filename": filename,
                "material": parameters.material_type or "Unknown",
                "dimensions": f"{parameters.dimensions.length}x{parameters.dimensions.width} mm",
                "holes": diagram_analysis.get("hole_count", 0),
                "slots": diagram_analysis.get("slot_count", 0)
            })

            # ── Aggregation Logic ──
            # Dimensions: We will merge dictionaries. For scalar bounds like length, add them up for an assembly scale.
            if "length" in parameters.dimensions.dict() and parameters.dimensions.length:
                aggregated_dimensions["length"] = aggregated_dimensions.get("length", 0) + parameters.dimensions.length
            if "width" in parameters.dimensions.dict() and parameters.dimensions.width:
                aggregated_dimensions["width"] = max(aggregated_dimensions.get("width", 0), parameters.dimensions.width)
            if "height" in parameters.dimensions.dict() and parameters.dimensions.height:
                aggregated_dimensions["height"] = max(aggregated_dimensions.get("height", 0), parameters.dimensions.height)

            if not primary_material and parameters.material_type:
                primary_material = parameters.material_type
                
            if parameters.geometric_features:
                aggregated_features.extend(parameters.geometric_features)

            aggregated_diagram_count += parameters.diagram_count
            max_diagram_area_ratio = max(max_diagram_area_ratio, parameters.diagram_area_ratio)
            aggregated_line_density += parameters.line_density
            
            # Aggregate OpenCV analysis counts
            total_hole_count += diagram_analysis.get("hole_count", 0)
            total_slot_count += diagram_analysis.get("slot_count", 0)
            total_fillet_count += diagram_analysis.get("fillet_count", 0)
            
            if parameters.diagram_images:
                aggregated_diagram_images.extend(parameters.diagram_images)
                
            min_confidence_score = min(min_confidence_score, ocr_confidence)
            all_thread_specs.extend(ocr_result.get("thread_specs", []))
            all_surface_finish_specs.extend(ocr_result.get("surface_finish_specs", []))

        except Exception as e:
            logger.exception(f"Error processing file {filename}: {str(e)}")
            error_msg = str(e).replace("Parameter extraction error: ", "")
            raise HTTPException(status_code=400, detail=f"Failed to process {filename}: {error_msg}")

    if not file_breakdown:
        raise HTTPException(status_code=400, detail="No valid files successfully processed.")

    try:
        # Create a single estimation record for the assembly
        estimation = Estimation(
            user_id=current_user.id,
            filename=f"Assembly ({len(filenames)} files)",
            dimensions=aggregated_dimensions,
            material_type=primary_material or "steel",
            surface_finish="machined", # Defaulting for assembly
            tolerances={"general": 0.1, "critical": 0.05, "surface": 0.01},
            geometric_features=list(set(aggregated_features)),
            confidence_score=min_confidence_score,
            diagram_count=aggregated_diagram_count,
            diagram_area_ratio=max_diagram_area_ratio,
            line_density=aggregated_line_density / len(filenames),
            diagram_images=aggregated_diagram_images,
            diagram_analysis={
                "note": f"Aggregated from {len(filenames)} files",
                "hole_count": total_hole_count,
                "slot_count": total_slot_count,
                "fillet_count": total_fillet_count,
                "aspect_ratio": 1.5,  # Standard aspect ratio for assembly visual
                "file_breakdown": file_breakdown
            }
        )

        db.add(estimation)
        db.commit()
        db.refresh(estimation)

        logger.info(f"Successfully processed assembly of {len(filenames)} drawings")

        response_data = {
            "status": "success",
            "estimation_id": estimation.id,
            "filename": f"Assembly ({len(filenames)} files)",
            "extracted_parameters": {
                "dimensions": aggregated_dimensions,
                "material_type": primary_material or "steel",
                "diagram_count": aggregated_diagram_count
            },
            "ocr_result": {
                "confidence_score": float(min_confidence_score or 0.0),
                "thread_specs": list(set(all_thread_specs)),
                "surface_finish_specs": list(set(all_surface_finish_specs)),
                "material_info": primary_material,
            },
            "message": "Assembly drawings processed successfully."
        }

        return JSONResponse(content=jsonable_encoder(response_data))

    except Exception as e:
        logger.exception(f"Error saving assembly estimation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving assembly estimation: {str(e)}")


@router.post("/estimate/{estimation_id}")
def generate_estimate(
    estimation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate cost estimation for an uploaded drawing.

    Returns both formula-based and ML-predicted costs with comparison.
    """
    try:
        estimation = db.query(Estimation).filter(Estimation.id == estimation_id, Estimation.user_id == current_user.id).first()
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

        # Fetch user settings
        user_settings_record = db.query(UserCostSettings).filter(UserCostSettings.user_id == current_user.id).first()
        user_settings_dict = {}
        if user_settings_record:
            user_settings_dict = {
                "material_cost_multiplier": user_settings_record.material_cost_multiplier,
                "machining_rate": user_settings_record.machining_rate,
                "labor_rate": user_settings_record.labor_rate,
                "overhead_percentage": user_settings_record.overhead_percentage,
                "profit_margin": user_settings_record.profit_margin
            }

        costs = cost_calculator.calculate_costs(
            material_type=material_type,
            operations=operations,
            cycle_time=cycle_time,
            dimensions=dimensions,
            user_settings=user_settings_dict
        )
        logger.info(f"Calculated costs: {costs}")

        # ── XGBoost ML prediction ──
        ml_prediction = ml_service.predict_cost(
            dimensions=dimensions,
            material_type=material_type,
            tolerances=tolerances,
            surface_finish=surface_finish,
            operations=operations,
            diagram_analysis=estimation.diagram_analysis
        )

        # Scale formula costs to match XGBoost prediction if model is loaded
        if ml_prediction.get("model_used") == "xgboost" and ml_prediction.get("predicted_cost", 0.0) > 0:
            xgb_total = ml_prediction["predicted_cost"]
            formula_total = float(costs.get("total_cost", 0.0))
            if formula_total > 0:
                scale = xgb_total / formula_total
                costs = {k: round(v * scale, 2) for k, v in costs.items()}
                # Ensure total is exactly the predicted cost
                costs["total_cost"] = xgb_total

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
        
        diagram_analysis = dict(estimation.diagram_analysis) if estimation.diagram_analysis else {}
        diagram_analysis["ml_details"] = ml_prediction
        estimation.diagram_analysis = diagram_analysis
        
        estimation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(estimation)

        logger.info(f"Cost estimation completed for ID: {estimation_id}")

        response_data = {
            "status": "success",
            "estimation_id": estimation.id,
            "cost_breakdown": {
                "raw_material_cost": float(estimation.raw_material_cost or 0.0),
                "machining_cost": float(estimation.machining_cost or 0.0),
                "manpower_cost": float(estimation.manpower_cost or 0.0),
                "overhead_cost": float(estimation.overhead_cost or 0.0),
                "logistics_cost": float(estimation.logistics_cost or 0.0),
                "subtotal": float(
                    (estimation.raw_material_cost or 0.0) +
                    (estimation.machining_cost or 0.0) +
                    (estimation.manpower_cost or 0.0) +
                    (estimation.overhead_cost or 0.0) +
                    (estimation.logistics_cost or 0.0)
                ),
                "profit_margin": float(estimation.profit_margin or 0.0),
                "total_cost": float(estimation.total_cost or 0.0)
            },
            "ml_prediction": {
                "predicted_cost": float(ml_prediction.get("predicted_cost", 0.0)),
                "confidence_lower": float(ml_prediction.get("confidence_lower", 0.0)),
                "confidence_upper": float(ml_prediction.get("confidence_upper", 0.0)),
                "model_used": ml_prediction.get("model_used", "unknown"),
                "feature_importance": ml_prediction.get("feature_importance", {}),
            },
            "manufacturing_operations": operations,
            "estimated_cycle_time": float(cycle_time)
        }

        return JSONResponse(content=jsonable_encoder(response_data))

    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        logger.exception(f"Error generating estimate: {str(e)}")
        logger.error(f"Full traceback:\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Error generating estimate: {str(e)}")


@router.get("/history")
def get_estimation_history(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get estimation history."""
    try:
        estimations = db.query(Estimation).filter(Estimation.user_id == current_user.id).order_by(Estimation.upload_date.desc()).offset(skip).limit(limit).all()
        total = db.query(Estimation).filter(Estimation.user_id == current_user.id).count()

        return {
            "status": "success",
            "total": total,
            "estimations": [
                {
                    "id": e.id,
                    "filename": e.filename,
                    "total_cost": e.total_cost,
                    "material_type": e.material_type,
                    "upload_date": e.upload_date.isoformat() + "Z" if e.upload_date else None,
                    "estimated_cycle_time": e.estimated_cycle_time
                }
                for e in estimations
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving history")


@router.get("/{estimation_id}")
def get_estimation(
    estimation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed estimation by ID."""
    try:
        estimation = db.query(Estimation).filter(Estimation.id == estimation_id, Estimation.user_id == current_user.id).first()
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
                    "geometric_features": estimation.geometric_features,
                    "diagram_count": estimation.diagram_count,
                    "diagram_area_ratio": estimation.diagram_area_ratio,
                    "line_density": estimation.line_density,
                    "diagram_images": estimation.diagram_images,
                    "diagram_analysis": estimation.diagram_analysis
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
                "upload_date": estimation.upload_date.isoformat() + "Z" if estimation.upload_date else None,
                "ml_prediction": {
                    "predicted_cost": float(estimation.diagram_analysis.get("ml_details", {}).get("predicted_cost", 0.0)) if estimation.diagram_analysis else 0.0,
                    "confidence_lower": float(estimation.diagram_analysis.get("ml_details", {}).get("confidence_lower", 0.0)) if estimation.diagram_analysis else 0.0,
                    "confidence_upper": float(estimation.diagram_analysis.get("ml_details", {}).get("confidence_upper", 0.0)) if estimation.diagram_analysis else 0.0,
                    "model_used": estimation.diagram_analysis.get("ml_details", {}).get("model_used", "unknown") if estimation.diagram_analysis else "unknown",
                    "feature_importance": estimation.diagram_analysis.get("ml_details", {}).get("feature_importance", {}) if estimation.diagram_analysis else {},
                } if estimation.diagram_analysis and "ml_details" in estimation.diagram_analysis else None
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving estimation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving estimation")

@router.get("/{estimation_id}/export")
def export_estimation_excel(
    estimation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export estimation to Quotation and BOM Excel sheets."""
    try:
        estimation = db.query(Estimation).filter(
            Estimation.id == estimation_id,
            Estimation.user_id == current_user.id
        ).first()
        if not estimation:
            raise HTTPException(status_code=404, detail="Estimation not found")
            
        # Use custom complex Excel exporter matching Quotation & BOM
        output = generate_complex_excel(estimation)
        
        headers = {
            'Content-Disposition': f'attachment; filename="Quotation_BOM_{estimation_id}.xlsx"'
        }
        
        return StreamingResponse(
            output, 
            headers=headers,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        raise HTTPException(status_code=500, detail="Error exporting to Excel")
