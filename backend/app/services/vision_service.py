# RapidOCR service
import cv2
import re
import numpy as np
from fastapi import UploadFile
from time import perf_counter
from app.core.registry import MODEL_REGISTRY
import logging
import hashlib

logger = logging.getLogger(__name__)

# QR Regex to match URLS
URL_PATTERN = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*")

# Initialize the QR code detector of OpenCV (global multiplexing to improve performance)
qr_detector = cv2.QRCodeDetector()


class ImageRouter:
    def __init__(self):
        self.specs = {
            "blur": {"ideal": 120.0, "fail": 40.0, "w": 1.5},
            "contrast": {"ideal": 0.8, "fail": 0.2, "w": 1.5},
            "entropy": {"ideal": 4.5, "fail": 6.5, "w": 1.0},
            "noise": {"ideal": 3.0, "fail": 12.0, "w": 1.0},
            "complexity": {"ideal": 300, "fail": 2200, "w": 1.0},  # 16-bin
        }
        self.last_analysis = {}

    def _get_histogram_complexity(self, image):
        # Resize to fixed dimension for O(1) temporal consistency
        small_img = cv2.resize(image, (128, 128), interpolation=cv2.INTER_AREA)
        hist = cv2.calcHist(
            [small_img], [0, 1, 2], None, [16, 16, 16], [0, 256, 0, 256, 0, 256]
        )
        return np.count_nonzero(hist)

    def _estimate_noise(self, gray):
        # Optimized Box Filter (Faster than Gaussian for high-pass residual)
        mean_img = cv2.boxFilter(gray, -1, (3, 3))
        residual = gray.astype(np.float32) - mean_img
        return np.std(residual)

    def is_complex(self, raw_image) -> bool:
        if raw_image is None or raw_image.size == 0:
            return False

        # --- ARCHITECTURAL GUARD: ANALYSIS DOWNSCALE ---
        # We create a 'Proxy' for analysis so 4K images don't kill throughput.
        h, w = raw_image.shape[:2]
        max_dim = max(h, w)
        analysis_scale = 1024

        if max_dim > analysis_scale:
            # Scale down only heavy images
            scale_factor = analysis_scale / max_dim
            image = cv2.resize(
                raw_image,
                (0, 0),
                fx=scale_factor,
                fy=scale_factor,
                interpolation=cv2.INTER_AREA,
            )
        else:
            # Use raw pixels for low-res/small images for max accuracy
            image = raw_image

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        min_v, max_v, _, _ = cv2.minMaxLoc(gray)

        # 1. Critical Failure: Non-Informative Frames
        # If the image is flat-black or total-white, it's "Complex" (unusable)
        if max_v - min_v < 10:
            return True

        # 2. Metric Extraction
        m = {
            "blur": cv2.Laplacian(gray, cv2.CV_64F).var(),
            "entropy": -np.sum(
                (
                    p := (h := cv2.calcHist([gray], [0], None, [256], [0, 256])).ravel()
                    / (h.sum() + 1e-7)
                )
                * np.log2(p + 1e-7)
            ),
            "contrast": (max_v - min_v) / (max_v + min_v + 1e-7),
            "noise": self._estimate_noise(gray),
            "complexity": self._get_histogram_complexity(image),
        }

        # 3. CRITICAL GATES
        critical_reasons = []
        if m["blur"] < 35:
            critical_reasons.append("Severe Blur")
        if m["contrast"] < 0.15:
            critical_reasons.append("Severe Washout")
        if m["complexity"] > 3500:
            critical_reasons.append("Extreme Complexity")  # Sensor noise ceiling

        is_critical = len(critical_reasons) > 0

        # 4. WEIGHTED ACCUMULATION
        reasons = []
        total_risk = 0.0

        for key, spec in self.specs.items():
            val = m[key]
            if key in ["blur", "contrast"]:
                penalty = np.clip(
                    (spec["ideal"] - val) / (spec["ideal"] - spec["fail"]), 0, 1
                )
            else:
                penalty = np.clip(
                    (val - spec["ideal"]) / (spec["fail"] - spec["ideal"]), 0, 1
                )

            total_risk += penalty * spec["w"]
            if penalty > 0.2:
                reasons.append(f"{key}({int(penalty * 100)}%)")

        should_escalate = is_critical or (total_risk >= 2.5)

        self.last_analysis = {
            "is_complex": should_escalate,
            "complexity_score": round(total_risk, 2),
            "reasons": (", ".join(critical_reasons + reasons))
            if (is_critical or reasons)
            else "Nominal",
            "metrics": m,
        }

        return should_escalate


router = ImageRouter()


