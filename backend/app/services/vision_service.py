# Placeholder for OCR/video framework
import cv2
import re

# import easyocr
import numpy as np
from fastapi import UploadFile
from time import perf_counter
from app.core.registry import MODEL_REGISTRY

# from rapidocr_onnxruntime import RapidOCR
import logging

import hashlib

# RapidOCR uses ONNX INT8 by default if models are provided,
# but the standard package is already 5-10x faster than EasyOCR.
# engine = RapidOCR(det_db_thresh=0.2, det_db_box_thresh=0.4)

# intialize the ocr model once at the module level to avoid repeated loading
# Note: if easyocr is still too laggy, try rapidocr
# reader = easyocr.Reader(["en"], gpu=False, verbose=False)


def extract_audio_from_video(video_file) -> str:
    """
    TODO: (Optional) Use ffmpeg-python to strip the audio track from the video file.
    Save to a temporary file and return the path.
    """
    return "temp/dummy_audio.wav"


def extract_frames(video_file):
    """
    TODO: (Optional) Implement frame sampling (e.g., 1 frame per second) using OpenCV (cv2).
    Yield frames iteratively to prevent RAM exhaustion.
    """
    yield "dummy_frame_data"


async def scan_visual_forensics(frame_generator):
    """
    TODO: (Optional) Scan visuals for deepfakes.
    """
    return {"visual_risk_score": 0.0, "flags": []}


# QR Regular
# The regular expression matching the URL
URL_PATTERN = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*")

# Initialize the QR code detector of OpenCV (global multiplexing to improve performance)
qr_detector = cv2.QRCodeDetector()


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

    print("QR filename:", image_file.filename)
    print("QR content_type:", image_file.content_type)
    print("QR bytes length:", len(file_bytes))
    print("QR sha256:", hashlib.sha256(file_bytes).hexdigest())

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

    # def extract_ocr_text(image_file: UploadFile) -> str:
    #     """
    #     TODO: Use EasyOCR to extract text from images/screenshots.
    #     Return "" if no text found.
    #     We have two helper functions here:
    #     One to detect the language of the text
    #     Another to join the text lines based on the detected language (Chinese vs English/Bahasa Malaysia).
    #     """

    #     def detect_language(text: str) -> str:
    #         """
    #         Detect the language of the text based on character analysis.
    #         """
    #         chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    #         english_chars = len(re.findall(r"[A-Za-z]", text))

    #         # based on most characters, determine language
    #         total = chinese_chars + english_chars

    #         if total == 0:
    #             return "Unknown"

    #         # ratio-based decision
    #         chinese_ratio = chinese_chars / total
    #         english_ratio = english_chars / total

    #         if chinese_ratio > 0.7:
    #             return "Chinese"
    #         elif english_ratio > 0.7:
    #             return "English or Bahasa Malaysia"
    #         else:
    #             return "Mixed"

    #     def join_text(lines, lang="unknown"):
    #         """
    #         Join lines of text based on detected language.
    #         For Chinese, join without spaces.
    #         For English and Bahasa Malaysia, join with spaces.
    #         """
    #         if lang == "Chinese":
    #             return "".join(lines).strip()
    #         else:
    #             return " ".join(lines).strip()

    #     # 1. Reset the pointer in case a previous service touched it
    #     image_file.file.seek(0)

    #     # 2. Read the bytes
    #     # Note: Use image_file.file.read() in sync functions,
    #     # or await image_file.read() in async functions.
    #     file_bytes = image_file.file.read()

    #     # 3. Reset the pointer again for the next service
    #     image_file.file.seek(0)

    #     # 4. Convert bytes to numpy array
    #     nparr = np.frombuffer(file_bytes, np.uint8)

    #     # 5. Decode the image (this replaces cv2.imread)
    #     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    #     # # load image
    #     # img = cv2.imread(image_file)
    #     if img is None:
    #         raise ValueError(f"Could not read image: {image_file}")

    #     # grayscale
    #     gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #     # enlarge
    #     gray_enlarged = cv2.resize(
    #         # 2x linear optimized for arm/easyocr
    #         gray_img,
    #         None,
    #         fx=2,
    #         fy=2,
    #         interpolation=cv2.INTER_LINEAR,
    #         # gray_img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC # cubic too much for oracle arm server
    #     )

    #     # Adaptive thresholding
    #     processed_img = cv2.adaptiveThreshold(
    #         gray_enlarged, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    #     )
    #     # Otsu's thresholding (alternative adaptive thresholding)
    #     # _, processed_img = cv2.threshold(gray_enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    #     # Automatic Inversion (In case of dark mode)
    #     # If the background is dark (mean < 127), flip it so text is black on white
    #     if np.mean(processed_img) < 127:
    #         processed_img = cv2.bitwise_not(processed_img)

    #     # EasyOCR can read grayscale perfectly unless you have colourful text.
    #     # Only enable below if we need colourful text detection.
    #     # # convert to 3 channel
    #     # processed_img = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)

    #     # EasyOCR. detail=0 returns a simple list of strings
    #     extracted_lines = reader.readtext(processed_img, detail=0)

    #     full_text_temp = " ".join(extracted_lines)

    #     # detect language
    #     detected_lang = detect_language(full_text_temp)
    #     # join text based on language
    #     full_text = join_text(extracted_lines, detected_lang)

    #     return full_text

    urls = URL_PATTERN.findall(data)
    return [{"decoded_content": data, "urls": urls}]


