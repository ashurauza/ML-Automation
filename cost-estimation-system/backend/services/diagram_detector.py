"""
OpenCV-based diagram detection service for engineering drawings.

Detects geometric shapes (holes, rectangles, arcs), dimension lines,
title blocks, and computes a part complexity score from technical drawings.
"""
import cv2
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class DetectedCircle:
    """A detected circular feature (hole, bore, etc.)."""
    center_x: int
    center_y: int
    radius: int
    estimated_diameter_mm: Optional[float] = None


@dataclass
class DetectedRectangle:
    """A detected rectangular feature (pocket, slot, etc.)."""
    x: int
    y: int
    width: int
    height: int
    angle: float = 0.0


@dataclass
class DetectedLine:
    """A detected line segment (dimension line, edge)."""
    x1: int
    y1: int
    x2: int
    y2: int
    length_px: float = 0.0
    is_horizontal: bool = False
    is_vertical: bool = False


@dataclass
class DiagramAnalysis:
    """Complete analysis results from OpenCV processing."""
    # Detected features
    circles: List[DetectedCircle] = field(default_factory=list)
    rectangles: List[DetectedRectangle] = field(default_factory=list)
    lines: List[DetectedLine] = field(default_factory=list)
    contour_count: int = 0

    # Feature counts
    hole_count: int = 0
    slot_count: int = 0
    pocket_count: int = 0
    fillet_count: int = 0
    chamfer_count: int = 0

    # Complexity metrics
    complexity_score: float = 0.0
    total_contour_area: float = 0.0
    symmetry_score: float = 0.0

    # Region detection
    has_title_block: bool = False
    title_block_region: Optional[Dict[str, int]] = None
    num_drawing_views: int = 0

    # Image metadata
    image_width: int = 0
    image_height: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        result = asdict(self)
        # Convert dataclass lists to dicts
        result["circles"] = [asdict(c) for c in self.circles]
        result["rectangles"] = [asdict(r) for r in self.rectangles]
        result["lines"] = [asdict(l) for l in self.lines]
        return result


