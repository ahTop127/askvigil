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
import type { RiskLevel, ScamCase, ScamDetectionResult } from "@lib/types";

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
    const shouldShowScamTypeBadge =
      !result.submittedUrl && !result.qrDecodedContent;
    const guidance = result.guidance ?? [
      "Do not click unknown links or open unexpected files.",
      "Verify requests through official channels before responding.",
    ];
    const immediateTitle =
      result.immediateGuidanceTitle?.trim() || "Action Guide";
    const immediateSummary = result.immediateGuidanceSummary?.trim();
    const isUnknownScamType =
      (result.scamType ?? "").trim().toLowerCase() === "unknown";
    const shouldShowRelatedCases =
      !result.submittedUrl && !result.qrDecodedContent;
    const isQrResult = Boolean(result.qrDecodedContent || result.qrContentType);
    const isUrlOrQrResult = Boolean(result.submittedUrl || isQrResult);
    const isTextResult = result.detectionType === "text";
    const dontDoItems =
      result.immediateGuidanceDontDo &&
      result.immediateGuidanceDontDo.length > 0
        ? result.immediateGuidanceDontDo
        : guidance.slice(0, 2);
    const saferActionItems =
      result.immediateGuidanceSaferAction &&
      result.immediateGuidanceSaferAction.length > 0
        ? result.immediateGuidanceSaferAction
        : guidance.slice(2, 5);
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
          aria-label={`Detection result: ${level} risk, score ${result.score}`}
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
                <div className="grid gap-6 rounded-3xl border border-slate-200 bg-white p-5 md:grid-cols-[220px_1fr] md:items-center md:p-6 mb-8 shadow-sm">
                <div
                  className={`relative mx-auto w-44 h-44 rounded-full border-8 border-slate-100 bg-white flex items-center justify-center shadow-lg ${styles.glow}`}
                >
                  <div className="w-32 h-32 rounded-full border border-slate-100 bg-white flex flex-col items-center justify-center">
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
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <div
                      className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-base font-bold border ${styles.badge}`}
                    >
                      {level === "low" ? (
                        <Shield className="w-4 h-4" aria-hidden />
                      ) : (
                        <AlertCircle className="w-4 h-4" aria-hidden />
                      )}
                      {level === "high"
                        ? UI_TEXT.result.high
                        : level === "medium"
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
                  {!isUrlOrQrResult && (
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
              )}

              {result.submittedUrl && (
                <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm">
                  <h3 className="font-semibold text-gray-900 mb-2 text-lg">
                    Detected Link
                  </h3>
                  <p className="text-base text-gray-700 break-all">
                    {result.submittedUrl}
                  </p>
                  {result.redirectUrl && (
                    <p className="text-base text-gray-600 mt-1 break-all">
                      Redirects to: {result.redirectUrl}
                    </p>
                  )}
                </div>
              )}

              {!isQrResult &&
                (!noFlags ? (
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
                ) : (
                  <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm space-y-3">
                    <h3 className="font-semibold text-gray-900 text-lg">
                      No obvious scam patterns found
                    </h3>
                  </div>
                ))}

              {!isQrResult && (
                <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-semibold text-gray-900 text-lg">
                      {immediateTitle}
                    </h3>
                  </div>
                  <div
                    className={`mt-4 grid gap-4 ${
                      isUnknownScamType ? "" : "md:grid-cols-2"
                    }`}
                  >
                    {!isUnknownScamType && (
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
    prev.result.timestamp === next.result.timestamp,
);
