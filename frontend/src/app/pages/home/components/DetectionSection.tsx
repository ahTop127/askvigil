import { useCallback } from "react";
import { UI_TEXT } from "@lib/constants/text";
import type { UseScamDetectionReturn } from "../hooks/useScamDetection";
import { DetectionForm } from "./DetectionForm";

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
    handleCheck,
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
      className="relative overflow-hidden bg-gradient-to-b from-[#f7fbff] via-[#f4f8ff] to-[#eef4ff] pt-12 pb-20 md:pt-14"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 -left-20 h-72 w-72 rounded-full bg-[#93c5fd]/20 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute top-24 -right-24 h-80 w-80 rounded-full bg-[#a7f3d0]/20 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-white/70 to-transparent"
      />
      <div className="max-w-4xl mx-auto px-4 relative z-10">
        <div className="text-center mb-12 -mt-4">
          <h2 className="text-5xl md:text-6xl font-bold text-primary mb-4">
            {UI_TEXT.detection.hubTitle}
          </h2>
          <p className="text-xl md:text-2xl leading-relaxed text-gray-600">
            {UI_TEXT.detection.hubSubtitle}
          </p>
        </div>

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
      </div>
    </section>
  );
}
