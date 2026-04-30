from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from app.services import nlp_service, vision_service, audio_service
from typing import Literal


async def scan_universal_input(
    file: UploadFile = None,
    text: str = None,
    input_type: Literal["text", "image", "audio", "video", "qr", "auto"] = "auto",
):
    """The Master Entry Point with cascading text aggregation."""
    results = {"modalities": {}, "unified_text_analysis": None}
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

        if "video" in mime:
            vid_res, vid_text = await _handle_video_flow(file)
            results["modalities"]["video"] = vid_res
            if vid_text:
                accumulated_text.append(vid_text)

        elif "image" in mime:
            img_res, img_text = await _handle_image_flow(file)
            results["modalities"]["image"] = img_res
            if img_text:
                accumulated_text.append(img_text)

        elif "audio" in mime:
            aud_res, aud_text = await audio_service.scan_audio(file)
            results["modalities"]["audio"] = aud_res
            if aud_text:
                accumulated_text.append(aud_text)

    # Execution Layer: Unified Text Scanning
    if accumulated_text:
        # Join multiple text sources with a newline to preserve logical separation
        combined_text = "\n".join(accumulated_text)
        results["unified_text_analysis"] = await nlp_service.scan_unified_text(
            combined_text
        )

    return results


async def _handle_video_flow(video_file: UploadFile):
    # 1. Extraction
    audio_path = vision_service.extract_audio_from_video(video_file)
    frame_generator = vision_service.extract_frames(video_file)

    # 2. Execution
    audio_results, audio_text = await audio_service.scan_audio(audio_path)
    video_results = await vision_service.scan_visual_forensics(frame_generator)

    return {"audio": audio_results, "video": video_results}, audio_text


# jiayi: i removed the async here and also changed the input to str for testing purposes, can change back to async and UploadFile later
async def _handle_image_flow(image_file: UploadFile):
    results = {"qr_urls": []}

    # # 1. Look for QR Codes
    # qr_urls = vision_service.detect_qr_codes(image_file)
    # if qr_urls:
    #     results["qr_urls"] = [await nlp_service.scan_url(u) for u in qr_urls]

    # 2. Look for Text via OCR which is implemented in the vision service file
    # Run in async so we don't hog the server
    extracted_text = await run_in_threadpool(
        vision_service.extract_ocr_text, image_file
    )

    # optional for testing
    # print(f"Extracted OCR Text: {extracted_text}")

    return results, extracted_text


# if you wanna test uncomment this
# result_test = _handle_image_flow("OCR_TEST_EN.png")


async def _handle_qr_flow(qr_file: UploadFile):
    """
    QR-only flow:
    1) Decode QR from image
    2) Extract URLs
    3) Scan URLs only (no text analysis)
    Returns:
        {
          "decoded_items": [...],
          "qr_urls": [...],
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

    # 3) URL-only analysis
    url_analysis = []
    for url in qr_urls:
        url_analysis.append(await nlp_service.scan_url(url))
    return {
        "decoded_items": qr_items,
        "qr_urls": qr_urls,
        "url_analysis": url_analysis,
    }