def detect_qr_codes(image_file: UploadFile) -> list[str]:
    """
    Decode QR codes from an uploaded image and extract URLs.

    Return format:
    [
      {
        "decoded_content": "...",
        "urls": ["https://..."]
      }
    ]

    Raises:
        ValueError: when file type/content is invalid or image decode fails.
    """
    # 1) Basic type guard (service layer uses ValueError, not HTTPException)
    content_type = image_file.content_type or ""
    if not content_type.startswith("image/"):
        raise ValueError("Please upload a valid image file.")

    # 2) Read bytes safely (sync service style)
    image_file.file.seek(0)
    file_bytes = image_file.file.read()
    image_file.file.seek(0)

    logger.info(f"QR filename: {image_file.filename}")
    logger.info(f"QR content_type: {image_file.content_type}")
    logger.info(f"QR bytes length: {len(file_bytes)}")
    logger.info(f"QR sha256: {hashlib.sha256(file_bytes).hexdigest()}")

    if not file_bytes:
        raise ValueError("Uploaded image is empty.")

    # 3) Decode image
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")

    # 4) Decode QR (single QR path; enough for current use case)
    data, _bbox, _straight_qrcode = qr_detector.detectAndDecode(img)

    # 5) Normalize output
    if not data:
        return []

    urls = URL_PATTERN.findall(data)
    return [{"decoded_content": data, "urls": urls}]


def get_rotate_crop_image(img: np.ndarray, points: list) -> np.ndarray:
    """
    Rectifies a quadrilateral text region into a standard horizontal bounding crop.
    """
    img_height, img_width = img.shape[:2]
    points = np.array(points, dtype=np.float32)

    rect_width = int(
        max(
            np.linalg.norm(points[0] - points[1]), np.linalg.norm(points[2] - points[3])
        )
    )
    rect_height = int(
        max(
            np.linalg.norm(points[0] - points[3]), np.linalg.norm(points[1] - points[2])
        )
    )

    # Clamp dimensions to legal physical asset sizes
    rect_width = max(1, min(rect_width, img_width))
    rect_height = max(1, min(rect_height, img_height))

    dst_pts = np.array(
        [[0, 0], [rect_width, 0], [rect_width, rect_height], [0, rect_height]],
        dtype=np.float32,
    )

    M = cv2.getPerspectiveTransform(points, dst_pts)
    img_crop = cv2.warpPerspective(
        img,
        M,
        (rect_width, rect_height),
        borderMode=cv2.BORDER_REPLICATE,
        flags=cv2.INTER_LINEAR,
    )

    # Rotate vertical text to horizontal for standard CRNN processing
    if img_crop.shape[0] > img_crop.shape[1] * 1.5:
        img_crop = np.rot90(img_crop, -1)

    return img_crop