class DiagramDetector:
    """
    OpenCV-based detector for engineering drawing features.

    Pipeline:
    1. Preprocess image (grayscale, blur, threshold)
    2. Detect contours and classify shapes
    3. Detect circles (holes) via HoughCircles
    4. Detect lines (dimension lines, edges) via HoughLinesP
    5. Identify title block region
    6. Compute complexity score
    """

    def __init__(self):
        self.logger = logger
        # Minimum contour area to filter noise (in pixels²)
        self.min_contour_area = 100
        # Maximum contour area as fraction of image (filter full-page contours)
        self.max_contour_area_ratio = 0.6

    def analyze_image(self, image: Image.Image) -> DiagramAnalysis:
        """
        Analyze a PIL Image of an engineering drawing.

        Args:
            image: PIL Image object (from pdf2image or direct upload)

        Returns:
            DiagramAnalysis with all detected features
        """
        try:
            # Convert PIL Image to OpenCV format (BGR)
            img_array = np.array(image)
            if len(img_array.shape) == 2:
                # Already grayscale
                gray = img_array
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
            else:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

            h, w = gray.shape[:2]
            analysis = DiagramAnalysis(image_width=w, image_height=h)

            # Step 1: Preprocess
            preprocessed = self._preprocess(gray)

            # Step 2: Detect contours
            contours = self._detect_contours(preprocessed, h, w)
            analysis.contour_count = len(contours)

            # Step 3: Classify contours into shapes
            self._classify_contours(contours, analysis)

            # Step 4: Detect circles via Hough transform
            circles = self._detect_circles(gray)
            analysis.circles.extend(circles)
            analysis.hole_count = len(analysis.circles)

            # Step 5: Detect lines via Hough transform
            lines = self._detect_lines(preprocessed)
            analysis.lines = lines

            # Step 6: Detect title block
            self._detect_title_block(contours, analysis, h, w)

            # Step 7: Estimate number of drawing views
            analysis.num_drawing_views = self._estimate_views(contours, h, w)

            # Step 8: Detect fillets and chamfers from arc-like contours
            self._detect_fillets_chamfers(contours, analysis)

            # Step 9: Compute complexity score
            analysis.complexity_score = self._compute_complexity(analysis)

            # Step 10: Compute symmetry
            analysis.symmetry_score = self._compute_symmetry(preprocessed)

            # Compute total contour area
            analysis.total_contour_area = sum(
                cv2.contourArea(c) for c in contours
            )

            self.logger.info(
                f"Diagram analysis complete: {analysis.hole_count} holes, "
                f"{analysis.slot_count} slots, {analysis.pocket_count} pockets, "
                f"complexity={analysis.complexity_score:.2f}"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing diagram: {str(e)}")
            # Return empty analysis on failure
            return DiagramAnalysis()

    def analyze_from_path(self, image_path: str) -> DiagramAnalysis:
        """Analyze an image from file path."""
        img = Image.open(image_path)
        return self.analyze_image(img)

    # ─── Internal Pipeline Steps ────────────────────────────────────

    def _preprocess(self, gray: np.ndarray) -> np.ndarray:
        """
        Preprocess grayscale image for contour/shape detection.

        Pipeline: Gaussian blur → adaptive threshold → morphological close
        """
        # Reduce noise while preserving edges
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Adaptive thresholding handles varying illumination
        thresh = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11,
            C=2
        )

        # Morphological closing to connect broken lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

        return closed

    def _detect_contours(
        self, preprocessed: np.ndarray, h: int, w: int
    ) -> List[np.ndarray]:
        """Find and filter contours by area."""
        contours, hierarchy = cv2.findContours(
            preprocessed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        max_area = h * w * self.max_contour_area_ratio
        filtered = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_contour_area < area < max_area:
                filtered.append(cnt)

        return filtered

    def _classify_contours(
        self, contours: List[np.ndarray], analysis: DiagramAnalysis
    ) -> None:
        """
        Classify contours into rectangles (pockets/slots) using polygon
        approximation.
        """
        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            area = cv2.contourArea(cnt)

            if len(approx) == 4 and area > 500:
                # Rectangular shape — could be a pocket or slot
                x, y, w_rect, h_rect = cv2.boundingRect(approx)
                aspect_ratio = float(w_rect) / max(h_rect, 1)

                rect = DetectedRectangle(
                    x=x, y=y, width=w_rect, height=h_rect
                )

                if aspect_ratio > 3.0 or aspect_ratio < 0.33:
                    # Elongated rectangle → slot
                    analysis.slot_count += 1
                else:
                    # Regular rectangle → pocket
                    analysis.pocket_count += 1

                analysis.rectangles.append(rect)

    def _detect_circles(self, gray: np.ndarray) -> List[DetectedCircle]:
        """Detect circles using Hough Circle Transform."""
        circles_list = []

        # Apply slight blur for Hough
        blurred = cv2.medianBlur(gray, 5)

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=30,
            param1=100,
            param2=40,
            minRadius=5,
            maxRadius=200
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            for c in circles[0, :]:
                detected = DetectedCircle(
                    center_x=int(c[0]),
                    center_y=int(c[1]),
                    radius=int(c[2])
                )
                circles_list.append(detected)

        return circles_list

    def _detect_lines(self, preprocessed: np.ndarray) -> List[DetectedLine]:
        """Detect line segments using Probabilistic Hough Transform."""
        lines_list = []

        lines = cv2.HoughLinesP(
            preprocessed,
            rho=1,
            theta=np.pi / 180,
            threshold=80,
            minLineLength=40,
            maxLineGap=10
        )

        if lines is not None:
            for line in lines[:100]:  # Limit to 100 lines
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

                # Determine orientation
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                is_horizontal = bool(abs(angle) < 10 or abs(angle) > 170)
                is_vertical = bool(80 < abs(angle) < 100)

                detected = DetectedLine(
                    x1=int(x1), y1=int(y1),
                    x2=int(x2), y2=int(y2),
                    length_px=float(length),
                    is_horizontal=is_horizontal,
                    is_vertical=is_vertical
                )
                lines_list.append(detected)

        return lines_list

    def _detect_title_block(
        self, contours: List[np.ndarray], analysis: DiagramAnalysis,
        h: int, w: int
    ) -> None:
        """
        Detect the title block — typically a large rectangle
        in the bottom-right quadrant of the drawing.
        """
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)

            # Title block: bottom-right, reasonable size
            is_bottom_right = (x + cw > w * 0.5) and (y + ch > h * 0.6)
            is_reasonable_size = (
                cw > w * 0.15 and ch > h * 0.1 and
                cw < w * 0.55 and ch < h * 0.5
            )

            if is_bottom_right and is_reasonable_size:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

                if len(approx) >= 4:
                    analysis.has_title_block = True
                    analysis.title_block_region = {
                        "x": x, "y": y, "width": cw, "height": ch
                    }
                    break  # Take the first valid match

    def _estimate_views(
        self, contours: List[np.ndarray], h: int, w: int
    ) -> int:
        """
        Estimate number of drawing views by counting large,
        well-separated contour clusters.
        """
        large_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > h * w * 0.01:  # At least 1% of image area
                x, y, cw, ch = cv2.boundingRect(cnt)
                large_contours.append((x + cw // 2, y + ch // 2))

        if len(large_contours) < 2:
            return 1

        # Simple clustering: count distinct horizontal/vertical zones
        x_coords = sorted([c[0] for c in large_contours])
        y_coords = sorted([c[1] for c in large_contours])

        x_clusters = 1
        for i in range(1, len(x_coords)):
            if x_coords[i] - x_coords[i - 1] > w * 0.25:
                x_clusters += 1

        y_clusters = 1
        for i in range(1, len(y_coords)):
            if y_coords[i] - y_coords[i - 1] > h * 0.25:
                y_clusters += 1

        return max(x_clusters, y_clusters)

    def _detect_fillets_chamfers(
        self, contours: List[np.ndarray], analysis: DiagramAnalysis
    ) -> None:
        """
        Detect fillets (arcs/curves) and chamfers (angled edges)
        from contour approximations.
        """
        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            area = cv2.contourArea(cnt)

            if area < 200:
                continue

            # Approximate with tighter epsilon for detail
            approx_tight = cv2.approxPolyDP(cnt, 0.01 * peri, True)
            approx_loose = cv2.approxPolyDP(cnt, 0.04 * peri, True)

            num_vertices_tight = len(approx_tight)
            num_vertices_loose = len(approx_loose)

            # Many vertices with tight approx but few with loose → curves (fillets)
            if num_vertices_tight > 8 and num_vertices_loose <= 5:
                # Likely contains arcs / fillets
                circularity = 4 * np.pi * area / (peri * peri + 1e-6)
                if 0.3 < circularity < 0.9:
                    analysis.fillet_count += 1

            # Exactly 3 vertices in loose approx → triangular cut (chamfer)
            if num_vertices_loose == 3 and area < 5000:
                analysis.chamfer_count += 1

    def _compute_complexity(self, analysis: DiagramAnalysis) -> float:
        """
        Compute a part complexity score (0–100) based on detected features.

        Factors:
        - Number of holes, slots, pockets (each adds complexity)
        - Number of contours (geometric detail)
        - Fillets and chamfers (finishing operations)
        - Number of drawing views (more views = more complex part)
        """
        score = 0.0

        # Holes: 5 points each, max 30
        score += min(analysis.hole_count * 5, 30)

        # Slots: 8 points each, max 24
        score += min(analysis.slot_count * 8, 24)

        # Pockets: 6 points each, max 18
        score += min(analysis.pocket_count * 6, 18)

        # Fillets: 2 points each, max 8
        score += min(analysis.fillet_count * 2, 8)

        # Chamfers: 2 points each, max 8
        score += min(analysis.chamfer_count * 2, 8)

        # Contour detail: log-scaled
        if analysis.contour_count > 0:
            score += min(np.log1p(analysis.contour_count) * 2, 10)

        # Drawing views: 2 points per extra view
        score += min((analysis.num_drawing_views - 1) * 2, 6)

        return min(round(score, 2), 100.0)

    def _compute_symmetry(self, preprocessed: np.ndarray) -> float:
        """
        Estimate drawing symmetry by comparing left/right halves.

        Returns a score 0.0 (asymmetric) to 1.0 (perfectly symmetric).
        """
        h, w = preprocessed.shape[:2]
        mid = w // 2

        left_half = preprocessed[:, :mid]
        right_half = preprocessed[:, mid:2 * mid]

        # Flip right half horizontally
        right_flipped = cv2.flip(right_half, 1)

        # Ensure same size (in case of odd width)
        min_w = min(left_half.shape[1], right_flipped.shape[1])
        left_half = left_half[:, :min_w]
        right_flipped = right_flipped[:, :min_w]

        # Compute similarity (normalized cross-correlation)
        if left_half.size == 0 or right_flipped.size == 0:
            return 0.0

        # Use structural similarity via pixel comparison
        diff = cv2.absdiff(left_half, right_flipped)
        non_zero = cv2.countNonZero(diff)
        total_pixels = left_half.shape[0] * left_half.shape[1]

        similarity = 1.0 - (non_zero / max(total_pixels, 1))
        return round(max(0.0, similarity), 3)
