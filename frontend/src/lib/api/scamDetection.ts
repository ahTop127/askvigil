import type {
  ScamDetectionInput,
  ScamDetectionResult,
  UrlHeatmapFusionWeights,
} from "@lib/types";
import { APP_CONFIG } from "@lib/config/app";
import { logger } from "@lib/utils/logger";
import { isValidUrl } from "@lib/utils/validation";
import { buildUrlMetaHighlights } from "@lib/utils/urlMetaFeatures";
import {
  parseUrlTokenHeatmap,
  standardizeUrlForHeatmap,
} from "@lib/utils/urlHeatmapDisplay";
import { ensureSessionId } from "@lib/api/session";

/**
 * POST /api/v1/detection/scan — multipart `text` and/or `file`.
 * Score comes from `unified_text_analysis.text_data.risk_score` (your API shape).
 */
export async function detectScam(
  input: ScamDetectionInput,
): Promise<ScamDetectionResult> {
  logger.info("detectScam called", { type: input.type });
  try {
    /** Resolve session_id before building FormData so every scan carries the id. */
    const sessionId = await ensureSessionId();

    const formData = new FormData();
    const inputType = resolveInputType(input);
    formData.append("input_type", inputType);
    if (typeof input.content === "string") {
      formData.append("text", input.content);
    } else {
      formData.append("file", input.content);
    }
    if (sessionId) {
      formData.append("session_id", sessionId);
    }

    const endpoint = `${APP_CONFIG.api.baseUrl.replace(/\/$/, "")}/v1/detection/scan`;
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { Accept: "application/json" },
      credentials: "include",
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

function resolveInputType(
  input: ScamDetectionInput,
): "text" | "image" | "url" | "qr" {
  if (input.type === "qr") return "qr";
  if (input.type === "image") return "image";
  if (input.submissionChannel === "url_tab") return "url";
  return "text";
}

/** URL tab sends `type: "text"`; derive displayed link from a lone URL string. */
function submittedUrlFromInput(input: ScamDetectionInput): string | undefined {
  if (typeof input.content !== "string") return undefined;
  const trimmed = input.content.trim();
  if (!trimmed) return undefined;
  if (input.type === "url") return trimmed;
  if (input.type === "text" && !trimmed.includes("\n") && isValidUrl(trimmed)) {
    return trimmed;
  }
  return undefined;
}

function parseHeatmapFusion(
  fusionBreakdown: unknown,
): UrlHeatmapFusionWeights | undefined {
  if (!fusionBreakdown || typeof fusionBreakdown !== "object") return undefined;
  const o = fusionBreakdown as Record<string, unknown>;
  const wx = toNumberOrNull(o.effective_xgb_weight);
  const wd = toNumberOrNull(o.effective_db_weight);
  if (wx === null || wd === null) return undefined;
  return {
    effective_xgb_weight: Math.max(0, Math.min(1, wx)),
    effective_db_weight: Math.max(0, Math.min(1, wd)),
  };
}

function parseUrlHeatmapFusion(
  unifiedEntry: QrUrlAnalysisLike | null,
): UrlHeatmapFusionWeights | undefined {
  if (!unifiedEntry) return undefined;
  return parseHeatmapFusion(unifiedEntry.explainability?.fusion_breakdown);
}

function extractTextHeatmapFromAnalysis(
  textAnalysis: TextAnalysisLike | null,
  fallbackBase?: string,
): Pick<
  ScamDetectionResult,
  "textTokenHeatmap" | "textHeatmapBaseText" | "textHeatmapFusion"
> {
  if (!textAnalysis) return {};
  const wx = textAnalysis.weightage_explainability;
  const parsed = parseUrlTokenHeatmap(wx?.token_heatmap);
  const fromApi = asNonEmptyString(textAnalysis["input text"])?.trim();
  const base = fromApi || fallbackBase?.trim();
  const fusion = parseHeatmapFusion(wx?.fusion_breakdown);
  if (!base || parsed.length === 0) return {};
  const filtered = parsed.filter(
    (e) =>
      e.start_char >= 0 &&
      e.end_char <= base.length &&
      e.start_char < e.end_char,
  );
  if (filtered.length === 0) return {};
  return {
    textTokenHeatmap: filtered,
    textHeatmapBaseText: base,
    ...(fusion ? { textHeatmapFusion: fusion } : {}),
  };
}

function extractUrlHeatmapFromUnified(
  unifiedEntry: QrUrlAnalysisLike | null,
): Pick<
  ScamDetectionResult,
  "urlTokenHeatmap" | "urlHeatmapBaseUrl" | "urlHeatmapFusion"
> {
  if (!unifiedEntry) return {};
  const raw = unifiedEntry.explainability?.token_heatmap;
  const parsed = parseUrlTokenHeatmap(raw);
  const resolved = asNonEmptyString(unifiedEntry.resolved_url)?.trim();
  const fusion = parseUrlHeatmapFusion(unifiedEntry);
  if (!resolved || parsed.length === 0) return {};
  const base = standardizeUrlForHeatmap(resolved);
  const filtered = parsed.filter(
    (e) =>
      e.start_char >= 0 &&
      e.end_char <= base.length &&
      e.start_char < e.end_char,
  );
  if (filtered.length === 0) return {};
  return {
    urlTokenHeatmap: filtered,
    urlHeatmapBaseUrl: base,
    ...(fusion ? { urlHeatmapFusion: fusion } : {}),
  };
}

function mapScanResponse(
  raw: unknown,
  input: ScamDetectionInput,
): ScamDetectionResult {
  if (input.type === "qr") {
    return mapQrScanResponse(raw);
  }

  const textAnalysis = getTextAnalysis(raw);
  const legacyTextData = getLegacyTextData(raw);
  const unifiedUrlEntry = resolveUnifiedUrlBranch(raw);
  const overallRiskScore = toNumberOrNull(getOverallRiskScore(raw));
  const baseRiskRaw =
    textAnalysis?.risk_score_percent ??
    textAnalysis?.risk_score ??
    legacyTextData?.risk_score ??
    getLegacyRrfTopScore(raw);
  /** Mixed textarea + URL branch: headline score = text_analysis only; URL tab uses url_analysis[]. */
  const dualTextUrlCandidate =
    input.type === "text" &&
    input.submissionChannel !== "url_tab" &&
    textAnalysis !== null &&
    unifiedUrlEntry !== null;
  /** Paste-URL strip (and QR-less URL-only UX): merge overall_risk_score when URL branch exists. */
  const mergeOverallIntoHeadlineScore =
    unifiedUrlEntry !== null &&
    !dualTextUrlCandidate &&
    overallRiskScore !== null &&
    overallRiskScore !== -1;
  const riskRaw = mergeOverallIntoHeadlineScore
    ? overallRiskScore
    : baseRiskRaw;
  const score = toScorePercent(riskRaw);

  const category = normalizeScamType(
    asNonEmptyString(textAnalysis?.scam_type?.predicted_type) ??
      asNonEmptyString(legacyTextData?.category) ??
      "unknown",
  );

  const clean = asNonEmptyString(legacyTextData?.clean_text);
  const summary = asNonEmptyString(textAnalysis?.immediate_guidance?.summary);
  const indicatorReasons = getIndicatorReasons(
    textAnalysis?.explainability?.matched_indicators,
  );
  const explanation =
    summary ??
    (indicatorReasons && indicatorReasons.length > 200
      ? `${indicatorReasons.slice(0, 200)}...`
      : indicatorReasons) ??
    (clean && clean.length > 200 ? `${clean.slice(0, 200)}…` : clean) ??
    `Scam check completed for ${input.type}.`;

  const urlMetaFeatures = unifiedUrlEntry
    ? buildUrlMetaHighlights(
        unifiedUrlEntry.meta_labels,
        unifiedUrlEntry.meta_vector,
      )
    : [];

  const isUrlStripSubmission =
    input.submissionChannel === "url_tab" && typeof input.content === "string";

  /** Text-area message with URL branch: backend must return both NLP text analysis and url_analysis. */
  const dualTextUrlDetection = dualTextUrlCandidate;

  let urlDetectionSummary: ScamDetectionResult["urlDetectionSummary"];
  if (dualTextUrlDetection && unifiedUrlEntry) {
    const resolvedRaw = asNonEmptyString(unifiedUrlEntry.resolved_url)?.trim();
    const displayUrl =
      resolvedRaw && isValidUrl(resolvedRaw) ? resolvedRaw : "";
    const branchScore = toScorePercent(unifiedUrlEntry.risk_score ?? 0);
    const branchMeta = buildUrlMetaHighlights(
      unifiedUrlEntry.meta_labels,
      unifiedUrlEntry.meta_vector,
    );
    urlDetectionSummary = {
      displayUrl,
      urlRiskScore: branchScore,
      urlRiskLevel: toRiskLevel(branchScore),
      urlMetaFeatures: branchMeta.length > 0 ? branchMeta : undefined,
    };
  }

  /** Link row / paste-URL UX only when backend returned a real url_analysis payload. */
  const submittedUrl = ((): string | undefined => {
    if (!unifiedUrlEntry) return undefined;
    if (isUrlStripSubmission) {
      const t = typeof input.content === "string" ? input.content.trim() : "";
      return t && isValidUrl(t) ? t : undefined;
    }
    return submittedUrlFromInput(input);
  })();

  const { urlTokenHeatmap, urlHeatmapBaseUrl, urlHeatmapFusion } =
    extractUrlHeatmapFromUnified(unifiedUrlEntry);

  const inputTextBase =
    input.type === "text" && typeof input.content === "string"
      ? input.content.trim()
      : undefined;
  const { textTokenHeatmap, textHeatmapBaseText, textHeatmapFusion } =
    extractTextHeatmapFromAnalysis(textAnalysis, inputTextBase);

  return {
    score,
    riskLevel: toRiskLevel(score),
    explanation,
    scamType: category,
    timestamp: new Date().toISOString(),
    overallRiskScore: overallRiskScore ?? undefined,
    extractedText: clean ?? undefined,
    submittedUrl,
    qrDecodedContent: undefined,
    qrContentType: undefined,
    dualTextUrlDetection: dualTextUrlDetection ? true : undefined,
    urlDetectionSummary,
    urlMetaFeatures: dualTextUrlDetection
      ? undefined
      : urlMetaFeatures.length > 0
        ? urlMetaFeatures
        : undefined,
    suspiciousItems: getSuspiciousItems(
      textAnalysis?.explainability?.matched_indicators,
      clean,
    ),
    guidance: getGuidance(textAnalysis?.immediate_guidance, category),
    immediateGuidanceTitle:
      asNonEmptyString(textAnalysis?.immediate_guidance?.title) ?? undefined,
    immediateGuidanceSummary: summary ?? undefined,
    immediateGuidanceDontDo: toStringList(
      textAnalysis?.immediate_guidance?.dont_do,
    ),
    immediateGuidanceSaferAction: toStringList(
      textAnalysis?.immediate_guidance?.safer_action,
    ),
    urlTokenHeatmap,
    urlHeatmapBaseUrl,
    urlHeatmapFusion,
    textTokenHeatmap,
    textHeatmapBaseText,
    textHeatmapFusion,
    originalText: inputTextBase || undefined,
  };
}

function mapQrScanResponse(raw: unknown): ScamDetectionResult {
  const qr = getQrModal(raw);
  const firstAnalysis = qr?.url_analysis?.[0] ?? null;
  const firstDecoded = qr?.decoded_items?.[0] ?? null;
  const decodedContent =
    asNonEmptyString(firstDecoded?.decoded_content) ??
    asNonEmptyString(qr?.qr_urls?.[0]) ??
    null;

  const riskRaw = firstAnalysis?.risk_score ?? 0;
  const score = toScorePercent(riskRaw);
  const decision = asNonEmptyString(firstAnalysis?.decision)?.toLowerCase();
  const isFlagged = decision === "flagged" || score >= 70;
  const qrReportAnalysis =
    extractQrReportAnalysis(qr?.url_report_analysis) ??
    extractQrReportAnalysis(firstAnalysis);

  return {
    score,
    riskLevel: toRiskLevel(score),
    explanation: isFlagged
      ? "This QR code points to a potentially risky URL. Verify the destination before opening it."
      : "No obvious high-risk signals were found in the decoded QR URL, but stay cautious before sharing information.",
    scamType: "unknown",
    timestamp: new Date().toISOString(),
    qrDecodedContent: decodedContent ?? undefined,
    qrContentType: decodedContent ? "url" : undefined,
    qrUrlReportAnalysis: qrReportAnalysis ?? undefined,
    suspiciousItems: isFlagged
      ? [
          {
            text: decodedContent ?? "decoded-url",
            reason:
              "The decoded URL risk analysis indicates suspicious characteristics.",
          },
        ]
      : [],
    guidance: [
      "Do not enter passwords, OTP, or bank details unless the website is verified.",
      "Check the domain carefully and avoid shortened or unfamiliar links.",
      "Open the URL only after confirming it through official channels.",
    ],
  };
}

function extractQrReportAnalysis(
  source: QrUrlAnalysisLike | unknown,
): Record<string, unknown> | Record<string, unknown>[] | null {
  if (!source) return null;
  let report: unknown = null;

  if (Array.isArray(source)) {
    report = source;
  } else if (typeof source === "object") {
    const sourceObject = source as Record<string, unknown>;
    if (
      sourceObject.rl_report_analysis !== undefined ||
      sourceObject.url_report_analysis !== undefined
    ) {
      report =
        sourceObject.rl_report_analysis ?? sourceObject.url_report_analysis;
    } else {
      const looksLikeUrlAnalysis =
        sourceObject.risk_score !== undefined ||
        sourceObject.decision !== undefined ||
        sourceObject.resolved_url !== undefined ||
        sourceObject.resolved_successfully !== undefined;
      report = looksLikeUrlAnalysis ? null : sourceObject;
    }
  }

  if (!report) return null;

  if (Array.isArray(report)) {
    const rows = report.filter(
      (item): item is Record<string, unknown> =>
        !!item && typeof item === "object",
    );
    return rows.length > 0 ? rows : null;
  }

  if (typeof report === "object") {
    return report as Record<string, unknown>;
  }

  return null;
}

function getSuspiciousItems(
  indicators: IndicatorLike[] | undefined,
  clean: string | null,
): ScamDetectionResult["suspiciousItems"] {
  if (Array.isArray(indicators) && indicators.length > 0) {
    return indicators
      .map((item) => {
        const terms = Array.isArray(item.matched_terms)
          ? item.matched_terms.filter(
              (t): t is string => typeof t === "string" && t.trim(),
            )
          : [];
        const reason = asNonEmptyString(item.reason);
        if (!reason) return null;
        return {
          text:
            terms.length > 0
              ? terms.join(", ")
              : (item.category ?? "indicator"),
          reason,
        };
      })
      .filter((x): x is { text: string; reason: string } => x !== null)
      .slice(0, 5);
  }

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

function getGuidance(
  immediate: ImmediateGuidanceLike | undefined,
  category: string,
): string[] {
  const dontDo = Array.isArray(immediate?.dont_do)
    ? immediate.dont_do.filter(
        (x): x is string => typeof x === "string" && x.trim(),
      )
    : [];
  const saferAction = Array.isArray(immediate?.safer_action)
    ? immediate.safer_action.filter(
        (x): x is string => typeof x === "string" && x.trim(),
      )
    : [];
  const merged = [...dontDo, ...saferAction];
  if (merged.length > 0) return merged;

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

interface ImmediateGuidanceLike {
  title?: unknown;
  summary?: unknown;
  dont_do?: unknown;
  safer_action?: unknown;
}

interface IndicatorLike {
  category?: string;
  matched_terms?: unknown;
  reason?: unknown;
}

interface QrUrlAnalysisLike {
  risk_score?: unknown;
  decision?: unknown;
  resolved_url?: unknown;
  url_report_analysis?: unknown;
  rl_report_analysis?: unknown;
  meta_labels?: unknown;
  meta_vector?: unknown;
  explainability?: {
    token_heatmap?: unknown;
    fusion_breakdown?: unknown;
  };
}

interface QrDecodedItemLike {
  decoded_content?: unknown;
  urls?: unknown;
}

interface TextAnalysisLike {
  risk_score?: unknown;
  risk_score_percent?: unknown;
  scam_type?: {
    predicted_type?: unknown;
  };
  explainability?: {
    matched_indicators?: IndicatorLike[];
  };
  weightage_explainability?: {
    token_heatmap?: unknown;
    fusion_breakdown?: unknown;
  };
  "input text"?: unknown;
  immediate_guidance?: ImmediateGuidanceLike;
}

function getTextAnalysis(raw: unknown): TextAnalysisLike | null {
  const unified = getUnifiedTextAnalysis(raw);
  if (!unified) return null;
  const textAnalysis = unified.text_analysis;
  if (!textAnalysis || typeof textAnalysis !== "object") return null;
  return textAnalysis as TextAnalysisLike;
}

function getQrModal(raw: unknown): {
  url_analysis?: QrUrlAnalysisLike[];
  decoded_items?: QrDecodedItemLike[];
  qr_urls?: string[];
  url_report_analysis?: unknown;
} | null {
  if (!raw || typeof raw !== "object") return null;
  const modalities = (raw as Record<string, unknown>).modalities;
  if (!modalities || typeof modalities !== "object") return null;
  const qr = (modalities as Record<string, unknown>).qr;
  if (!qr || typeof qr !== "object") return null;

  const qrObj = qr as Record<string, unknown>;
  return {
    url_analysis: Array.isArray(qrObj.url_analysis)
      ? (qrObj.url_analysis as QrUrlAnalysisLike[])
      : [],
    decoded_items: Array.isArray(qrObj.decoded_items)
      ? (qrObj.decoded_items as QrDecodedItemLike[])
      : [],
    qr_urls: Array.isArray(qrObj.qr_urls)
      ? qrObj.qr_urls.filter((x): x is string => typeof x === "string")
      : [],
    url_report_analysis: qrObj.url_report_analysis ?? qrObj.rl_report_analysis,
  };
}

function getLegacyTextData(raw: unknown): Record<string, unknown> | null {
  const unified = getUnifiedTextAnalysis(raw);
  if (!unified) return null;
  const textData = unified.text_data;
  if (!textData || typeof textData !== "object") return null;
  return textData as Record<string, unknown>;
}

function getUnifiedTextAnalysis(raw: unknown): Record<string, unknown> | null {
  if (!raw || typeof raw !== "object") return null;
  const unified = (raw as Record<string, unknown>).unified_text_analysis;
  if (!unified || typeof unified !== "object") return null;
  return unified as Record<string, unknown>;
}

/** First entry from `unified_text_analysis.url_analysis` (URL branch of unified scan). */
function getFirstUnifiedUrlAnalysis(raw: unknown): QrUrlAnalysisLike | null {
  const unified = getUnifiedTextAnalysis(raw);
  if (!unified) return null;
  const arr = unified.url_analysis;
  if (!Array.isArray(arr) || arr.length === 0) return null;
  const first = arr[0];
  if (!first || typeof first !== "object") return null;
  return first as QrUrlAnalysisLike;
}

/** Backend returned a substantive URL row — not merely an empty array. */
function unifiedUrlBranchHasPayload(entry: QrUrlAnalysisLike): boolean {
  const resolved = asNonEmptyString(entry.resolved_url)?.trim();
  if (resolved && isValidUrl(resolved)) return true;
  const rs = entry.risk_score;
  if (typeof rs === "number" && Number.isFinite(rs)) return true;
  if (typeof rs === "string" && rs.trim()) {
    const n = Number(rs);
    if (Number.isFinite(n)) return true;
  }
  if (Array.isArray(entry.meta_labels) && entry.meta_labels.length > 0) {
    return true;
  }
  return false;
}

/** Enables URL-branch mapping only when `url_analysis[0]` carries analyzable scores/meta or a usable URL. */
function resolveUnifiedUrlBranch(raw: unknown): QrUrlAnalysisLike | null {
  const first = getFirstUnifiedUrlAnalysis(raw);
  if (!first) return null;
  return unifiedUrlBranchHasPayload(first) ? first : null;
}

function getOverallRiskScore(raw: unknown): unknown {
  const unified = getUnifiedTextAnalysis(raw);
  if (!unified) return null;
  return unified.overall_risk_score;
}

/** Fallback score from `unified_text_analysis.text_data.rrf_features[0]` (0-1 range). */
function getLegacyRrfTopScore(raw: unknown): number | null {
  const textData = getLegacyTextData(raw);
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

function asNonEmptyString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function getIndicatorReasons(
  indicators: IndicatorLike[] | undefined,
): string | null {
  if (!Array.isArray(indicators) || indicators.length === 0) return null;
  const reasons = indicators
    .map((item) => asNonEmptyString(item.reason))
    .filter((x): x is string => x !== null);
  if (reasons.length === 0) return null;
  return reasons.join(" ");
}

function normalizeScamType(value: string): string {
  const normalized = value.trim().toLowerCase().replace(/\s+/g, " ");
  const compact = normalized.replace(/[\s-]+/g, "_");
  // Contract output set is still only 3 classes; this just tolerates format drift.
  if (
    compact === "job_scam" ||
    compact === "job_scams" ||
    normalized.startsWith("job scam")
  ) {
    return "job-scam";
  }
  if (compact === "phishing" || normalized.startsWith("phishing")) {
    return "phishing";
  }
  if (
    compact === "otp_scam" ||
    compact === "otp_scams" ||
    normalized.startsWith("otp scam") ||
    normalized.includes("one-time password") ||
    normalized.includes("one time password")
  ) {
    return "otp-scam";
  }
  return "unknown";
}

function toStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((x): x is string => typeof x === "string" && x.trim());
}

function toNumberOrNull(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const n = Number(value);
    if (Number.isFinite(n)) return n;
  }
  return null;
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
