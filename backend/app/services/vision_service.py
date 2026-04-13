# Placeholder for OCR/video framework
import cv2
import re
from paddleocr import PaddleOCR

# intialize the ocr model once at the module level to avoid repeated loading
ocr = PaddleOCR()


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


def detect_qr_codes(image_file) -> list[str]:
    """
    TODO: Use OpenCV to detect and decode QR codes into URL strings.
    """
    return []


def extract_ocr_text(image_file) -> str:
    """
    TODO: Use PaddleOCR to extract text from images/screenshots.
    Return "" if no text found.
    We have two helper functions here:
    One to detect the language of the text
    Another to join the text lines based on the detected language (Chinese vs English/Bahasa Malaysia).
    """

    def detect_language(text: str) -> str:
        """
        Detect the language of the text based on character analysis.
        """
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        english_chars = len(re.findall(r"[A-Za-z]", text))

        # based on most characters, determine language
        total = chinese_chars + english_chars

        if total == 0:
            return "Unknown"

        # ratio-based decision
        chinese_ratio = chinese_chars / total
        english_ratio = english_chars / total

        if chinese_ratio > 0.7:
            return "Chinese"
        elif english_ratio > 0.7:
            return "English or Bahasa Malaysia"
        else:
            return "Mixed"

    def join_text(lines, lang="unknown"):
        """
        Join lines of text based on detected language.
        For Chinese, join without spaces.
        For English and Bahasa Malaysia, join with spaces.
        """
        if lang == "chinese":
            return "".join(lines).strip()
        else:
            return " ".join(lines).strip()

    # load image
    img = cv2.imread(image_file)
    if img is None:
        raise ValueError(f"Could not read image: {image_file}")

    # grayscale
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # enlarge
    gray_enlarged = cv2.resize(
        gray_img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC
    )

    # threshold
    _, thresh_img = cv2.threshold(gray_enlarged, 170, 255, cv2.THRESH_BINARY)

    # convert to 3 channel
    thresh_img = cv2.cvtColor(thresh_img, cv2.COLOR_GRAY2BGR)

    # OCR
    result_img = ocr.predict(thresh_img)

    # different lines of text extracted from OCR result --> risk explaination (highlighting text)
    extracted_lines = []
    for item in result_img:
        if isinstance(item, dict) and "rec_texts" in item:
            extracted_lines.extend(item["rec_texts"])

    full_text_temp = " ".join(extracted_lines)

    # detect language
    detected_lang = detect_language(full_text_temp)
    # join text based on language
    full_text = join_text(extracted_lines, detected_lang)

    return full_text
