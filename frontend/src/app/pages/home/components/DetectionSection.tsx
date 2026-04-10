import { useCallback } from "react";
import { Shield } from "lucide-react";
import { Button } from "@components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@components/ui/dialog";
import { UI_TEXT } from "@lib/constants/text";
import type { UseScamDetectionReturn } from "../hooks/useScamDetection";
import { DetectionForm } from "./DetectionForm";
import { ResultDisplay } from "./ResultDisplay";

export interface DetectionSectionProps {
  detection: UseScamDetectionReturn;
}

/**
 * Hub header, detection form vs result, and privacy confirmation dialog.
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
    showPrivacyDialog,
    result,
    handleCheck,
    confirmCheck,
    cancelPrivacy,
    resetDetection,
    setShowPrivacyDialog,
    clearError,
  } = detection;

  const onTabChange = useCallback(
    (tab: string) => {
      clearError();
      setActiveTab(tab);
    },
    [clearError, setActiveTab]
  );

  return (
    <section id="check-section" className="py-20 bg-[#F7F8FA] relative overflow-hidden">
      <div className="max-w-4xl mx-auto px-4 relative z-10">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-[#EAA866] text-white px-4 py-2 rounded-full text-sm font-medium mb-4">
            <Shield className="w-4 h-4" aria-hidden />
            {UI_TEXT.detection.startHere}
          </div>
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

      <Dialog open={showPrivacyDialog} onOpenChange={setShowPrivacyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold">{UI_TEXT.privacy.title}</DialogTitle>
            <DialogDescription className="text-base leading-relaxed text-gray-600">{UI_TEXT.privacy.description}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={cancelPrivacy}>
              {UI_TEXT.privacy.cancel}
            </Button>
            <Button onClick={() => void confirmCheck()}>
              {UI_TEXT.privacy.continue}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
