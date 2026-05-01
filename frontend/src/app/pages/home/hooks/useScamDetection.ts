import { useCallback, useState } from "react";
import { detectScam } from "@lib/api/scamDetection";
import { ERROR_MESSAGES } from "@lib/constants/text";
import type { DetectionType, ScamDetectionResult } from "@lib/types";
import { validateDetectionInput } from "@lib/utils/validation";
import { logger } from "@lib/utils/logger";

function isDetectionTab(v: string): v is DetectionType {
  return v === "text" || v === "image" || v === "url" || v === "qr";
}

const STEP_DEMO_TRIGGER = "__STEP_DEMO__";

function isStepDemoPayload(
  type: DetectionType,
  content: string | File,
): boolean {
  return (
    type === "text" &&
    typeof content === "string" &&
    content.includes(STEP_DEMO_TRIGGER)
  );
}

function buildStepDemoResult(payload: {
  type: DetectionType;
  content: string | File;
}): ScamDetectionResult {
  const baseResult: ScamDetectionResult = {
    score: 78,
    riskLevel: "high",
    explanation:
      "This is a demo result for step transition testing. Several urgency and credential-request signals were detected.",
    scamType: "phishing",
    timestamp: new Date().toISOString(),
    suspiciousItems: [
      { text: "urgent", reason: "Creates pressure to act immediately." },
      { text: "verify now", reason: "Impersonates account verification flow." },
    ],
    guidance: [
      "Do not click unknown links or open unexpected files.",
      "Verify requests through official channels before responding.",
      "Report suspicious content and block the sender immediately.",
    ],
  };

  if (payload.type === "url" && typeof payload.content === "string") {
    return {
      ...baseResult,
      submittedUrl: payload.content,
    };
  }

  if (payload.type === "qr") {
    return {
      ...baseResult,
      qrDecodedContent: "https://secure-payment-check.example",
      qrContentType: "url",
    };
  }

  return baseResult;
}

export interface UseScamDetectionReturn {
  activeTab: DetectionType;
  textInput: string;
  urlInput: string;
  imageFile: File | null;
  qrFile: File | null;
  error: string;
  isChecking: boolean;
  showResult: boolean;
  result: ScamDetectionResult | null;
  setActiveTab: (tab: string) => void;
  setTextInput: (value: string) => void;
  setUrlInput: (value: string) => void;
  setImageFile: (file: File | null) => void;
  setQrFile: (file: File | null) => void;
  handleCheck: () => Promise<void>;
  resetDetection: () => void;
  clearError: () => void;
}

export function useScamDetection(): UseScamDetectionReturn {
  const [activeTab, setActiveTabState] = useState<DetectionType>("text");
  const [textInput, setTextInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [qrFile, setQrFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [isChecking, setIsChecking] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [result, setResult] = useState<ScamDetectionResult | null>(null);

  const setActiveTab = useCallback((tab: string) => {
    if (isDetectionTab(tab)) setActiveTabState(tab);
  }, []);

  const getPayload = useCallback((): {
    type: DetectionType;
    content: string | File;
  } | null => {
    switch (activeTab) {
      case "text":
        return { type: "text", content: textInput };
      case "url":
        return { type: "url", content: urlInput };
      case "image":
        return imageFile ? { type: "image", content: imageFile } : null;
      case "qr":
        return qrFile ? { type: "qr", content: qrFile } : null;
      default:
        return null;
    }
  }, [activeTab, textInput, urlInput, imageFile, qrFile]);

  const runDetection = useCallback(async () => {
    setError("");
    const payload = getPayload();
    if (!payload) {
      if (activeTab === "image") setError(ERROR_MESSAGES.imageUpload);
      else if (activeTab === "qr") setError(ERROR_MESSAGES.qrUpload);
      else if (activeTab === "url") setError(ERROR_MESSAGES.urlInput);
      else setError(ERROR_MESSAGES.textInput);
      return;
    }
    const v = validateDetectionInput(payload.type, payload.content);
    if (!v.isValid) {
      setError(v.error ?? ERROR_MESSAGES.textInput);
      return;
    }
    setIsChecking(true);
    setShowResult(false);
    try {
      let res: ScamDetectionResult;
      const shouldUseLocalDemo =
        payload.type === "qr" ||
        isStepDemoPayload(payload.type, payload.content);

      if (shouldUseLocalDemo) {
        await new Promise((resolve) => {
          window.setTimeout(resolve, 5200);
        });
        res = buildStepDemoResult(payload);
      } else {
        res = await detectScam({
          type: payload.type,
          content: payload.content,
        });
      }

      if (payload.type === "image") {
        const extracted = (res.extractedText ?? "").trim();
        if (extracted.length < 5) {
          setError(ERROR_MESSAGES.insufficientContent);
          setShowResult(false);
          return;
        }
      }

      if (
        (payload.type === "text" || payload.type === "image") &&
        res.overallRiskScore === -1
      ) {
        setError(ERROR_MESSAGES.insufficientContent);
        setShowResult(false);
        return;
      }

      setResult(res);
      setShowResult(true);
    } catch (e) {
      logger.error("Detection failed", e instanceof Error ? e : undefined);
      const msg = e instanceof Error ? e.message.toLowerCase() : "";
      if (activeTab === "url") {
        if (msg.includes("failed (422)") || msg.includes("reachable")) {
          setError(ERROR_MESSAGES.unreachableUrl);
        } else {
          setError(ERROR_MESSAGES.urlAnalyzeFailed);
        }
      } else if (activeTab === "qr") {
        setError(ERROR_MESSAGES.qrDecodeFailed);
      } else {
        setError(ERROR_MESSAGES.analysisFailed);
      }
    } finally {
      setIsChecking(false);
    }
  }, [activeTab, getPayload]);

  const handleCheck = useCallback(async () => {
    await runDetection();
  }, [runDetection]);

  const resetDetection = useCallback(() => {
    setShowResult(false);
    setResult(null);
    setTextInput("");
    setUrlInput("");
    setImageFile(null);
    setQrFile(null);
    setError("");
    setActiveTabState("text");
  }, []);

  const clearError = useCallback(() => setError(""), []);

  return {
    activeTab,
    textInput,
    urlInput,
    imageFile,
    qrFile,
    error,
    isChecking,
    showResult,
    result,
    setActiveTab,
    setTextInput,
    setUrlInput,
    setImageFile,
    setQrFile,
    handleCheck,
    resetDetection,
    clearError,
  };
}
