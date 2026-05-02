import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { AlertCircle } from "lucide-react";
import { Button } from "../components/ui/button";
import { Navigation } from "../components/Navigation";
import { ResultDisplay } from "./home/components/ResultDisplay";
import type { RiskLevel, ScamDetectionResult } from "@lib/types";

interface LegacyScanResult {
  input?: string;
  type?: string;
  riskLevel: RiskLevel;
  explanation: string;
  scamType?: string;
}

function toScoreFromLevel(level: RiskLevel): number {
  if (level === "high") return 80;
  if (level === "medium") return 55;
  return 20;
}

function normalizeStoredResult(raw: unknown): ScamDetectionResult | null {
  if (!raw || typeof raw !== "object") return null;
  const obj = raw as Record<string, unknown>;

  if (
    typeof obj.score === "number" &&
    typeof obj.riskLevel === "string" &&
    typeof obj.explanation === "string" &&
    typeof obj.timestamp === "string"
  ) {
    return obj as unknown as ScamDetectionResult;
  }

  if (
    typeof obj.riskLevel === "string" &&
    typeof obj.explanation === "string"
  ) {
    const legacy = obj as LegacyScanResult;
    return {
      score: toScoreFromLevel(legacy.riskLevel),
      riskLevel: legacy.riskLevel,
      explanation: legacy.explanation,
      scamType: legacy.scamType ?? "unknown",
      timestamp: new Date().toISOString(),
      detectionType:
        legacy.type === "text" ||
        legacy.type === "image" ||
        legacy.type === "url" ||
        legacy.type === "qr"
          ? legacy.type
          : undefined,
      submittedUrl:
        legacy.type === "url" && typeof legacy.input === "string"
          ? legacy.input
          : undefined,
    };
  }

  return null;
}

export default function DetectionResultPage() {
  const navigate = useNavigate();
  const [result, setResult] = useState<ScamDetectionResult | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const storedResult = localStorage.getItem("lastScanResult");
    if (storedResult) {
      try {
        const parsed = JSON.parse(storedResult) as unknown;
        const normalized = normalizeStoredResult(parsed);
        if (!normalized) {
          setError(true);
          return;
        }
        setResult(normalized);
      } catch {
        setError(true);
      }
    } else {
      setError(true);
    }
  }, []);

  if (error || !result) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />

        <main className="mx-auto w-full max-w-[1280px] px-4 py-12">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-12 text-center">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Something Went Wrong
            </h2>
            <p className="text-gray-600 mb-6">
              We could not generate a risk score. Please try again.
            </p>
            <Button onClick={() => navigate("/")}>Return to Home</Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="mx-auto w-full max-w-[1280px] px-4 py-12">
        <ResultDisplay result={result} onNewAnalysis={() => navigate("/")} />
      </main>
    </div>
  );
}
