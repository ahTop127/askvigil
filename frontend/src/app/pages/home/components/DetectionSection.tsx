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
      className="relative overflow-hidden bg-[#F6F4F1] pt-12 pb-20 md:pt-14"
    >
      {/* Layered gradient: anchored on #F6F4F1, subtle luminosity shift */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-gradient-to-br from-[#FAFAF8] via-[#F6F4F1] to-[#E8E4DE]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-gradient-to-t from-transparent via-transparent to-[#FFFCF9]/75"
      />
      {/* Soft radial accents — restrained, editorial */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-28 left-[12%] h-[28rem] w-[28rem] -translate-x-1/2 rounded-full bg-[#283C5E]/[0.045] blur-[100px]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute top-8 -right-16 h-[22rem] w-[22rem] rounded-full bg-[#B8A99A]/12 blur-[88px]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-0 left-1/2 h-64 w-[120%] -translate-x-1/2 rounded-[100%] bg-gradient-to-t from-[#DFD8CF]/35 via-transparent to-transparent"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-white/55 to-transparent"
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
