import { memo } from "react";
import { useNavigate } from "react-router";
import { AlertCircle, Shield } from "lucide-react";
import { Button } from "@components/ui/button";
import { APP_CONFIG } from "@lib/config/app";
import { UI_TEXT } from "@lib/constants/text";
import type { RiskLevel, ScamDetectionResult } from "@lib/types";

const RISK_STYLES: Record<
  RiskLevel,
  { card: string; ring: string; score: string; badge: string }
> = {
  high: {
    card: "bg-red-50 border-red-300",
    ring: "bg-red-500",
    score: "text-red-600",
    badge: "bg-red-500 text-white",
  },
  medium: {
    card: "bg-amber-50 border-amber-300",
    ring: "bg-amber-500",
    score: "text-amber-600",
    badge: "bg-amber-500 text-white",
  },
  low: {
    card: "bg-green-50 border-green-300",
    ring: "bg-green-500",
    score: "text-green-600",
    badge: "bg-green-500 text-white",
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
    const level = isRiskLevel(result.riskLevel) ? result.riskLevel : "low";
    const styles = RISK_STYLES[level];

    return (
      <div className="space-y-6">
        <div
          className={`relative rounded-3xl p-8 md:p-10 border-2 shadow-lg overflow-hidden ${styles.card}`}
          role="region"
          aria-label={`Detection result: ${level} risk, score ${result.score}`}
        >
          <div className="relative z-10">
            <div className="flex justify-center mb-8">
              <div
                className={`relative w-48 h-48 rounded-full flex items-center justify-center ${styles.ring} shadow-xl border-4 border-white motion-safe:animate-[pulse_2.5s_ease-in-out_infinite]`}
              >
                <div className="w-36 h-36 rounded-full bg-white flex flex-col items-center justify-center">
                  <div
                    className={`text-6xl font-bold ${styles.score}`}
                    aria-hidden
                  >
                    {result.score}
                  </div>
                  <div className="text-sm font-semibold text-gray-600">
                    {UI_TEXT.result.scoreSuffix}
                  </div>
                </div>
              </div>
            </div>

            <div className="text-center mb-6">
              <div
                className={`inline-flex items-center gap-2 px-6 py-3 rounded-full font-bold text-lg mb-3 ${styles.badge} shadow-md`}
              >
                {level === "high" ? (
                  <>
                    <AlertCircle className="w-6 h-6" aria-hidden />
                    {UI_TEXT.result.high}
                  </>
                ) : level === "medium" ? (
                  <>
                    <AlertCircle className="w-6 h-6" aria-hidden />
                    {UI_TEXT.result.medium}
                  </>
                ) : (
                  <>
                    <Shield className="w-6 h-6" aria-hidden />
                    {UI_TEXT.result.low}
                  </>
                )}
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 mb-6 border border-gray-200 shadow-sm">
              <p className="text-gray-800 text-center leading-relaxed font-medium">
                {result.explanation}
              </p>
              <p className="text-center text-xs text-gray-500 mt-2">
                {APP_CONFIG.name} ·{" "}
                {new Date(result.timestamp).toLocaleString()}
              </p>
            </div>

            {level !== "low" && (
              <Button
                type="button"
                onClick={() => navigate("/guidance")}
                className="w-full h-12 bg-[#EAA866] hover:bg-[#D89654] text-white border-0 font-semibold shadow-md mb-4"
              >
                {UI_TEXT.result.guidanceCta}
              </Button>
            )}
          </div>
        </div>

        <Button
          type="button"
          onClick={onNewAnalysis}
          className="w-full h-14 text-base font-semibold bg-white hover:bg-gray-50 text-[#EAA866] border-2 border-[#EAA866] shadow-md transition-all"
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