# # Keep default rapidocr here commented out for benchmarking later
# def extract_ocr_text(image_file: UploadFile) -> str:
#     """
#     Extracts text from UploadFile using RapidOCR, default settings.
#     Optimized for speed and specific language joining rules.
#     """
#     t_start = time.perf_counter()
#     # 1. IO: Read bytes and manage file pointer
#     image_file.file.seek(0)
#     file_bytes = image_file.file.read()
#     image_file.file.seek(0)

#     # 2. Decode: Convert bytes to OpenCV image
#     nparr = np.frombuffer(file_bytes, np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#     if img is None:
#         return ""

#     # 3. Scale: Resize large images to 1280px to boost speed without losing accuracy
#     h, w = img.shape[:2]
#     if max(h, w) > 1024:
#         scale = 1024 / max(h, w)
#         img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

#     # 4. Inference: Run OCR (Detection + Recognition)
#     result, _ = engine(img)
#     if not result:
#         return ""

# # 5. Sort: Order text boxes top-to-bottom, then left-to-right
# result.sort(key=lambda x: (x[0][0][1], x[0][0][0]))

# extracted_lines = [line[1] for line in result]
# full_text_raw = " ".join(extracted_lines)

#     # 6. Language Logic: Determine if text is primarily Chinese
#     def detect_language(text: str) -> str:
#         chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
#         english_chars = len(re.findall(r"[A-Za-z]", text))
#         total = chinese_chars + english_chars
#         if total == 0:
#             return "Unknown"
#         return "Chinese" if (chinese_chars / total) > 0.7 else "English"

#     # 7. Join: Remove spaces for Chinese; keep spaces for English/Malay
#     elapse_ms = round((time.perf_counter() - t_start) * 1000, 2)
#     print(f"OCR scanned in: {elapse_ms} ms")
#     if detect_language(full_text_raw) == "Chinese":
#         return "".join(extracted_lines).strip()
#     else:
#         return " ".join(extracted_lines).strip()


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
            "score": round(total_risk, 2),
            "reasons": (", ".join(critical_reasons + reasons))
            if (is_critical or reasons)
            else "Nominal",
            "metrics": m,
        }

        return should_escalate


router = ImageRouter()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("OCR-Core")


def is_meaningless(box_img):
    """
    Extremely cheap reject filter.
    Must remain much cheaper than OCR.
    """
    if box_img is None or box_img.size == 0:
        return True

    h, w = box_img.shape[:2]

    # Reject tiny crops
    if h < 4 or w < 4:
        return True

    gray = cv2.cvtColor(box_img, cv2.COLOR_BGR2GRAY)

    # Extremely low variance usually means blank/noise
    if gray.std() < 2.0:
        return True

    return False


def get_optimal_size(is_complex, image):
    h, w = image.shape[:2]
    # Calculate aspect ratio (Longest / Shortest)
    aspect_ratio = max(w, h) / (min(w, h) + 1e-7)

    # Rapid Path
    if not is_complex:
        # If it's a 'sliver' (extreme aspect ratio > 10:1)
        # boost the size to ensure the text remains tall enough.
        if aspect_ratio > 10:
            return 1280
        return 640

    # Enhanced Path (Complex/Photos)
    if max(h, w) > 1500:
        return 1024
    return 960


