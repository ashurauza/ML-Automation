"""
PDF processing service for extracting text and images from engineering drawings.

Enhanced pipeline:
1. Extract text via pdfplumber (tables, raw text)
2. Convert pages to images via pdf2image
3. Preprocess images (grayscale, denoise, threshold) for clean OCR
4. Multi-pass OCR with engineering-specific patterns
5. Extract dimensions, tolerances, GD&T, thread specs, title block data
"""
# Deferred imports for pdfplumber, pdf2image, pytesseract to fix startup hangs
# import pdfplumber
# from pdf2image import convert_from_path
# import pytesseract
import logging
from typing import Dict, List, Any, Optional
import numpy as np
from PIL import Image
import cv2
from services.opencv_service import OpenCVService
import re
import io

logger = logging.getLogger(__name__)


class OCRResult:
    """Structured OCR extraction results with confidence tracking."""

    def __init__(self):
        self.raw_text: str = ""
        self.dimensions: List[Dict[str, Any]] = []
        self.tolerances: List[Dict[str, Any]] = []
        self.thread_specs: List[str] = []
        self.surface_finish_specs: List[str] = []
        self.gdt_callouts: List[str] = []
        self.material_info: Optional[str] = None
        self.weight_info: Optional[str] = None
        self.part_number: Optional[str] = None
        self.title_block_text: str = ""
        self.confidence_score: float = 0.0
        self.page_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "dimensions": self.dimensions,
            "tolerances": self.tolerances,
            "thread_specs": self.thread_specs,
            "surface_finish_specs": self.surface_finish_specs,
            "gdt_callouts": self.gdt_callouts,
            "material_info": self.material_info,
            "weight_info": self.weight_info,
            "part_number": self.part_number,
            "title_block_text": self.title_block_text,
            "confidence_score": self.confidence_score,
            "page_count": self.page_count,
        }


