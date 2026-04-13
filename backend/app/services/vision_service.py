# Placeholder for OCR/video framework
import cv2
import re
import easyocr
import numpy as np

# intialize the ocr model once at the module level to avoid repeated loading
reader = easyocr.Reader(["en"], gpu=False)


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
    TODO: Use EasyOCR to extract text from images/screenshots.
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
        # 2x linear optimized for arm/easyocr
        gray_img,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_LINEAR,
        # gray_img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC # cubic too much for oracle arm server
    )

    # Adaptive thresholding
    processed_img = cv2.adaptiveThreshold(
        gray_enlarged, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    # Otsu's thresholding (alternative adaptive thresholding)
    # _, processed_img = cv2.threshold(gray_enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Automatic Inversion (In case of dark mode)
    # If the background is dark (mean < 127), flip it so text is black on white
    if np.mean(processed_img) < 127:
        processed_img = cv2.bitwise_not(processed_img)

    # EasyOCR can read grayscale perfectly unless you have colourful text.
    # Only enable below if we need colourful text detection.
    # # convert to 3 channel
    # processed_img = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)

    # EasyOCR. detail=0 returns a simple list of strings
    extracted_lines = reader.readtext(processed_img, detail=0)

    full_text_temp = " ".join(extracted_lines)

    # detect language
    detected_lang = detect_language(full_text_temp)
    # join text based on language
    full_text = join_text(extracted_lines, detected_lang)

    return full_text
