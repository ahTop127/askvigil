# Placeholder for OCR/video framework


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
    TODO: Use PaddleOCR or Tesseract to extract text from images/screenshots.
    Return "" if no text found.
    """
    return ""