def get_rotate_crop_image(img, points):
    """
    Rectify a quadrilateral text region into a horizontal crop.
    Optimized for OCR throughput + stability.
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

    # Clamp pathological dimensions
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

    # Rotate vertical text
    if img_crop.shape[0] > img_crop.shape[1] * 1.5:
        img_crop = np.rot90(img_crop, -1)

    return img_crop


def log_step(name, start):
    ms = (perf_counter() - start) * 1000
    print(f"[PROFILE] {name}: {ms:.2f} ms")
    return perf_counter()


import cv2


def pad_to_same_width(crops, target_h=48):
    """
    Normalize crops to same height and padded width.
    This stabilizes ONNX batch execution.
    """

    resized = []
    max_w = 0

    # 1. normalize height first (CRITICAL)
    for img in crops:
        h, w = img.shape[:2]
        scale = target_h / max(h, 1)
        new_w = int(w * scale)
        new_h = target_h

        resized_img = cv2.resize(img, (new_w, new_h))
        resized.append(resized_img)
        max_w = max(max_w, new_w)

    # 2. pad width
    padded = []
    for img in resized:
        h, w = img.shape[:2]

        pad = np.zeros((h, max_w, 3), dtype=np.uint8)
        pad[:, :w] = img

        padded.append(pad)

    return padded


def scan_ocr(image, engine_rapid, engine_enhanced):

    t_total = perf_counter()
    print("\n================ OCR START ================\n")
    # -------------------------------------------------
    # Phase 1: Routing
    # -------------------------------------------------
    t = perf_counter()
    is_complex = router.is_complex(image)
    # is_complex = True # Hard coded only for testing.
    analysis = router.last_analysis
    engine = engine_enhanced if is_complex else engine_rapid
    print(f"[ROUTE] complex={is_complex}")
    log_step("routing", t)

    # DO NOT RESIZE MANUALLY. LET RAPIDOCR DO IT.

    # -------------------------------------------------
    # Phase 2: DETECTION
    # -------------------------------------------------
    t = perf_counter()
    dt_boxes, _ = engine.text_det(image)
    log_step("det", t)

    if dt_boxes is None:
        print("[DET] No boxes")
        return [], {}
    print(f"[DET] raw boxes: {len(dt_boxes)}")

    # -------------------------------------------------
    # Phase 3: BOX FILTER
    # -------------------------------------------------
    t = perf_counter()
    filtered = []
    for box in dt_boxes:
        try:
            x = box[:, 0]
            y = box[:, 1]

            w_box = max(x) - min(x)
            h_box = max(y) - min(y)

            if w_box * h_box < 50:
                continue
            if w_box < 8 or h_box < 8:
                continue

            aspect = w_box / max(h_box, 1)
            if aspect > 25 or aspect < 0.1:
                continue

            filtered.append(box)
        except:
            continue

    dt_boxes = filtered
    print(f"[FILTER] boxes kept: {len(dt_boxes)}")

    log_step("box-filter", t)

    # -------------------------------------------------
    # Phase 4: CROPPING (List Comprehension is faster)
    # -------------------------------------------------
    t = perf_counter()

    # Use a list comprehension for a tighter loop
    crops_and_boxes = [(get_rotate_crop_image(image, box), box) for box in dt_boxes]

    # Filter out invalid crops in one pass
    valid_data = [
        (c, b)
        for c, b in crops_and_boxes
        if c is not None and c.size > 0 and c.shape[0] >= 5 and c.shape[1] >= 5
    ]

    if not valid_data:
        return [], {}

    # Group similar lengths to minimize padding math
    valid_data.sort(key=lambda x: x[0].shape[1])
    crops, boxes = zip(*valid_data)
    log_step("crop", t)

    # -------------------------------------------------
    # Phase 5: RECOGNITION (Width Bucket Optimized)
    # -------------------------------------------------
    t = perf_counter()
    final_results = []
    skipped = 0

    # Bucket by crop width to reduce padding waste
    buckets = {"s": [], "m": [], "l": []}

    for crop, box in zip(crops, boxes):
        w = crop.shape[1]
        # Optional width cap
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

    except Exception as e:
        print(f"[RECOGNITION CRITICAL]: {e}")

    log_step("rec-batch", t)

    # --- PHASES 6: READING ORDER SORT ---
    t = perf_counter()
    # Inline sorting
    final_results.sort(
        key=lambda x: (
            np.mean(np.array(x["box"])[:, 1]),
            np.mean(np.array(x["box"])[:, 0]),
        )
    )
    log_step("sort", t)

    # -------------------------------------------------
    # FINAL
    # -------------------------------------------------
    total = (perf_counter() - t_total) * 1000

    print("\n============= OCR PROFILE =============")
    print(f"TOTAL TIME: {total:.2f} ms")
    print(f"boxes: {len(dt_boxes)}")
    print(f"crops: {len(crops)}")
    print(f"skipped: {skipped}")
    print("======================================\n")

    metadata = {
        "source": f"{'enhanced' if is_complex else 'rapid'}",
        "risk_score": analysis["score"],
        "reasons": analysis["reasons"],
        "metrics": analysis["metrics"],
        "stats": {
            "detected": len(dt_boxes),
            "processed": len(final_results),
            "skipped": skipped,
        },
        "elapse_ms": total,
    }
    return final_results, metadata


def extract_ocr_text(image_file: UploadFile) -> str:
    """
    Extracts text from UploadFile using RapidOCR.
    Integrates Adaptive Routing, ARM-Optimization, and Language Joining.
    Uses rapid model for simple images, enhanced model for complex images.
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
    results, metadata = scan_ocr(img, engine_rapid, engine_enhanced)

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

    # Diagnostics: Attach the metadata to the return value temporarily
    # or log it so the Profiler can see it.
    print(
        f"DIAGNOSTIC: {metadata['source']} | Risk: {metadata['risk_score']} | Time: {metadata['elapse_ms']}ms"
    )

    return final_text
