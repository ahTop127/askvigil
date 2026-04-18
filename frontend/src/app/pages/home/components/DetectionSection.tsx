import { useCallback } from "react";
import { UI_TEXT } from "@lib/constants/text";
import type { UseScamDetectionReturn } from "../hooks/useScamDetection";
import { DetectionForm } from "./DetectionForm";
import { ResultDisplay } from "./ResultDisplay";

export interface DetectionSectionProps {
  detection: UseScamDetectionReturn;
}

/**
 * Hub header and detection form/result states.
 */
export function DetectionSection({ detection }: DetectionSectionProps) {
  const {
    activeTab,
    setActiveTab,
    textInput,
    setTextInput,
    urlInput,
    setUrlInput,
    imageFile,
    qrFile,
    setImageFile,
    setQrFile,
    error,
    isChecking,
    showResult,
    result,
    handleCheck,
    resetDetection,
    clearError,
  } = detection;

  const onTabChange = useCallback(
    (tab: string) => {
      clearError();
      setActiveTab(tab);
    },
    [clearError, setActiveTab],
  );

  return (
    <section
      id="check-section"
      className="py-20 bg-[#F7F8FA] relative overflow-hidden"
    >
      <div className="max-w-4xl mx-auto px-4 relative z-10">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-[#EAA866] mb-4">
            {UI_TEXT.detection.hubTitle}
          </h2>
          <p className="text-lg text-gray-600">
            {UI_TEXT.detection.hubSubtitle}
          </p>
        </div>

        {!showResult ? (
          <DetectionForm
            activeTab={activeTab}
            onTabChange={onTabChange}
            textInput={textInput}
            onTextChange={(v) => {
              setTextInput(v);
              clearError();
            }}
            urlInput={urlInput}
            onUrlChange={(v) => {
              setUrlInput(v);
              clearError();
            }}
            imageFile={imageFile}
            qrFile={qrFile}
            onImageFile={(f) => {
              setImageFile(f);
              clearError();
            }}
            onQrFile={(f) => {
              setQrFile(f);
              clearError();
            }}
            error={error}
            isChecking={isChecking}
            onRequestCheck={handleCheck}
          />
        ) : (
          result && (
            <ResultDisplay result={result} onNewAnalysis={resetDetection} />
          )
        )}
      </div>

    </section>
  );
}
