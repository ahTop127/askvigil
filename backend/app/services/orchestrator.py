import asyncio
from typing import Literal

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from app.services import nlp_service, vision_service
from app.utils.url_tools import get_url_report


async def scan_universal_input(
    file: UploadFile = None,
    text: str = None,
    input_type: Literal["text", "image", "qr", "auto"] = "auto",
):
    """The Master Entry Point with cascading text aggregation."""
    results = {"modalities": {}, "unified_text_analysis": None, "metadata": {}}
    accumulated_text = []

    if text:
        accumulated_text.append(text)

    if file:
        mime = file.content_type

        # 1) Clarify the QR branch: Only conduct URL detection and do not perform unified_text
        if input_type == "qr":
            qr_res = await _handle_qr_flow(file)
            results["modalities"]["qr"] = qr_res
            return results

        elif "image" in mime:
            img_res, img_text, metadata = await _handle_image_flow(file)
            results["modalities"]["image"] = img_res
            if img_text:
                accumulated_text.append(img_text)
            results["metadata"] = metadata

    # Execution Layer: Unified Text Scanning
    if accumulated_text:
        # Join multiple text sources with a newline to preserve logical separation
        combined_text = "\n".join(accumulated_text)
        results["unified_text_analysis"] = await nlp_service.scan_unified_text(
            combined_text
        )

    return results


async def _handle_image_flow(image_file: UploadFile):
    """
    Runs extract_ocr_text asynchronously via custom RapidOCR implementation.
    1) Detect text in image
    2) Preprocess text boxes
    3) Recognize text
    Returns:
    Text results
    """
    results = {"qr_urls": []}

    # Look for Text via OCR, implemented in the vision service file
    # Run in async so we don't hog the server
    extracted_text, metadata = await run_in_threadpool(
        vision_service.extract_ocr_text, image_file
    )

    return results, extracted_text, metadata


async def _handle_qr_flow(qr_file: UploadFile):
    """
    QR-only flow:
    1) Decode QR from image
    2) Extract URLs
    3) Scan URLs only (no text analysis)
    Returns:
        {
          "decoded_items": [
            {
                    "decoded_content": "https://example.com/login?from=qr",
                    # The original text of the QR code (it could be a URL or a URL plus other text)
                    "urls": [
                        "https://example.com/login?from=qr"
                    ]
            }
          ],
          "qr_urls": [...],
          # The input directly used for subsequent URL risk detection
          "url_analysis": [...],
        }
    """
    # 1) Decode QR in threadpool (OpenCV is sync CPU work)
    qr_items = await run_in_threadpool(vision_service.detect_qr_codes, qr_file)
    # qr_items expected format:
    # [
    #   {"decoded_content": "...", "urls": ["https://..."]},
    #   ...
    # ]

    # 2) Flatten + deduplicate URLs
    qr_urls: list[str] = []
    for item in qr_items:
        qr_urls.extend(item.get("urls", []))
    qr_urls = list(dict.fromkeys(qr_urls))  # keep order, remove duplicates

    # 3) URL-only analysis (rrf_score, no change)
    url_analysis = []
    for url in qr_urls:
        url_analysis.append(await nlp_service.scan_url(url))

    # 4) Analysis results of the URL tool
    report_tasks = [get_url_report(url) for url in qr_urls]
    # return_exceptions=True If a certain task fails, it will not cause the program to crash.
    # It will treat that incorrect Exception object (Exception) as a result and place it in the list,
    # while the successful task still returns a normal detection report.
    report_results = await asyncio.gather(*report_tasks, return_exceptions=True)

    url_report_analysis = []
    for u, r in zip(qr_urls, report_results):
        if isinstance(r, Exception):
            url_report_analysis.append(
                {
                    "Website Address": u,
                    "Error": f"Program exception: {r!s}",
                }
            )
        else:
            url_report_analysis.append(r)

    return {
        "decoded_items": qr_items,
        "qr_urls": qr_urls,
        "url_analysis": url_analysis,
        "url_report_analysis": url_report_analysis,
    }
