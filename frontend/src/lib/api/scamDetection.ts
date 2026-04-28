import type { ScamDetectionInput, ScamDetectionResult } from "@lib/types";
import { APP_CONFIG } from "@lib/config/app";
import { mockCases } from "@lib/constants/cases";
import { logger } from "@lib/utils/logger";

/**
 * POST /api/v1/detection/scan — multipart `text` and/or `file`.
 * Score comes from `unified_text_analysis.text_data.risk_score` (your API shape).
 */
export async function detectScam(
  input: ScamDetectionInput,
): Promise<ScamDetectionResult> {
  logger.info("detectScam called", { type: input.type });
  try {
    const formData = new FormData();
    if (typeof input.content === "string") {
      formData.append("text", input.content);
    } else {
      formData.append("file", input.content);
    }

    const endpoint = `${APP_CONFIG.api.baseUrl.replace(/\/$/, "")}/v1/detection/scan`;
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { Accept: "application/json" },
      body: formData,
    });

    if (!response.ok) {
      const detail = await tryReadError(response);
      throw new Error(
        detail ?? `Detection request failed (${response.status})`,
      );
    }

    const raw = (await response.json()) as unknown;
    const result = mapScanResponse(raw, input);
    logger.info("detectScam completed", { score: result.score });
    return result;
  } catch (e) {
    logger.error("detectScam failed", e instanceof Error ? e : undefined);
    throw e instanceof Error ? e : new Error("Detection failed");
  }
}

function mapScanResponse(
  raw: unknown,
  input: ScamDetectionInput,
): ScamDetectionResult {
  const textData = getTextData(raw);
  const riskRaw = textData?.risk_score ?? getRrfTopScore(raw);
  const score = toScorePercent(riskRaw);

  const category =
    typeof textData?.category === "string" && textData.category.trim()
      ? textData.category.trim()
      : "unknown";

  const clean =
    typeof textData?.clean_text === "string" && textData.clean_text.trim()
      ? textData.clean_text.trim()
      : null;
  const explanation =
    clean && clean.length > 200
      ? `${clean.slice(0, 200)}…`
      : (clean ?? `Scam check completed for ${input.type}.`);

  return {
    score,
    riskLevel: toRiskLevel(score),
    explanation,
    scamType: category,
    timestamp: new Date().toISOString(),
    submittedUrl: input.type === "url" ? String(input.content) : undefined,
    qrDecodedContent:
      input.type === "qr" ? "https://secure-payment-check.example" : undefined,
    qrContentType: input.type === "qr" ? "url" : undefined,
    suspiciousItems: getSuspiciousItems(clean),
    guidance: getGuidance(category),
    relatedCase: mockCases.find((c) => c.scamType === category),
  };
}

function getSuspiciousItems(clean: string | null): ScamDetectionResult["suspiciousItems"] {
  if (!clean) return [];
  const seeds = [
    { text: "urgent", reason: "Creates pressure to act without verification." },
    { text: "otp", reason: "Requests one-time password or verification code." },
    { text: "bank", reason: "Asks for sensitive banking information." },
    { text: "click", reason: "Pushes user to open unknown links immediately." },
    { text: "verify", reason: "Impersonates account verification workflow." },
  ];
  const lowered = clean.toLowerCase();
  return seeds.filter((s) => lowered.includes(s.text)).slice(0, 5);
}

function getGuidance(category: string): string[] {
  if (category.includes("job")) {
    return [
      "Do not pay any fees or make any transfers.",
      "Do not share your bank details or OTP codes.",
      "Verify the offer through the company official website.",
    ];
  }
  return [
    "Do not click unknown links or open unexpected files.",
    "Verify requests through official channels before responding.",
    "Report suspicious content and block the sender immediately.",
  ];
}

function getTextData(raw: unknown): Record<string, unknown> | null {
  if (!raw || typeof raw !== "object") return null;
  const unified = (raw as Record<string, unknown>).unified_text_analysis;
  if (!unified || typeof unified !== "object") return null;
  const textData = (unified as Record<string, unknown>).text_data;
  if (!textData || typeof textData !== "object") return null;
  return textData as Record<string, unknown>;
}

/** Fallback score from `unified_text_analysis.text_data.rrf_features[0]` (0-1 range). */
function getRrfTopScore(raw: unknown): number | null {
  const textData = getTextData(raw);
  if (!textData) return null;
  const rrf = textData.rrf_features;
  if (!Array.isArray(rrf) || rrf.length === 0) return null;
  const first = rrf[0];
  if (typeof first === "number" && Number.isFinite(first)) return first * 100;
  if (typeof first === "string") {
    const n = Number(first);
    if (Number.isFinite(n)) return n * 100;
  }
  return null;
}

/** Backend `risk_score`: 0–100 or 0–1; missing → 0 */
function toScorePercent(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    const scaled = value <= 1 ? value * 100 : value;
    return Math.max(0, Math.min(100, Math.round(scaled)));
  }
  if (typeof value === "string") {
    const n = Number(value);
    if (Number.isFinite(n)) return toScorePercent(n);
  }
  return 0;
}

function toRiskLevel(score: number): ScamDetectionResult["riskLevel"] {
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

async function tryReadError(response: Response): Promise<string | null> {
  try {
    const data = (await response.json()) as unknown;
    if (data && typeof data === "object" && "detail" in data) {
      const detail = (data as { detail?: unknown }).detail;
      if (typeof detail === "string" && detail.trim()) return detail;
    }
    return null;
  } catch {
    return null;
  }
}
