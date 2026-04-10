import { useCallback, useState } from "react";
import { detectScam } from "@lib/api/scamDetection";
import { ERROR_MESSAGES } from "@lib/constants/text";
import type { DetectionType, ScamDetectionResult } from "@lib/types";
import { validateDetectionInput } from "@lib/utils/validation";
import { logger } from "@lib/utils/logger";

function isDetectionTab(v: string): v is DetectionType {
  return v === "text" || v === "image" || v === "url" || v === "qr";
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
  showPrivacyDialog: boolean;
  result: ScamDetectionResult | null;
  setActiveTab: (tab: string) => void;
  setTextInput: (value: string) => void;
  setUrlInput: (value: string) => void;
  setImageFile: (file: File | null) => void;
  setQrFile: (file: File | null) => void;
  handleCheck: () => void;
  confirmCheck: () => Promise<void>;
  cancelPrivacy: () => void;
  resetDetection: () => void;
  setShowPrivacyDialog: (open: boolean) => void;
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
  const [showPrivacyDialog, setShowPrivacyDialog] = useState(false);
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

  const handleCheck = useCallback(() => {
    setError("");
    const payload = getPayload();
    if (!payload) {
      if (activeTab === "image") setError(ERROR_MESSAGES.imageUpload);
      else if (activeTab === "qr") setError(ERROR_MESSAGES.qrUpload);
      else setError(ERROR_MESSAGES.textInput);
      return;
    }
    const v = validateDetectionInput(payload.type, payload.content);
    if (!v.isValid) {
      setError(v.error ?? ERROR_MESSAGES.textInput);
      return;
    }
    setShowPrivacyDialog(true);
  }, [activeTab, getPayload]);

  const confirmCheck = useCallback(async () => {
    const payload = getPayload();
    if (!payload) return;
    setShowPrivacyDialog(false);
    setIsChecking(true);
    setShowResult(false);
    try {
      const res = await detectScam({
        type: payload.type,
        content: payload.content,
      });
      setResult(res);
      setShowResult(true);
    } catch (e) {
      logger.error("Detection failed", e instanceof Error ? e : undefined);
      setError("Something went wrong. Please try again.");
    } finally {
      setIsChecking(false);
    }
  }, [getPayload]);

  const cancelPrivacy = useCallback(() => {
    setShowPrivacyDialog(false);
  }, []);

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
    showPrivacyDialog,
    result,
    setActiveTab,
    setTextInput,
    setUrlInput,
    setImageFile,
    setQrFile,
    handleCheck,
    confirmCheck,
    cancelPrivacy,
    resetDetection,
    setShowPrivacyDialog,
    clearError,
  };
}
