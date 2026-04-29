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
  if (normalized === "qr_code_scam" || normalized === "qr-scam") return "qr-scam";
  if (normalized === "otp_scam" || normalized === "otp-scam") return "otp-scam";
  if (normalized === "suspicious_link" || normalized === "suspicious-link") {
    return "suspicious-link";
  }
  return "all";
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
    const visibleFlags = showAllFlags ? suspiciousItems : suspiciousItems.slice(0, 5);
    const extraCount = Math.max(0, suspiciousItems.length - 5);
    const noFlags = suspiciousItems.length === 0;
    const scamTypeLabel = result.scamType?.trim() || "Suspicious Content";
    const guidance = result.guidance ?? [
      "Do not click unknown links or open unexpected files.",
      "Verify requests through official channels before responding.",
    ];
    const immediateTitle = result.immediateGuidanceTitle?.trim() || "Action Guide";
    const immediateSummary = result.immediateGuidanceSummary?.trim();
    const isUnknownScamType = (result.scamType ?? "").trim().toLowerCase() === "unknown";
    const shouldShowRelatedCases = !result.submittedUrl && !result.qrDecodedContent;
    const dontDoItems =
      result.immediateGuidanceDontDo && result.immediateGuidanceDontDo.length > 0
        ? result.immediateGuidanceDontDo
        : guidance.slice(0, 2);
    const saferActionItems =
      result.immediateGuidanceSaferAction && result.immediateGuidanceSaferAction.length > 0
        ? result.immediateGuidanceSaferAction
        : guidance.slice(2, 5);
    const caseFilterScamType = useMemo(
      () => getCaseFilterScamType(result.scamType || ""),
      [result.scamType],
    );

    useEffect(() => {
      let cancelled = false;
      if (caseFilterScamType === "all") {
        setRelatedCase(null);
        setIsRelatedLoading(false);
        return;
      }
      setIsRelatedLoading(true);
      fetchScamCases({ scamType: caseFilterScamType, platform: "all", date: "all" })
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
          <div className={`h-1.5 w-full ${styles.accent}`} />
          <div className="relative z-10">
            <div className="p-6 md:p-9 bg-gradient-to-b from-white via-white to-slate-50/50 text-[15px] md:text-base">
            <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center">
              <div className="rounded-2xl p-4 border border-slate-200 bg-white/90 shadow-sm md:flex-1">
                <div className="flex flex-wrap gap-3">
                  {steps.map((step) => (
                    <div
                      key={step.key}
                      className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold tracking-wide ${
                        step.status === "current"
                          ? "text-primary bg-primary/10"
                          : step.status === "pending"
                            ? "text-gray-400 bg-gray-100"
                            : step.status === "failed"
                              ? "text-red-600 bg-red-50"
                              : "text-gray-700 bg-slate-100"
                      }`}
                    >
                      {step.status === "completed" && <Check className="w-4 h-4" />}
                      {step.status === "current" && (
                        <LoaderCircle className="w-4 h-4 animate-spin" />
                      )}
                      {step.status === "failed" && <TriangleAlert className="w-4 h-4" />}
                      <span>{step.label}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex justify-end">
                <Button
                  type="button"
                  onClick={onNewAnalysis}
                  className="h-10 rounded-full bg-primary px-5 text-base text-primary-foreground font-semibold hover:bg-secondary shadow-sm"
                >
                  Check Again
                </Button>
              </div>
            </div>

            <div className="grid gap-6 rounded-3xl border border-slate-200 bg-white p-5 md:grid-cols-[220px_1fr] md:items-center md:p-6 mb-8 shadow-sm">
              <div
                className={`relative mx-auto w-44 h-44 rounded-full border-8 border-slate-100 bg-white flex items-center justify-center shadow-lg ${styles.glow}`}
              >
                <div className="w-32 h-32 rounded-full border border-slate-100 bg-white flex flex-col items-center justify-center">
                  <div className={`text-6xl font-black tracking-tight ${styles.score}`} aria-hidden>
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
                  <Badge
                    variant="outline"
                    className="border-primary/40 text-primary bg-primary/10 px-3 py-1 font-semibold"
                  >
                    {scamTypeLabel}
                  </Badge>
                </div>
                <p className="text-gray-900 leading-relaxed text-lg md:text-xl font-medium">
                  {result.explanation}
                </p>
                <p className="text-sm text-gray-500 mt-3 font-medium">
                  {APP_CONFIG.name} · {new Date(result.timestamp).toLocaleString()}
                </p>
              </div>
            </div>

            {result.submittedUrl && (
              <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm">
                <h3 className="font-semibold text-gray-900 mb-2 text-lg">Detected Link</h3>
                <p className="text-base text-gray-700 break-all">{result.submittedUrl}</p>
                {result.redirectUrl && (
                  <p className="text-base text-gray-600 mt-1 break-all">
                    Redirects to: {result.redirectUrl}
                  </p>
                )}
              </div>
            )}

            {result.qrDecodedContent && (
              <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm">
                <h3 className="font-semibold text-gray-900 mb-2 text-lg">QR Code Content</h3>
                <p className="text-base text-gray-700 break-all">
                  {result.qrContentType === "url"
                    ? `This QR code opens: ${result.qrDecodedContent}`
                    : `This QR code contains: ${result.qrDecodedContent}`}
                </p>
              </div>
            )}

            {!noFlags ? (
              <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm space-y-4">
                <h3 className="font-semibold text-gray-900 text-lg">Suspicious Parts</h3>
                {visibleFlags.map((item, idx) => (
                  <div
                    key={`${item.text}-${idx}`}
                    className="rounded-xl bg-slate-50/80 p-4"
                  >
                    <div className="grid gap-2 md:grid-cols-[180px_1fr] md:items-start">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                          Detected Signal
                        </p>
                        <p className="mt-1 inline-flex rounded-md bg-amber-100 px-2.5 py-1 text-sm font-semibold text-gray-900">
                          {item.text}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                          Why It Is Risky
                        </p>
                        <p className="mt-1 text-base leading-relaxed text-gray-700">
                          {item.reason}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
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
            )}

            <div className="bg-white rounded-2xl p-6 mb-6 border border-slate-200 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-semibold text-gray-900 text-lg">{immediateTitle}</h3>
                <Badge variant="outline" className="text-xs border-primary/30 text-primary font-semibold">
                  Action Guide
                </Badge>
              </div>
              <div
                className={`mt-4 grid gap-4 ${
                  isUnknownScamType ? "" : "md:grid-cols-2"
                }`}
              >
                {!isUnknownScamType && (
                  <div className="rounded-xl bg-red-50 p-4 border border-red-100">
                    <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
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
                <div className="rounded-xl bg-emerald-50 p-4 border border-emerald-100">
                  <p className="text-xs font-semibold tracking-wide text-emerald-700">
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

            {level !== "low" && result.scamType !== "unknown" && (
              <Button
                type="button"
                onClick={() =>
                  navigate(`/guidance/${encodeURIComponent(result.scamType || "phishing")}`)
                }
                className="w-full h-12 bg-primary hover:bg-secondary text-primary-foreground border-0 font-semibold shadow-md mb-4"
              >
                I May Have Been Scammed
              </Button>
            )}

            {shouldShowRelatedCases && (
              <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
                <h3 className="font-semibold text-gray-900 mb-3 text-lg">Related Cases</h3>
                {isRelatedLoading ? (
                  <p className="text-base text-gray-600">Loading related case...</p>
                ) : relatedCase ? (
                  <button
                    className="w-full text-left border rounded-xl p-4 hover:shadow-md transition"
                    onClick={() => navigate(`/cases/${relatedCase.id}`)}
                  >
                    <p className="font-semibold text-gray-900 line-clamp-1">
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
                  onClick={() =>
                    navigate(`/cases?scamType=${encodeURIComponent(caseFilterScamType)}`)
                  }
                >
                  View More Cases →
                </button>
              </div>
            )}
            </div>
          </div>
        </div>

        <Button
          type="button"
          onClick={onNewAnalysis}
          className="w-full h-14 text-base font-semibold bg-background hover:bg-muted/40 text-primary border-2 border-primary/50 shadow-md transition-all"
        >
          {UI_TEXT.result.newAnalysis}
        </Button>
      </div>
    );
  },
  (prev, next) =>
    prev.result.score === next.result.score &&
    prev.result.riskLevel === next.result.riskLevel &&
    prev.result.timestamp === next.result.timestamp,
);