def sanitize_for_json(obj):
    """Recursively converts NumPy types to native Python types."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.float32, np.float64)):
        return obj.item()  # Converts to native Python float
    elif isinstance(obj, (np.int32, np.int64)):
        return obj.item()  # Converts to native Python int
    return obj


def scan_ocr(
    image: np.ndarray, engine_rapid, engine_enhanced, router
) -> tuple[list, dict]:
    """
    Executes an optimized multi-modal routing, detection, filtering, and
    batched recognition loop over an input matrix asset.
    """
    t_total = perf_counter()

    # --- Phase 1: Complexity Routing ---
    is_complex = router.is_complex(image)
    analysis = router.last_analysis
    engine = engine_enhanced if is_complex else engine_rapid

    # DO NOT RESIZE MANUALLY. LET RAPIDOCR DO IT.
    # --- Phase 2: Core Matrix Detection ---
    dt_boxes, _ = engine.text_det(image)

    if dt_boxes is None:
        return [], {}

    # --- Phase 3: Bounding-Box Filtering Matrix ---
    filtered = []
    for box in dt_boxes:
        try:
            x = box[:, 0]
            y = box[:, 1]

            w_box = max(x) - min(x)
            h_box = max(y) - min(y)

            # Drop micro-artifacts or skewed aspect spaces
            if (w_box * h_box < 50) or (w_box < 8 or h_box < 8):
                continue

            aspect = w_box / max(h_box, 1)
            if aspect > 25 or aspect < 0.1:
                continue

            filtered.append(box)
        except Exception:
            continue

    dt_boxes = filtered

    # --- Phase 4: Parallelized Crop Rectification ---
    crops_and_boxes = [(get_rotate_crop_image(image, box), box) for box in dt_boxes]

    # Purge broken dimensions in a singular list comprehension pass
    valid_data = [
        (c, b)
        for c, b in crops_and_boxes
        if c is not None and c.size > 0 and c.shape[0] >= 5 and c.shape[1] >= 5
    ]

    if not valid_data:
        return [], {}

    # Group dimensions horizontally to minimize padding layout space math
    valid_data.sort(key=lambda x: x[0].shape[1])
    crops, boxes = zip(*valid_data)

    # --- Phase 5: Recognition (Width Bucket Optimized) ---
    final_results = []
    skipped = 0
    buckets = {"s": [], "m": [], "l": []}

    for crop, box in zip(crops, boxes):
        w = crop.shape[1]

        # Enforce scale constraints on heavy lines
        if w > 512:
            scale = 512 / w
            crop = cv2.resize(
                crop,
                (512, max(8, int(crop.shape[0] * scale))),
                interpolation=cv2.INTER_AREA,
            )
            w = 512

        if w < 128:
            buckets["s"].append((crop, box))
        elif w < 256:
            buckets["m"].append((crop, box))
        else:
            buckets["l"].append((crop, box))

    try:
        for bucket_name in ["s", "m", "l"]:
            bucket = buckets[bucket_name]
            if not bucket:
                continue

            bucket_crops, bucket_boxes = zip(*bucket)
            rec_results, _ = engine.text_rec(list(bucket_crops))

            for box, rec in zip(bucket_boxes, rec_results):
                if not rec:
                    skipped += 1
                    continue

                text, conf = rec[0], float(rec[1])

                if conf >= 0.4:
                    final_results.append(
                        {"box": box.tolist(), "text": text, "conf": round(conf, 4)}
                    )
                else:
                    skipped += 1

    except Exception:
        logger.exception("CRITICAL: OCR Batch Recognition Engine Failure")

    # --- Phase 6: Top-Down, Left-to-Right Reading Order Sorting ---
    if final_results:
        heights = [
            np.max(np.array(x["box"])[:, 1]) - np.min(np.array(x["box"])[:, 1])
            for x in final_results
        ]
        denom = max(np.mean(heights) if heights else 32, 1) * 0.8

        final_results.sort(
            key=lambda x: (
                np.mean(np.array(x["box"])[:, 1]) // denom,
                np.mean(np.array(x["box"])[:, 0]),
            )
        )

    # Compile tracking metadata schema
    total_ms = (perf_counter() - t_total) * 1000
    metadata = {
        "source": "enhanced" if is_complex else "rapid",
        "complexity_score": analysis["complexity_score"],
        "reasons": analysis["reasons"],
        "metrics": analysis["metrics"],
        "stats": {
            "detected": len(dt_boxes),
            "processed": len(final_results),
            "skipped": skipped,
        },
        "elapse_ms": total_ms,
    }

    return final_results, sanitize_for_json(metadata)


def extract_ocr_text(image_file: UploadFile) -> str:
    """
    Extracts text from UploadFile using RapidOCR.
    Integrates Adaptive Routing, ARM-Optimization, and Language Joining.
    Uses rapid model for simple images, enhanced model for complex images.
    Returns text, and metadata of image quality
    """
    # 1. Access pre-warmed engines from Lifespan
    engine_rapid = MODEL_REGISTRY.get("ocr_rapid")
    engine_enhanced = MODEL_REGISTRY.get("ocr_enhanced")

    # Guard: If models failed to load in lifespan, handle gracefully
    if not engine_rapid or not engine_enhanced:
        logger.error("OCR Engines missing from Registry")
        return "Service temporarily unavailable: OCR Engine Error"

    # 2. IO and Decode
    image_file.file.seek(0)
    file_bytes = image_file.file.read()
    image_file.file.seek(0)
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return ""

    # 3. Process via our new dual-engine pipeline
    # Note: scan_ocr handles its own analysis-scaling internal to the Router
    results, metadata = scan_ocr(img, engine_rapid, engine_enhanced, router)

    if not results:
        return ""

    # 4. Extract text lines from structured results
    # results looks like: [{"box": [...], "text": "...", "conf": 0.9}, ...]
    extracted_lines = [item["text"] for item in results]
    full_text_raw = " ".join(extracted_lines)

    # 5. Language Logic: Determine if text is primarily Chinese
    def detect_language(text: str) -> str:
        import re

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        english_chars = len(re.findall(r"[A-Za-z]", text))
        total = chinese_chars + english_chars
        if total == 0:
            return "Unknown"
        return "Chinese" if (chinese_chars / total) > 0.7 else "English"

    # 6. Join & Return
    # This keeps your NLP service happy with a clean string
    if detect_language(full_text_raw) == "Chinese":
        final_text = "".join(extracted_lines).strip()
    else:
        final_text = " ".join(extracted_lines).strip()

    return final_text, metadata
