# Placeholder for OCR/video framework
import cv2
import re

# import easyocr
import numpy as np
from fastapi import UploadFile
from rapidocr_onnxruntime import RapidOCR

# Placeholder for models via oracle storage
# engine = RapidOCR(
#     det_model_path=settings.OCR_DET_PATH,
#     cls_model_path=settings.OCR_CLS_PATH,
#     rec_model_path=settings.OCR_REC_PATH,
#     rec_keys_path=settings.OCR_KEYS_PATH
# )

# RapidOCR uses ONNX INT8 by default if models are provided,
# but the standard package is already 5-10x faster than EasyOCR.
engine = RapidOCR(det_db_thresh=0.2, det_db_box_thresh=0.4)

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


def extract_ocr_text(image_file: UploadFile) -> str:
    """
    Extracts text from UploadFile using RapidOCR.
    Optimized for speed and specific language joining rules.
    """
    # 1. IO: Read bytes and manage file pointer
    image_file.file.seek(0)
    file_bytes = image_file.file.read()
    image_file.file.seek(0)

    # 2. Decode: Convert bytes to OpenCV image
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return ""

    # 3. Scale: Resize large images to 1280px to boost speed without losing accuracy
    h, w = img.shape[:2]
    if max(h, w) > 1024:
        scale = 1024 / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

    # 4. Inference: Run OCR (Detection + Recognition)
    result, _ = engine(img)
    if not result:
        return ""

    # 5. Sort: Order text boxes top-to-bottom, then left-to-right
    result.sort(key=lambda x: (x[0][0][1], x[0][0][0]))

    extracted_lines = [line[1] for line in result]
    full_text_raw = " ".join(extracted_lines)

    # 6. Language Logic: Determine if text is primarily Chinese
    def detect_language(text: str) -> str:
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        english_chars = len(re.findall(r"[A-Za-z]", text))
        total = chinese_chars + english_chars
        if total == 0:
            return "Unknown"
        return "Chinese" if (chinese_chars / total) > 0.7 else "English"

    # 7. Join: Remove spaces for Chinese; keep spaces for English/Malay
    if detect_language(full_text_raw) == "Chinese":
        return "".join(extracted_lines).strip()
    else:
        return " ".join(extracted_lines).strip()
