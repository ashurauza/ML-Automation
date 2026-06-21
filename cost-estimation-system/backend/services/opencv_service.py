"""
OpenCV service for detecting diagrams, views, and calculating drawing complexity metrics
"""
import cv2
import numpy as np
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenCVService:
    """Detect diagrams, views, and calculate drawing complexity using OpenCV"""
    
    @staticmethod
    def detect_diagrams(image_np: np.ndarray, page_num: int, output_dir: str = "./uploads") -> dict:
        """
        Processes a page image using OpenCV:
        - Segments the page into drawing regions (views/diagrams) using adaptive thresholding and contour analysis.
        - Crops and saves each detected drawing region as an individual PNG.
        - Calculates drawing metrics: diagram_count, diagram_area_ratio, and line_density.
        
        Args:
            image_np: NumPy array representing the image (in BGR or RGB format)
            page_num: Page index (1-based)
            output_dir: Directory where cropped diagram images will be saved
            
        Returns:
            Dictionary containing:
                - diagram_count: number of detected drawing regions
                - diagram_area_ratio: fraction of page area occupied by diagrams
                - line_density: fraction of page pixels that are drawing lines
                - diagram_images: list of relative URLs to cropped diagrams
        """
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Check image format
            if image_np is None or not isinstance(image_np, np.ndarray):
                logger.warning("Invalid image passed to OpenCVService")
                return OpenCVService._get_default_result()
                
            # Convert to grayscale
            if len(image_np.shape) == 3:
                gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            else:
                gray = image_np.copy()
                # Reconstruct BGR version for saving color crops if needed
                image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
                
            height, width = gray.shape
            total_area = height * width
            
            if total_area == 0:
                return OpenCVService._get_default_result()
                
            # Binarization: Adaptive thresholding works well for engineering drawings with text and lines
            # Using binary inversion so lines and shapes become foreground (255)
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # 1. Line density: percentage of foreground (white) pixels on the page
            fg_pixels = cv2.countNonZero(binary)
            line_density = float(fg_pixels) / float(total_area)
            
            # 2. Dilation to group close drawing components (views, tables, title blocks)
            # Using a rectangular kernel to bridge small gaps between text/lines
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
            dilated = cv2.dilate(binary, kernel, iterations=1)
            
            # 3. Contour Detection
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            diagram_bboxes = []
            cropped_images = []
            
            # Filter criteria: Diagrams should be large enough, but not cover the entire page border
            min_w = int(width * 0.15)      # At least 15% of page width
            min_h = int(height * 0.15)     # At least 15% of page height
            max_area_ratio = 0.92          # Exclude border frames that span >92% area
            
            for idx, cnt in enumerate(contours):
                x, y, w, h = cv2.boundingRect(cnt)
                cnt_area = w * h
                area_ratio = float(cnt_area) / float(total_area)
                
                # Check dimensions and area
                if w >= min_w and h >= min_h and area_ratio <= max_area_ratio:
                    diagram_bboxes.append((x, y, w, h))
                    
                    # Crop the drawing region from the original image
                    cropped = image_np[y:y+h, x:x+w]
                    
                    # Save the cropped image
                    filename = f"diagram_page_{page_num}_crop_{idx}_{int(datetime.now().timestamp())}.png"
                    filepath = os.path.join(output_dir, filename)
                    cv2.imwrite(filepath, cropped)
                    
                    # Store the web-accessible URL path
                    cropped_images.append(f"/uploads/{filename}")
            
            # Fallback if no diagrams were segmented (e.g. single large diagram with no clear boundary)
            if not diagram_bboxes and line_density > 0.005:
                # Crop the center 80% as the main diagram region
                cx = int(width * 0.1)
                cy = int(height * 0.1)
                cw = int(width * 0.8)
                ch = int(height * 0.8)
                diagram_bboxes.append((cx, cy, cw, ch))
                
                cropped = image_np[cy:cy+ch, cx:cx+cw]
                filename = f"diagram_page_{page_num}_full_{int(datetime.now().timestamp())}.png"
                filepath = os.path.join(output_dir, filename)
                cv2.imwrite(filepath, cropped)
                cropped_images.append(f"/uploads/{filename}")
                
            diagram_count = len(diagram_bboxes)
            
            # Calculate total area ratio occupied by diagrams
            total_diagram_area = sum(w * h for x, y, w, h in diagram_bboxes)
            diagram_area_ratio = float(total_diagram_area) / float(total_area)
            
            return {
                "diagram_count": diagram_count,
                "diagram_area_ratio": min(1.0, round(diagram_area_ratio, 4)),
                "line_density": round(line_density, 4),
                "diagram_images": cropped_images
            }
            
        except Exception as e:
            logger.error(f"Error in OpenCV diagram detection: {str(e)}")
            return OpenCVService._get_default_result()
            
    @staticmethod
    def _get_default_result() -> dict:
        """Return a safe dictionary when processing fails"""
        return {
            "diagram_count": 0,
            "diagram_area_ratio": 0.0,
            "line_density": 0.0,
            "diagram_images": []
        }
