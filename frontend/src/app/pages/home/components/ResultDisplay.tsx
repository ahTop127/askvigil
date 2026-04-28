import { memo, useMemo, useState } from "react";
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
import { APP_CONFIG } from "@lib/config/app";
import { UI_TEXT } from "@lib/constants/text";
import type { RiskLevel, ScamDetectionResult } from "@lib/types";

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

/**
 * Presents score, risk band, explanation, and optional guidance CTA.
 */
export const ResultDisplay = memo(
  function ResultDisplay({ result, onNewAnalysis }: ResultDisplayProps) {
    const navigate = useNavigate();
    const [showAllFlags, setShowAllFlags] = useState(false);
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

    return (
      <div className="space-y-6">
        <div
          className="relative overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm"
          role="region"
          aria-label={`Detection result: ${level} risk, score ${result.score}`}
        >
          <div className={`h-1.5 w-full ${styles.accent}`} />
          <div className="relative z-10">
            <div className="p-6 md:p-8">
            <div className="rounded-2xl p-4 border border-gray-200 mb-6">
              <div className="flex flex-wrap gap-3">
                {steps.map((step) => (
                  <div
                    key={step.key}
                    className={`inline-flex items-center gap-2 text-sm ${
                      step.status === "current"
                        ? "text-primary"
                        : step.status === "pending"
                          ? "text-gray-400"
                          : step.status === "failed"
                            ? "text-red-600"
                            : "text-gray-600"
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

            <div className="grid gap-4 md:grid-cols-[220px_1fr] items-center mb-6">
              <div
                className={`relative mx-auto w-44 h-44 rounded-full border-8 border-gray-100 bg-white flex items-center justify-center shadow-lg ${styles.glow}`}
              >
                <div className="w-32 h-32 rounded-full border border-gray-100 bg-white flex flex-col items-center justify-center">
                  <div className={`text-5xl font-bold ${styles.score}`} aria-hidden>
                    {result.score}
                  </div>
                  <div className="text-xs font-semibold text-gray-500">
                    {UI_TEXT.result.scoreSuffix}
                  </div>
                </div>
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  <div
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold border ${styles.badge}`}
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
                    className="border-primary/40 text-primary bg-primary/10"
                  >
                    {scamTypeLabel}
                  </Badge>
                </div>
                <p className="text-gray-800 leading-relaxed font-medium">
                  {result.explanation}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  {APP_CONFIG.name} · {new Date(result.timestamp).toLocaleString()}
                </p>
              </div>
            </div>

            {result.submittedUrl && (
              <div className="bg-white rounded-2xl p-6 mb-6 border border-gray-200 shadow-sm">
                <h3 className="font-semibold text-gray-900 mb-2">Detected Link</h3>
                <p className="text-sm text-gray-700 break-all">{result.submittedUrl}</p>
                {result.redirectUrl && (
                  <p className="text-sm text-gray-600 mt-1 break-all">
                    Redirects to: {result.redirectUrl}
                  </p>
                )}
              </div>
            )}

            {result.qrDecodedContent && (
              <div className="bg-white rounded-2xl p-6 mb-6 border border-gray-200 shadow-sm">
                <h3 className="font-semibold text-gray-900 mb-2">QR Code Content</h3>
                <p className="text-sm text-gray-700 break-all">
                  {result.qrContentType === "url"
                    ? `This QR code opens: ${result.qrDecodedContent}`
                    : `This QR code contains: ${result.qrDecodedContent}`}
                </p>
              </div>
            )}

            {!noFlags ? (
              <div className="bg-white rounded-2xl p-6 mb-6 border border-gray-200 shadow-sm space-y-3">
                <h3 className="font-semibold text-gray-900">Suspicious Parts</h3>
                {visibleFlags.map((item, idx) => (
                  <div key={`${item.text}-${idx}`} className="text-sm">
                    <p className="inline bg-yellow-200 px-1 rounded text-gray-900">
                      {item.text}
                    </p>
                    <p className="mt-1 text-gray-600">
                      ❌ "{item.text}" → {item.reason}
                    </p>
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
              <div className="bg-white rounded-2xl p-6 mb-6 border border-gray-200 shadow-sm space-y-3">
                <h3 className="font-semibold text-gray-900">
                  ✅ No obvious scam patterns found
                </h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>✅ Urgency language — None found</li>
                  <li>✅ Suspicious links — None found</li>
                  <li>✅ Requests for personal info — None found</li>
                </ul>
              </div>
            )}

            <div className="bg-white rounded-2xl p-6 mb-6 border border-gray-200 shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-2">What You Should Do</h3>
              <ul className="space-y-1 text-sm text-gray-700">
                {guidance.slice(0, 3).map((line) => (
                  <li key={line}>• {line}</li>
                ))}
              </ul>
            </div>

            {level !== "low" && (
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

            <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm">
              <h3 className="font-semibold text-gray-900 mb-3">Related Cases</h3>
              {result.relatedCase ? (
                <button
                  className="w-full text-left border rounded-xl p-4 hover:shadow-md transition"
                  onClick={() => navigate(`/cases/${result.relatedCase?.id}`)}
                >
                  <p className="font-semibold text-gray-900 line-clamp-1">
                    {result.relatedCase.title}
                  </p>
                  <p className="text-sm text-gray-600 line-clamp-2 mt-1">
                    {result.relatedCase.summary}
                  </p>
                </button>
              ) : (
                <p className="text-sm text-gray-600">
                  No related cases found for this type of scam yet.
                </p>
              )}
              <button
                className="mt-3 text-primary font-medium text-sm hover:underline"
                onClick={() =>
                  navigate(`/cases?scamType=${encodeURIComponent(result.scamType || "all")}`)
                }
              >
                View More Cases →
              </button>
            </div>
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
