import re

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/qr", tags=["Epic 4: QR Risk Analysis"])

# The regular expression matching the URL
URL_PATTERN = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*")

# Initialize the QR code detector of OpenCV (global multiplexing to improve performance)
qr_detector = cv2.QRCodeDetector()


@router.post("/analyze")
async def analyze_qr_code(file: UploadFile = File(...)):
    """
    AC 4.2: Check if a QR Code Is Safe
    """
    # 1. verify the file type
    # When a user uploads a file,
    # the browser will automatically attach a Content-Type header
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file.")

    try:
        # 2. convert the binary stream received by fastapi directly to opencv, an readable array.
        file_byte = np.frombuffer(await file.read(), dtype=np.uint8)
        # Decode the flat numpy array into an image matrix that OpenCV can understand
        img = cv2.imdecode(file_byte, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Could not decode image")

        # 3. use opencv decode the QR contend
        # Youdaoplaceholder0 - corrected QR code image
        data, bbox, straight_qrcode = qr_detector.detectAndDecode(img)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {e!s}")

    # AC 4.2.2: Prevent analysis when no valid QR Code content is provided
    if not data:
        raise HTTPException(
            status_code=400,
            detail="This is not a valid QR code. Please upload a valid QR code to check.",
        )

    # extract URLs from the content
    urls = URL_PATTERN.findall(data)
    if not urls:
        raise HTTPException(
            status_code=400,
            detail="Valid QR code found, but it does not contain any URL to analyze.",
        )

    target_url = urls[0]

    # 5. Call the URL risk detection logic (Mock) of a colleague
    risk_result = {
        "risk_score": 85,
        "risk_level": "High Risk",
        "suspicious_indicators": [
            "Domain age is less than 30 days",
            "Phishing patterns detected",
        ],
    }

    # 6. Return result (AC 4.2.3)
    return {
        "decoded_content": data,
        "extracted_url": target_url,
        "risk_analysis": risk_result,
    }