class PDFProcessor:
    """Process PDF engineering drawings and extract content with enhanced OCR."""

    def __init__(self):
        self.logger = logger

        # Engineering dimension patterns
        self._dim_patterns = [
            # Standard dimensions: "10 mm", "25.5 cm", "1.5 in"
            re.compile(r'(\d+\.?\d*)\s*(mm|cm|in|inches|")', re.IGNORECASE),
            # Diameter: "Ø10", "⌀25.5", "ø 3.4"
            re.compile(r'[Øø⌀]\s*(\d+\.?\d*)', re.IGNORECASE),
            # Dimension with tolerance: "25 ±0.1"
            re.compile(r'(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)', re.IGNORECASE),
            # R-notation (radius): "R25", "R 12.5"
            re.compile(r'R\s*(\d+\.?\d*)', re.IGNORECASE),
            # Plain numbers that look like dimensions (2+ digits, on their own)
            re.compile(r'(?<!\w)(\d{2,}\.?\d*)(?!\w)', re.IGNORECASE),
        ]

        # Thread specification patterns
        self._thread_patterns = [
            # Metric threads: "M10", "M12x1.5", "M8 x 1.25"
            re.compile(r'M(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)', re.IGNORECASE),
            re.compile(r'M(\d+\.?\d*)', re.IGNORECASE),
            # THRU holes: "2X Ø3.4 THRU"
            re.compile(r'(\d+)\s*[xX×]\s*[Øø⌀]\s*(\d+\.?\d*)\s*THRU', re.IGNORECASE),
            # Counterbore: "Ø6.5 ↧ 3"
            re.compile(r'[Øø⌀]\s*(\d+\.?\d*)\s*[↧⌴]\s*(\d+\.?\d*)', re.IGNORECASE),
        ]

        # GD&T / surface finish patterns
        self._surface_patterns = [
            # Ra values: "Ra3.2", "Ra 1.6"
            re.compile(r'Ra\s*(\d+\.?\d*)', re.IGNORECASE),
            # Rz values: "Rz12.5"
            re.compile(r'Rz\s*(\d+\.?\d*)', re.IGNORECASE),
        ]

        # Tolerance patterns
        self._tolerance_patterns = [
            # ±0.05
            re.compile(r'[±]\s*(\d+\.?\d*)'),
            # +0.1/-0.05
            re.compile(r'\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)'),
            # Tolerance class: "H7", "g6", "IT7"
            re.compile(r'(?:IT)?([A-Za-z])(\d{1,2})', re.IGNORECASE),
        ]

    def process_pdf(self, filepath: str) -> Dict[str, Any]:
        """
        Process PDF and extract text, images, and structured data.

        Enhanced pipeline:
        1. pdfplumber for native text/table extraction
        2. pdf2image → OpenCV preprocessing → Tesseract OCR
        3. Engineering-specific pattern extraction

        Args:
            filepath: Path to PDF file

        Returns:
            Dictionary containing extracted content + OCR results
        """
        try:
            ocr_result = OCRResult()
            extracted_data = {
                "text_content": "",
                "images": [],
                "tables": [],
                "dimensions": [],
                "annotations": [],
                "pil_images": [],  # Store PIL images for OpenCV analysis
                "diagram_count": 0,
                "diagram_area_ratio": 0.0,
                "line_density": 0.0,
                "diagram_images": []
            }

            # ── Phase 1: Extract text via pdfplumber ──
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                ocr_result.page_count = len(pdf.pages)
                for page_idx, page in enumerate(pdf.pages):
                    # Extract native text
                    text = page.extract_text()
                    if text:
                        extracted_data["text_content"] += (
                            f"\n--- Page {page_idx + 1} ---\n{text}"
                        )

                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        extracted_data["tables"].extend(tables)

            # ── Phase 2: Image-based OCR with preprocessing ──
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(filepath, dpi=150)
            except Exception as e:
                self.logger.warning(
                    f"pdf2image failed (poppler not installed?): {e}. "
                    "Falling back to text-only extraction."
                )
                images = []

            for img_idx, pil_image in enumerate(images):
                # Store PIL image for later OpenCV analysis
                extracted_data["pil_images"].append(pil_image)

                # Preprocess for OCR
                preprocessed = self._preprocess_for_ocr(pil_image)

                # Multi-pass OCR
                ocr_text = self._multi_pass_ocr(preprocessed, pil_image)

                if ocr_text:
                    extracted_data["text_content"] += (
                        f"\n--- OCR Page {img_idx + 1} ---\n{ocr_text}"
                    )
                    ocr_result.raw_text += ocr_text

                # Convert PIL Image to OpenCV BGR numpy array
                img_np = np.array(pil_image)
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                
                # Detect diagrams using OpenCV
                opencv_results = OpenCVService.detect_diagrams(img_cv, img_idx + 1, "./uploads")
                
                # Accumulate OpenCV results
                extracted_data["diagram_count"] += opencv_results["diagram_count"]
                extracted_data["diagram_area_ratio"] = max(extracted_data["diagram_area_ratio"], opencv_results["diagram_area_ratio"])
                extracted_data["line_density"] = (extracted_data["line_density"] * img_idx + opencv_results["line_density"]) / (img_idx + 1)
                extracted_data["diagram_images"].extend(opencv_results["diagram_images"])

                # Save image metadata
                extracted_data["images"].append({
                    "page": img_idx + 1,
                    "width": pil_image.width,
                    "height": pil_image.height,
                })

            # Round off accumulated visual stats
            extracted_data["diagram_area_ratio"] = round(extracted_data["diagram_area_ratio"], 4)
            extracted_data["line_density"] = round(extracted_data["line_density"], 4)

            # ── Phase 3: Engineering-specific extraction ──
            full_text = extracted_data["text_content"]

            # Extract dimensions
            dims = self._extract_dimensions_enhanced(full_text)
            extracted_data["dimensions"] = dims
            ocr_result.dimensions = dims

            # Extract thread specifications
            ocr_result.thread_specs = self._extract_thread_specs(full_text)

            # Extract surface finish / GD&T
            ocr_result.surface_finish_specs = self._extract_surface_specs(full_text)
            ocr_result.gdt_callouts = self._extract_gdt_callouts(full_text)

            # Extract tolerances
            ocr_result.tolerances = self._extract_tolerance_specs(full_text)

            # Extract title block info (material, weight, part number)
            self._extract_title_block_info(full_text, ocr_result)

            # Compute confidence score
            ocr_result.confidence_score = self._compute_ocr_confidence(ocr_result)

            # Add OCR result to extracted data
            extracted_data["ocr_result"] = ocr_result.to_dict()

            self.logger.info(
                f"PDF processed: {filepath} | "
                f"{len(dims)} dimensions, "
                f"{len(ocr_result.thread_specs)} threads, "
                f"confidence={ocr_result.confidence_score:.2f}"
            )

            return extracted_data

        except Exception as e:
            self.logger.error(f"Error processing PDF {filepath}: {str(e)}")
            raise Exception(f"PDF processing error: {str(e)}")

    def process_image(self, filepath: str) -> Dict[str, Any]:
        """
        Process a direct image upload (JPEG/PNG) instead of PDF.

        Args:
            filepath: Path to image file

        Returns:
            Dictionary containing extracted content
        """
        try:
            pil_image = Image.open(filepath)
            ocr_result = OCRResult()
            ocr_result.page_count = 1

            extracted_data = {
                "text_content": "",
                "images": [{"page": 1, "width": pil_image.width, "height": pil_image.height}],
                "tables": [],
                "dimensions": [],
                "annotations": [],
                "pil_images": [pil_image],
            }

            # Preprocess + OCR
            preprocessed = self._preprocess_for_ocr(pil_image)
            ocr_text = self._multi_pass_ocr(preprocessed, pil_image)
            extracted_data["text_content"] = ocr_text or ""
            ocr_result.raw_text = ocr_text or ""

            # Extract all engineering data
            dims = self._extract_dimensions_enhanced(ocr_text or "")
            extracted_data["dimensions"] = dims
            ocr_result.dimensions = dims
            ocr_result.thread_specs = self._extract_thread_specs(ocr_text or "")
            ocr_result.surface_finish_specs = self._extract_surface_specs(ocr_text or "")
            ocr_result.tolerances = self._extract_tolerance_specs(ocr_text or "")
            self._extract_title_block_info(ocr_text or "", ocr_result)
            ocr_result.confidence_score = self._compute_ocr_confidence(ocr_result)

            extracted_data["ocr_result"] = ocr_result.to_dict()
            return extracted_data

        except Exception as e:
            self.logger.error(f"Error processing image {filepath}: {str(e)}")
            raise Exception(f"Image processing error: {str(e)}")

    # ─── Image Preprocessing ───────────────────────────────────────

    def _preprocess_for_ocr(self, pil_image: Image.Image) -> Image.Image:
        """
        Preprocess image for optimal OCR accuracy.

        Pipeline: RGB→Gray → Gaussian blur → Adaptive threshold →
                  Morphological denoise → Dilation for text connectivity
        """
        # Convert to OpenCV format
        img_array = np.array(pil_image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Step 1: Denoise
        denoised = cv2.GaussianBlur(gray, (3, 3), 0)

        # Step 2: Adaptive thresholding for varying illumination
        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,
            C=10
        )

        # Step 3: Morphological operations to clean text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Step 4: Slight dilation to connect broken characters
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        dilated = cv2.dilate(cleaned, kernel_dilate, iterations=1)

        # Convert back to PIL
        return Image.fromarray(dilated)

    def _multi_pass_ocr(
        self, preprocessed: Image.Image, original: Image.Image
    ) -> str:
        """
        Multi-pass OCR with different Tesseract page segmentation modes.

        Pass 1: PSM 6 (uniform block of text) — good for title blocks
        Pass 2: PSM 11 (sparse text) — good for dimension callouts
        Pass 3: PSM 3 (fully automatic) on original — catches what others miss
        """
        combined_text = ""
        seen_lines = set()

        ocr_configs = [
            ("--psm 3 --oem 3", original, "auto"),
        ]

        import pytesseract
        for config, image, pass_name in ocr_configs:
            try:
                text = pytesseract.image_to_string(image, config=config)
                if text:
                    # Deduplicate lines across passes
                    for line in text.strip().split("\n"):
                        line_clean = line.strip()
                        if line_clean and line_clean not in seen_lines:
                            seen_lines.add(line_clean)
                            combined_text += line_clean + "\n"
            except Exception as e:
                self.logger.warning(f"OCR pass '{pass_name}' failed: {e}")

        return combined_text.strip()

    # ─── Engineering Pattern Extraction ─────────────────────────────

    def _extract_dimensions_enhanced(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract dimension values with engineering-aware patterns.

        Handles: standard dims (10 mm), diameters (Ø10), radii (R25),
        toleranced dims (25 ±0.1), and plain numeric callouts.
        """
        dimensions = []
        if not text:
            return dimensions

        seen_values = set()

        # Pattern 1: Standard dimensions with units
        for match in self._dim_patterns[0].finditer(text):
            val = float(match.group(1))
            unit = match.group(2).lower().replace('"', 'in')
            key = (val, unit)
            if key not in seen_values and val > 0:
                seen_values.add(key)
                dimensions.append({
                    "value": val, "unit": unit, "type": "linear"
                })

        # Pattern 2: Diameter notation
        for match in self._dim_patterns[1].finditer(text):
            val = float(match.group(1))
            key = (val, "diameter")
            if key not in seen_values and val > 0:
                seen_values.add(key)
                dimensions.append({
                    "value": val, "unit": "mm", "type": "diameter"
                })

        # Pattern 3: Toleranced dimensions
        for match in self._dim_patterns[2].finditer(text):
            val = float(match.group(1))
            tol = float(match.group(2))
            key = (val, "toleranced")
            if key not in seen_values and val > 0:
                seen_values.add(key)
                dimensions.append({
                    "value": val, "unit": "mm", "type": "toleranced",
                    "tolerance": tol
                })

        # Pattern 4: Radius notation
        for match in self._dim_patterns[3].finditer(text):
            val = float(match.group(1))
            key = (val, "radius")
            if key not in seen_values and val > 0:
                seen_values.add(key)
                dimensions.append({
                    "value": val, "unit": "mm", "type": "radius"
                })

        return dimensions

    def _extract_thread_specs(self, text: str) -> List[str]:
        """Extract thread specifications (M10x1.5, 2X Ø3.4 THRU, etc.)."""
        specs = []
        if not text:
            return specs

        for pattern in self._thread_patterns:
            for match in pattern.finditer(text):
                spec = match.group(0).strip()
                if spec not in specs:
                    specs.append(spec)

        return specs

    def _extract_surface_specs(self, text: str) -> List[str]:
        """Extract surface finish specifications (Ra3.2, Rz12.5)."""
        specs = []
        if not text:
            return specs

        for pattern in self._surface_patterns:
            for match in pattern.finditer(text):
                specs.append(match.group(0).strip())

        return specs

    def _extract_gdt_callouts(self, text: str) -> List[str]:
        """Extract GD&T related callouts."""
        callouts = []
        if not text:
            return callouts

        # Common GD&T keywords
        gdt_keywords = [
            "flatness", "parallelism", "perpendicularity",
            "concentricity", "circularity", "cylindricity",
            "true position", "runout", "angularity",
            "third angle projection", "first angle projection",
        ]

        text_lower = text.lower()
        for keyword in gdt_keywords:
            if keyword in text_lower:
                callouts.append(keyword)

        return callouts

    def _extract_tolerance_specs(self, text: str) -> List[Dict[str, Any]]:
        """Extract tolerance values and classes."""
        tolerances = []
        if not text:
            return tolerances

        # ±value tolerances
        for match in self._tolerance_patterns[0].finditer(text):
            tolerances.append({
                "type": "symmetric",
                "value": float(match.group(1)),
                "notation": f"±{match.group(1)}"
            })

        # +value/-value tolerances
        for match in self._tolerance_patterns[1].finditer(text):
            tolerances.append({
                "type": "asymmetric",
                "upper": float(match.group(1)),
                "lower": float(match.group(2)),
                "notation": f"+{match.group(1)}/-{match.group(2)}"
            })

        return tolerances

    def _extract_title_block_info(self, text: str, ocr_result: OCRResult) -> None:
        """
        Extract title block information: material, weight, part number.

        Looks for patterns like:
        - "ASTM A927 T410" (material spec)
        - "WEIGHT: 0.023 KG"
        - "DRG. NO: PVC101010200"
        """
        if not text:
            return

        text_lower = text.lower()

        # Material spec patterns
        material_patterns = [
            re.compile(r'ASTM\s+[A-Z]?\d+[A-Za-z\s]*', re.IGNORECASE),
            re.compile(r'(?:MATERIAL|MAT)[:\s]+([A-Za-z0-9\s]+)', re.IGNORECASE),
            re.compile(r'(?:EN|DIN|ISO|AISI|SAE)\s+\d+[\w\s-]*', re.IGNORECASE),
        ]

        for pattern in material_patterns:
            match = pattern.search(text)
            if match:
                ocr_result.material_info = match.group(0).strip()
                break

        # Weight pattern
        weight_match = re.search(
            r'WEIGHT[:\s]*(\d+\.?\d*)\s*(KG|G|LBS?)',
            text, re.IGNORECASE
        )
        if weight_match:
            ocr_result.weight_info = weight_match.group(0).strip()

        # Part number
        part_patterns = [
            re.compile(r'(?:DRG|PART|P/N|PN)[.\s:NO]*\s*([A-Z0-9-]+)', re.IGNORECASE),
            re.compile(r'(?:DRAWING\s+NO|DWG\s+NO)[.\s:]*\s*([A-Z0-9-]+)', re.IGNORECASE),
        ]
        for pattern in part_patterns:
            match = pattern.search(text)
            if match:
                ocr_result.part_number = match.group(1).strip()
                break

    # ─── Confidence Scoring ─────────────────────────────────────────

    def _compute_ocr_confidence(self, ocr_result: OCRResult) -> float:
        """
        Compute a confidence score (0.0–1.0) based on what was extracted.

        Higher confidence when more structured data is found.
        """
        score = 0.0
        max_score = 0.0

        # Dimensions found (most important)
        max_score += 40
        if len(ocr_result.dimensions) >= 3:
            score += 40
        elif len(ocr_result.dimensions) >= 1:
            score += 20

        # Material detected
        max_score += 20
        if ocr_result.material_info:
            score += 20

        # Thread specs found
        max_score += 10
        if ocr_result.thread_specs:
            score += 10

        # Surface finish found
        max_score += 10
        if ocr_result.surface_finish_specs:
            score += 10

        # Tolerances found
        max_score += 10
        if ocr_result.tolerances:
            score += 10

        # Weight found
        max_score += 5
        if ocr_result.weight_info:
            score += 5

        # Part number found
        max_score += 5
        if ocr_result.part_number:
            score += 5

        return round(score / max(max_score, 1), 2)

    # ─── Legacy compatibility ───────────────────────────────────────

    def _extract_dimensions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Legacy dimension extraction (kept for backward compatibility).
        Now delegates to the enhanced version.
        """
        return self._extract_dimensions_enhanced(text)
