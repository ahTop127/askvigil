from decimal import Decimal, ROUND_HALF_UP
from typing import Any
import hashlib
import os


def _to_decimal_2(v: Any) -> Decimal | None:
    if v is None:
        return None
    try:
        return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return None


def _encrypt_text(raw: str | None) -> str | None:
    if not raw:
        return None
    salt = os.getenv("INPUT_CONTENT_SALT", "")
    return hashlib.sha256(f"{salt}:{raw}".encode("utf-8")).hexdigest()


def _extract_text_branch(result: dict, fallback_text: str | None) -> dict:
    """
    text/image:
    - risk_score 取 risk_score_percent（优先）/ risk_score*100 / overall_risk_score*100
    - input_content 取 text_analysis['input text']，再哈希
    """
    uta = result.get("unified_text_analysis") or {}
    ta = uta.get("text_analysis") or {}

    rsp = ta.get("risk_score_percent")
    if rsp is not None:
        risk_score = _to_decimal_2(rsp)
    else:
        rs = ta.get("risk_score")
        if rs is not None:
            risk_score = _to_decimal_2(Decimal(str(rs)) * Decimal("100"))
        else:
            overall = uta.get("overall_risk_score")
            risk_score = (
                _to_decimal_2(Decimal(str(overall)) * Decimal("100"))
                if overall is not None and overall != -1
                else None
            )

    plain_text = ta.get("input text") or fallback_text
    return {
        "input_content": _encrypt_text(plain_text),
        "risk_score": risk_score,
    }


def _extract_url_rows_for_url_input(result: dict) -> list[dict]:
    """
    url:
    result['unified_text_analysis']['url_analysis'] -> 多行
    """
    uta = result.get("unified_text_analysis") or {}
    url_analysis = uta.get("url_analysis") or []

    rows: list[dict] = []
    for item in url_analysis:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "input_content": item.get("resolved_url") or item.get("input_url"),
                "risk_score": _to_decimal_2(item.get("risk_score")),  # 0~1 原值
            }
        )
    return rows


def _extract_url_rows_for_qr_input(result: dict) -> list[dict]:
    """
    qr:
    result['modalities']['qr']['url_analysis'] -> 多行
    """
    modalities = result.get("modalities") or {}
    qr_modal = modalities.get("qr") or {}
    url_analysis = qr_modal.get("url_analysis") or []

    rows: list[dict] = []
    for item in url_analysis:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "input_content": item.get("resolved_url") or item.get("input_url"),
                "risk_score": _to_decimal_2(item.get("risk_score")),  # 0~1 原值
            }
        )
    return rows


def build_detection_log_rows(
    *,
    input_type: str,  # 必须是 text/image/url/qr 之一
    result: dict,
    raw_text: str | None = None,
) -> list[dict]:
    """
    返回可用于 DetectionLog.create/bulk_create 的 rows（不含 session）
    每个 row: {input_type, input_content, risk_score}
    """
    if input_type in {"text", "image"}:
        single = _extract_text_branch(result, raw_text)
        return [
            {
                "input_type": input_type,
                "input_content": single["input_content"],
                "risk_score": single["risk_score"],
            }
        ]

    if input_type == "url":
        rows = _extract_url_rows_for_url_input(result)
        return [
            {
                "input_type": "url",
                "input_content": r["input_content"],
                "risk_score": r["risk_score"],
            }
            for r in rows
        ]

    if input_type == "qr":
        rows = _extract_url_rows_for_qr_input(result)
        return [
            {
                "input_type": "qr",
                "input_content": r["input_content"],
                "risk_score": r["risk_score"],
            }
            for r in rows
        ]

    # 兜底
    return []
