import { memo, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import {
  AlertCircle,
  Check,
  LoaderCircle,
  Shield,
  TriangleAlert,
} from "lucide-react";
import { Button } from "@components/ui/button";
import { Badge } from "@components/ui/badge";
import { fetchScamCases } from "@lib/api/cases";
import { APP_CONFIG } from "@lib/config/app";
import { UI_TEXT } from "@lib/constants/text";
import type {
  RiskLevel,
  ScamCase,
  ScamDetectionResult,
  UrlMetaFeatureHighlight,
} from "@lib/types";

const RISK_STYLES: Record<
  RiskLevel,
  {
    accent: string;
    score: string;
    badge: string;
    glow: string;
  }
> = {
  high: {
    accent: "bg-red-500",
    score: "text-red-600",
    badge: "bg-red-100 text-red-700 border-red-200",
    glow: "shadow-red-100",
  },
  medium: {
    accent: "bg-amber-500",
    score: "text-amber-600",
    badge: "bg-amber-100 text-amber-700 border-amber-200",
    glow: "shadow-amber-100",
  },
  low: {
    accent: "bg-green-500",
    score: "text-green-600",
    badge: "bg-green-100 text-green-700 border-green-200",
    glow: "shadow-green-100",
  },
};

const URL_META_SEVERITY_STYLES: Record<
  UrlMetaFeatureHighlight["severity"],
  { card: string; badge: string; emphasis: string; labelCell: string }
> = {
  high: {
    card: "border-red-200 bg-red-50/90",
    badge: "border border-red-300 bg-red-100 text-red-800",
    emphasis: "text-red-700",
    labelCell: "bg-red-200 text-black border-r border-red-500/85",
  },
  medium: {
    card: "border-amber-200 bg-amber-50/90",
    badge: "border border-amber-300 bg-amber-100 text-amber-900",
    emphasis: "text-amber-800",
    labelCell: "bg-amber-200 text-black border-r border-amber-500/85",
  },
  low: {
    card: "border-yellow-200 bg-yellow-50/80",
    badge: "border border-yellow-400 bg-yellow-100 text-yellow-900",
    emphasis: "text-yellow-800",
    labelCell: "bg-yellow-200 text-black border-r border-yellow-600/80",
  },
};

/** URL paste flow: score bands match app risk (high ≥70 / medium 40–69 / low &lt;40). */
const URL_ACTION_GUIDANCE_BY_LEVEL: Record<
  RiskLevel,
  { dontDo: string[]; safer: string[] }
> = {
  high: {
    dontDo: [
      "Don't click, type, or share this link — it is highly likely to be a phishing or credential-harvesting site.",
      "Don't enter any passwords, OTP, or bank details if you already opened it.",
    ],
    safer: [
      "Close the tab immediately and do not forward this link to anyone.",
      "If you entered any credentials, change your passwords now and contact your bank's official hotline.",
      "Report this link to your bank's fraud department or the Malaysian Cyber Security Centre (Cyber999).",
    ],
  },
  medium: {
    dontDo: [
      "Don't click this link directly from messages, emails, or WhatsApp groups without verifying.",
      "Don't enter personal information, IC number, or banking details without verifying the domain first.",
    ],
    safer: [
      "Verify the link through official channels before clicking.",
      "Navigate to the brand's official website directly by typing the URL manually (e.g., type maybank2u.com.my instead of clicking).",
      "Cross-check the domain with the official brand's domain — look at the rightmost part of the URL to see who really controls the site.",
    ],
  },
  low: {
    dontDo: [
      "Don't assume a \"safe\" score means you can relax completely — scammers can mimic legitimate structures.",
      "Don't share sensitive information even if the link appears technically safe.",
    ],
    safer: [
      "Double-check the URL and verify the sender's identity before proceeding.",
      "If you received this from an unknown sender, verify the source through other channels before taking any action.",
    ],
  },
};

function mulberry32(seed: number): () => number {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hashGuidanceSeed(parts: string[]): number {
  let h = 2166136261;
  for (const p of parts) {
    for (let i = 0; i < p.length; i++) {
      h ^= p.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
  }
  return h >>> 0;
}

/** Picks 1 or 2 distinct lines when the pool has ≥2; stable RNG via `next`. */
function pickUrlGuidanceSubset(lines: string[], next: () => number): string[] {
  if (lines.length === 0) return [];
  if (lines.length === 1) return [lines[0]];
  const count = next() < 0.5 ? 1 : 2;
  const order = lines.map((_, i) => i);
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(next() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  return order.slice(0, count).map((i) => lines[i]);
}

function urlMetaFeaturesEqual(
  a: ScamDetectionResult["urlMetaFeatures"],
  b: ScamDetectionResult["urlMetaFeatures"],
): boolean {
  if (a === b) return true;
  if (!a || !b || a.length !== b.length) return !a && !b;
  return a.every(
    (item, i) =>
      item.label === b[i]?.label &&
      item.score === b[i]?.score &&
      item.severity === b[i]?.severity &&
      item.explanation === b[i]?.explanation,
  );
}

function urlDetectionSummaryEqual(
  a: ScamDetectionResult["urlDetectionSummary"],
  b: ScamDetectionResult["urlDetectionSummary"],
): boolean {
  if (a === b) return true;
  if (!a || !b) return !a && !b;
  return (
    a.displayUrl === b.displayUrl &&
    a.urlRiskScore === b.urlRiskScore &&
    a.urlRiskLevel === b.urlRiskLevel &&
    urlMetaFeaturesEqual(a.urlMetaFeatures, b.urlMetaFeatures)
  );
}

export interface ResultDisplayProps {
  result: ScamDetectionResult;
  onNewAnalysis: () => void;
}

function isRiskLevel(v: string): v is RiskLevel {
  return v === "high" || v === "medium" || v === "low";
}

function getCaseFilterScamType(scamType: string): string {
  const normalized = scamType.trim().toLowerCase();
  if (normalized === "job_scam" || normalized === "job-scam") return "job-scam";
  if (normalized === "phishing") return "phishing";
  if (normalized === "otp_scam" || normalized === "otp-scam") return "otp-scam";
  return "all";
}

function humanizeReportKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function toReportDisplayValue(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "string") return value.trim() || "-";
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    const compact = value
      .map((item) => toReportDisplayValue(item))
      .filter((v) => v !== "-");
    return compact.length > 0 ? compact.join(", ") : "-";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return "-";
}

function toQrReportRows(
  report:
    | Record<string, unknown>
    | Record<string, unknown>[]
    | undefined,
): Array<{ label: string; value: string }> {
  if (!report) return [];
  const source =
    Array.isArray(report) && report.length > 0
      ? report[0]
      : (report as Record<string, unknown>);
  return Object.entries(source)
    .map(([key, value]) => ({
      label: humanizeReportKey(key),
      value: toReportDisplayValue(value),
    }))
    .filter((row) => row.value !== "-");
}

/**
 * Presents score, risk band, explanation, and optional guidance CTA.
 */
export const ResultDisplay = memo(
  function ResultDisplay({ result, onNewAnalysis }: ResultDisplayProps) {
    const navigate = useNavigate();
    const [showAllFlags, setShowAllFlags] = useState(false);
    const [relatedCase, setRelatedCase] = useState<ScamCase | null>(null);
    const [isRelatedLoading, setIsRelatedLoading] = useState(false);
    const level = isRiskLevel(result.riskLevel) ? result.riskLevel : "low";
    const styles = RISK_STYLES[level];
    const steps = useMemo(() => {
      if (result.steps?.length) return result.steps;
      return [
        { key: "upload", label: "Upload", status: "completed" as const },
        {
          key: "check-risks",
          label: "Check Risks",
          status: "completed" as const,
        },
        { key: "red-flags", label: "Red Flags", status: "completed" as const },
      ];
    }, [result.steps]);
    const suspiciousItems = result.suspiciousItems ?? [];
    const visibleFlags = showAllFlags
      ? suspiciousItems
      : suspiciousItems.slice(0, 5);
    const extraCount = Math.max(0, suspiciousItems.length - 5);
    const noFlags = suspiciousItems.length === 0;
    const scamTypeLabel = result.scamType?.trim() || "Suspicious Content";
    const guidance = result.guidance ?? [
      "Do not click unknown links or open unexpected files.",
      "Verify requests through official channels before responding.",
    ];
    const immediateTitle =
      result.immediateGuidanceTitle?.trim() || "Action Guide";
    const immediateSummary = result.immediateGuidanceSummary?.trim();
    const isUnknownScamType =
      (result.scamType ?? "").trim().toLowerCase() === "unknown";
    const isQrResult = Boolean(result.qrDecodedContent || result.qrContentType);
    const isUrlOrQrResult = Boolean(result.submittedUrl || isQrResult);
    const dualTextUrl =
      Boolean(result.dualTextUrlDetection) &&
      Boolean(result.urlDetectionSummary);
    const [summaryTab, setSummaryTab] = useState<"text" | "url">("text");

    useEffect(() => {
      setSummaryTab("text");
    }, [
      result.timestamp,
      result.score,
      result.dualTextUrlDetection,
      result.urlDetectionSummary?.displayUrl,
    ]);

    /** QR / URL flows (including dual-branch URL tab): do not show scam type badge. */
    const shouldShowScamTypeBadge =
      !isQrResult &&
      result.detectionType !== "qr" &&
      result.detectionType !== "url" &&
      !result.submittedUrl &&
      !(dualTextUrl && summaryTab === "url");

    const shouldShowRelatedCases =
      !result.submittedUrl &&
      !result.qrDecodedContent &&
      (!dualTextUrl || summaryTab === "text");

    const urlBranchLevel =
      result.urlDetectionSummary &&
      isRiskLevel(result.urlDetectionSummary.urlRiskLevel)
        ? result.urlDetectionSummary.urlRiskLevel
        : level;
    const scoreCardLevel =
      dualTextUrl && summaryTab === "url" ? urlBranchLevel : level;
    const scoreCardStyles = RISK_STYLES[scoreCardLevel];
    const scoreCardScore =
      dualTextUrl && summaryTab === "url" && result.urlDetectionSummary
        ? result.urlDetectionSummary.urlRiskScore
        : result.score;

    const showExplanationUnderScore = dualTextUrl
      ? summaryTab === "text"
      : !isUrlOrQrResult;

    const detectedLinkPrimary = dualTextUrl
      ? summaryTab === "url"
        ? result.urlDetectionSummary?.displayUrl?.trim()
        : undefined
      : result.submittedUrl?.trim();
    const showDetectedLinkCard = Boolean(detectedLinkPrimary);
    const notableUrlMeta =
      dualTextUrl && summaryTab === "url"
        ? result.urlDetectionSummary?.urlMetaFeatures
        : result.urlMetaFeatures;

    /** Non–dual-branch: same as legacy URL paste row (`submittedUrl` + merged `level`). */
    const submittedUrlGuidancePick = useMemo(() => {
      const url = result.submittedUrl?.trim();
      if (!url || !isRiskLevel(level)) return null;
      const seed = hashGuidanceSeed([
        url,
        result.timestamp,
        String(result.score),
        level,
      ]);
      const next = mulberry32(seed);
      const pool = URL_ACTION_GUIDANCE_BY_LEVEL[level];
      return {
        dontDo: pickUrlGuidanceSubset(pool.dontDo, next),
        safer: pickUrlGuidanceSubset(pool.safer, next),
      };
    }, [result.submittedUrl, result.timestamp, result.score, level]);

    /** Dual-branch URL tab: same pool + RNG pattern as URL paste, keyed by branch URL/score/tier. */
    const dualUrlTabGuidancePick = useMemo(() => {
      if (!result.dualTextUrlDetection || !result.urlDetectionSummary) {
        return null;
      }
      const sum = result.urlDetectionSummary;
      const uLevel = isRiskLevel(sum.urlRiskLevel)
        ? sum.urlRiskLevel
        : level;
      const seed = hashGuidanceSeed([
        sum.displayUrl.trim() || "url-branch",
        result.timestamp,
        String(sum.urlRiskScore),
        uLevel,
      ]);
      const next = mulberry32(seed);
      const pool = URL_ACTION_GUIDANCE_BY_LEVEL[uLevel];
      return {
        dontDo: pickUrlGuidanceSubset(pool.dontDo, next),
        safer: pickUrlGuidanceSubset(pool.safer, next),
      };
    }, [
      result.dualTextUrlDetection,
      result.timestamp,
      result.urlDetectionSummary?.displayUrl,
      result.urlDetectionSummary?.urlRiskScore,
      result.urlDetectionSummary?.urlRiskLevel,
      level,
    ]);

    /** Dual text tab: behave like plain text result (no URL-line guidance). URL tab: URL-style guidance. */
    const urlGuidancePick = dualTextUrl
      ? summaryTab === "url"
        ? dualUrlTabGuidancePick
        : null
      : submittedUrlGuidancePick;

    const dontDoItems =
      urlGuidancePick?.dontDo ??
      (result.immediateGuidanceDontDo &&
      result.immediateGuidanceDontDo.length > 0
        ? result.immediateGuidanceDontDo
        : guidance.slice(0, 2));
    const saferActionItems =
      urlGuidancePick?.safer ??
      (result.immediateGuidanceSaferAction &&
      result.immediateGuidanceSaferAction.length > 0
        ? result.immediateGuidanceSaferAction
        : guidance.slice(2, 5));
    const urlActionGuideTwoColumn =
      urlGuidancePick !== null || !isUnknownScamType;
    const showUrlAwareDontDoPanel =
      urlGuidancePick !== null || !isUnknownScamType;
    const caseFilterScamType = useMemo(
      () => getCaseFilterScamType(result.scamType || ""),
      [result.scamType],
    );
    const qrReportRows = useMemo(
      () => toQrReportRows(result.qrUrlReportAnalysis),
      [result.qrUrlReportAnalysis],
    );

    useEffect(() => {
      let cancelled = false;
      if (caseFilterScamType === "all") {
        setRelatedCase(null);
        setIsRelatedLoading(false);
        return;
      }
      setIsRelatedLoading(true);
      fetchScamCases({
        scamType: caseFilterScamType,
        platform: "all",
        date: "all",
      })
        .then((items) => {
          if (!cancelled) setRelatedCase(items[0] ?? null);
        })
        .catch(() => {
          if (!cancelled) setRelatedCase(null);
        })
        .finally(() => {
          if (!cancelled) setIsRelatedLoading(false);
        });
      return () => {
        cancelled = true;
      };
    }, [caseFilterScamType]);

    return (
      <div className="space-y-6">
        <div
          className="relative overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm"
          role="region"
          aria-label={`Detection result: ${scoreCardLevel} risk, score ${scoreCardScore}`}
        >
          <div className="overflow-hidden border-b border-[#8ed6ce] bg-white shadow-sm">
            <div className="bg-[#223C61] px-5 py-3">
              <h3 className="text-lg font-semibold text-white">
                {result.qrDecodedContent || qrReportRows.length > 0
                  ? "URL Report Summary"
                  : "Detection Summary"}
              </h3>
            </div>
            <div className="border-b border-[#d9efec] px-5 py-3">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
                  {steps.map((step) => (
                    <div
                      key={step.key}
                      className={`inline-flex items-center gap-1.5 text-sm font-semibold tracking-wide ${
                        step.status === "pending"
                          ? "text-gray-400"
                          : step.status === "failed"
                            ? "text-red-600"
                            : "text-gray-700"
                      }`}
                    >
                      {step.status === "completed" && (
                        <Check className="h-4 w-4 text-emerald-600" />
                      )}
                      {step.status === "current" && (
                        <LoaderCircle className="h-4 w-4 animate-spin text-primary" />
                      )}
                      {step.status === "failed" && (
                        <TriangleAlert className="h-4 w-4 text-red-600" />
                      )}
                      <span>{step.label}</span>
                    </div>
                  ))}
                </div>
                <Button
                  type="button"
                  onClick={onNewAnalysis}
                  className="h-9 w-[170px] items-end gap-5 rounded-2xl bg-[#283C5E] px-[2px] text-sm font-semibold text-white hover:bg-[#1f314f]"
                >
                  Check Again
                </Button>
              </div>
            </div>
          </div>

          {(result.qrDecodedContent || qrReportRows.length > 0) && (
            <div className="overflow-hidden border-b border-[#8ed6ce] bg-white shadow-sm">
              <div className="p-3 md:p-4">
                <div className="mb-3 rounded-xl border border-[#d9efec] bg-[#f8fdfc] p-4 md:p-5">
                  <div className="grid gap-5 md:grid-cols-[220px_1fr] md:items-center">
                    <div
                      className={`relative mx-auto h-44 w-44 rounded-full border-8 border-slate-100 bg-white shadow-lg ${styles.glow} flex items-center justify-center`}
                    >
                      <div className="flex h-32 w-32 flex-col items-center justify-center rounded-full border border-slate-100 bg-white">
                        <div
                          className={`text-6xl font-black tracking-tight ${styles.score}`}
                          aria-hidden
                        >
                          {result.score}
                        </div>
                        <div className="text-[11px] font-bold uppercase tracking-[0.16em] text-gray-500">
                          {UI_TEXT.result.scoreSuffix}
                        </div>
                      </div>
                    </div>
                    <div>
                      <div
                        className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-base font-bold ${styles.badge}`}
                      >
                        {level === "low" ? (
                          <Shield className="h-4 w-4" aria-hidden />
                        ) : (
                          <AlertCircle className="h-4 w-4" aria-hidden />
                        )}
                        {level === "high"
                          ? UI_TEXT.result.high
                          : level === "medium"
                            ? UI_TEXT.result.medium
                            : UI_TEXT.result.low}
                      </div>
                      <p className="mt-3 text-sm font-medium text-gray-500">
                        {APP_CONFIG.name} ·{" "}
                        {new Date(result.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
                {result.qrDecodedContent && (
                  <div className="grid grid-cols-[180px_1fr] gap-3 border-b border-[#e9f4f2] px-3 py-3 bg-white md:px-4">
                    <p className="text-sm font-semibold text-slate-800">
                      QR Code Content
                    </p>
                    <p className="text-sm text-slate-700 break-words">
                      {result.qrContentType === "url"
                        ? `This QR code opens: ${result.qrDecodedContent}`
                        : `This QR code contains: ${result.qrDecodedContent}`}
                    </p>
                  </div>
                )}
                {qrReportRows.map((row) => (
                  <div
                    key={row.label}
                    className="grid grid-cols-[180px_1fr] gap-3 border-b border-[#e9f4f2] px-3 py-3 odd:bg-white even:bg-[#fbfefe] last:border-b-0 md:px-4"
                  >
                    <p className="text-sm font-semibold text-slate-800">
                      {row.label}
                    </p>
                    <p className="text-sm text-slate-700 break-words">
                      {row.value}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="relative z-10">
            <div className="p-6 md:p-9 bg-gradient-to-b from-white via-white to-slate-50/50 text-[15px] md:text-base">
              <div className="-mt-2 mb-6 md:-mt-4 md:mb-5" />

              {!isQrResult && (
                <div className="mb-8 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
                  {dualTextUrl && (
                    <div
                      className="border-b border-slate-200 bg-[#eef1f6]"
                      role="tablist"
                      aria-label="Detection summary type"
                    >
                      <div className="flex p-1.5 md:p-2">
                        <div className="flex w-full gap-0 rounded-md bg-slate-300/35 p-1 shadow-inner ring-1 ring-slate-300/40 md:max-w-2xl">
                          <button
                            type="button"
                            role="tab"
                            aria-selected={summaryTab === "text"}
                            onClick={() => setSummaryTab("text")}
                            className={`min-h-9 flex-1 rounded px-2 py-2 text-center text-xs font-medium leading-snug transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#283C5E] md:px-4 md:text-sm ${
                              summaryTab === "text"
                                ? "bg-[#283C5E] text-white shadow-sm"
                                : "bg-transparent text-slate-700 hover:bg-white/60 hover:text-slate-900"
                            }`}
                          >
                            Text detection summary
                          </button>
                          <button
                            type="button"
                            role="tab"
                            aria-selected={summaryTab === "url"}
                            onClick={() => setSummaryTab("url")}
                            className={`min-h-9 flex-1 rounded px-2 py-2 text-center text-xs font-medium leading-snug transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#283C5E] md:px-4 md:text-sm ${
                              summaryTab === "url"
                                ? "bg-[#283C5E] text-white shadow-sm"
                                : "bg-transparent text-slate-700 hover:bg-white/60 hover:text-slate-900"
                            }`}
                          >
                            URL detection summary
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                  <div className="grid gap-6 p-5 md:grid-cols-[220px_1fr] md:items-center md:p-6">
                    <div
                      className={`relative mx-auto w-44 h-44 rounded-full border-8 border-slate-100 bg-white flex items-center justify-center shadow-lg ${scoreCardStyles.glow}`}
                    >
                      <div className="w-32 h-32 rounded-full border border-slate-100 bg-white flex flex-col items-center justify-center">
                        <div
                          className={`text-6xl font-black tracking-tight ${scoreCardStyles.score}`}
                          aria-hidden
                        >
                          {scoreCardScore}
                        </div>
                        <div className="text-[11px] font-bold uppercase tracking-[0.16em] text-gray-500">
                          {UI_TEXT.result.scoreSuffix}
                        </div>
                      </div>
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-3">
                        <div
                          className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-base font-bold border ${scoreCardStyles.badge}`}
                        >
                          {scoreCardLevel === "low" ? (
                            <Shield className="w-4 h-4" aria-hidden />
                          ) : (
                            <AlertCircle className="w-4 h-4" aria-hidden />
                          )}
                          {scoreCardLevel === "high"
                            ? UI_TEXT.result.high
                            : scoreCardLevel === "medium"
                              ? UI_TEXT.result.medium
                              : UI_TEXT.result.low}
                        </div>
                        {shouldShowScamTypeBadge && (
                          <Badge
                            variant="outline"
                            className="border-primary/40 text-primary bg-primary/10 px-3 py-1 font-semibold"
                          >
                            {scamTypeLabel}
                          </Badge>
                        )}
                      </div>
                      {showExplanationUnderScore && (
                        <p className="text-gray-900 leading-relaxed text-lg md:text-xl font-medium">
                          {result.explanation}
                        </p>
                      )}
                      <p className="text-sm text-gray-500 mt-3 font-medium">
                        {APP_CONFIG.name} ·{" "}
                        {new Date(result.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {showDetectedLinkCard && (
                <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm">
                  <h3 className="font-semibold text-gray-900 mb-2 text-lg">
                    Detected Link
                  </h3>
                  <p className="text-base text-gray-700 break-all">
                    {detectedLinkPrimary}
                  </p>
                  {!dualTextUrl && result.redirectUrl && (
                    <p className="text-base text-gray-600 mt-1 break-all">
                      Redirects to: {result.redirectUrl}
                    </p>
                  )}
                  {notableUrlMeta && notableUrlMeta.length > 0 && (
                    <div className="mt-6">
                      <h4 className="mb-3 text-base font-semibold text-gray-900">
                        Notable URL signals
                      </h4>
                      <div className="overflow-hidden rounded-none border border-[#e9f4f2]">
                        {notableUrlMeta.map((item, idx) => {
                          const ms = URL_META_SEVERITY_STYLES[item.severity];
                          const bandLabel =
                            item.severity === "high"
                              ? "High"
                              : item.severity === "medium"
                                ? "Moderate"
                                : "Notice";
                          return (
                            <div
                              key={`${item.label}-${idx}`}
                              className="flex items-center gap-3 border-b border-[#e9f4f2] last:border-b-0 md:gap-4"
                            >
                              <div
                                className={`m-0 flex w-[132px] shrink-0 items-center px-2 py-2 text-sm font-semibold ${ms.labelCell}`}
                              >
                                {item.label}
                              </div>
                              <div
                                className={`min-w-0 flex-1 py-3 pr-3 text-sm leading-relaxed text-black break-words md:pr-4 ${
                                  idx % 2 === 0 ? "bg-white" : "bg-[#fbfefe]"
                                }`}
                              >
                                <span
                                  className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold md:text-sm ${ms.badge}`}
                                >
                                  {bandLabel}
                                </span>
                                <span className="text-neutral-600">{" — "}</span>
                                <span>{item.explanation}</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {!isQrResult &&
                !noFlags &&
                (!dualTextUrl || summaryTab === "text") && (
                <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm space-y-4">
                  <h3 className="font-semibold text-gray-900 text-lg">
                    Suspicious Parts
                  </h3>
                  <div className="overflow-hidden rounded-xl border border-[#e9f4f2]">
                    <div className="grid grid-cols-[180px_1fr] gap-3 border-b border-[#e9f4f2] bg-white px-3 py-3 md:px-4">
                      <p className="text-base font-semibold text-slate-800">
                        Detected Signal
                      </p>
                      <p className="text-base font-semibold text-slate-800">
                        Why It Is Risky
                      </p>
                    </div>
                    {visibleFlags.map((item, idx) => (
                      <div
                        key={`${item.text}-${idx}`}
                        className="grid grid-cols-[180px_1fr] gap-3 border-b border-[#e9f4f2] px-3 py-3 odd:bg-white even:bg-[#fbfefe] last:border-b-0 md:px-4"
                      >
                        <p className="text-base text-slate-700 break-words">
                          {item.text}
                        </p>
                        <p className="text-base text-slate-700 break-words">
                          {item.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                  {extraCount > 0 && (
                    <button
                      className="text-primary text-sm font-medium hover:underline"
                      onClick={() => setShowAllFlags((v) => !v)}
                    >
                      {showAllFlags ? "Show less" : `Show ${extraCount} more`}
                    </button>
                  )}
                </div>
                )}

              {!isQrResult && (
                <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-semibold text-gray-900 text-lg">
                      {immediateTitle}
                    </h3>
                  </div>
                  <div
                    className={`mt-4 grid gap-4 ${
                      urlActionGuideTwoColumn ? "md:grid-cols-2" : ""
                    }`}
                  >
                    {showUrlAwareDontDoPanel && (
                      <div className="rounded-xl bg-red-50 p-4 border border-red-100 transition-transform duration-200 ease-out hover:scale-[1.02] hover:shadow-md">
                        <p className="text-lg font-semibold text-red-700">
                          Don&apos;t Do
                        </p>
                        <ul className="mt-2 space-y-2 text-base text-red-900">
                          {dontDoItems.map((line) => (
                            <li key={line} className="flex gap-2 leading-relaxed">
                              <span aria-hidden className="mt-0.5 text-red-600">
                                •
                              </span>
                              <span>{line}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <div className="rounded-xl bg-emerald-50 p-4 border border-emerald-100 transition-transform duration-200 ease-out hover:scale-[1.02] hover:shadow-md">
                      <p className="text-lg font-semibold text-emerald-700">
                        What you should do now:
                      </p>
                      <ul className="mt-2 space-y-2 text-base text-emerald-900">
                        {saferActionItems.map((line) => (
                          <li key={line} className="flex gap-2 leading-relaxed">
                            <span aria-hidden className="mt-0.5 text-emerald-600">
                              •
                            </span>
                            <span>{line}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {level !== "low" && result.scamType !== "unknown" && (
                <Button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/guidance/${encodeURIComponent(result.scamType || "phishing")}`,
                    )
                  }
                  className="w-full h-12 bg-primary hover:bg-secondary text-primary-foreground border-0 font-semibold shadow-md mb-4"
                >
                  I May Have Been Scammed
                </Button>
              )}

              {shouldShowRelatedCases && (
                <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
                  <h3 className="font-semibold text-gray-900 mb-3 text-lg">
                    Related Cases
                  </h3>
                  {isRelatedLoading ? (
                    <p className="text-base text-gray-600">
                      Loading related case...
                    </p>
                  ) : relatedCase ? (
                    <button
                      className="group w-full text-left p-0 transition"
                      onClick={() => {
                        if (relatedCase.sourceUrl?.trim()) {
                          window.open(relatedCase.sourceUrl, "_blank", "noopener,noreferrer");
                          return;
                        }
                        navigate(`/cases/${relatedCase.id}`);
                      }}
                    >
                      <p className="line-clamp-1 font-semibold text-gray-900 transition-colors group-hover:text-primary group-hover:underline">
                        {relatedCase.title}
                      </p>
                      <p className="text-base text-gray-600 mt-1">
                        {relatedCase.summary}
                      </p>
                    </button>
                  ) : (
                    <p className="text-base text-gray-600">
                      No related cases found for this type of scam yet.
                    </p>
                  )}
                  <button
                    className="mt-3 text-primary font-medium text-sm hover:underline"
                    onClick={() => {
                      if (caseFilterScamType === "all") {
                        navigate("/cases");
                        return;
                      }
                      navigate(
                        `/cases?scamType=${encodeURIComponent(caseFilterScamType)}`,
                      );
                    }}
                  >
                    View More Cases →
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    );
  },
  (prev, next) =>
    prev.result.score === next.result.score &&
    prev.result.riskLevel === next.result.riskLevel &&
    prev.result.timestamp === next.result.timestamp &&
    prev.result.submittedUrl === next.result.submittedUrl &&
    prev.result.dualTextUrlDetection === next.result.dualTextUrlDetection &&
    urlDetectionSummaryEqual(
      prev.result.urlDetectionSummary,
      next.result.urlDetectionSummary,
    ) &&
    urlMetaFeaturesEqual(
      prev.result.urlMetaFeatures,
      next.result.urlMetaFeatures,
    ),
);
