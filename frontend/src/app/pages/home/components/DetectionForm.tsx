import {
  forwardRef,
  memo,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
  type SyntheticEvent,
} from "react";
import {
  FileSearch,
  Check,
  LoaderCircle,
  Link as LinkIcon,
  QrCode,
  Shield,
  Upload,
  AlertCircle,
} from "lucide-react";
import { Button } from "@components/ui/button";
import { Textarea } from "@components/ui/textarea";
import { Input } from "@components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@components/ui/tabs";
import { UI_TEXT } from "@lib/constants/text";
import type { DetectionType } from "@lib/types";
import ReactCrop, {
  centerCrop,
  convertToPixelCrop,
  type Crop,
  type PixelCrop,
} from "react-image-crop";
import "react-image-crop/dist/ReactCrop.css";

export interface DetectionFormProps {
  activeTab: DetectionType;
  onTabChange: (tab: string) => void;
  textInput: string;
  onTextChange: (value: string) => void;
  urlInput: string;
  onUrlChange: (value: string) => void;
  imageFile: File | null;
  qrFile: File | null;
  onImageFile: (file: File | null) => void;
  onQrFile: (file: File | null) => void;
  error: string;
  isChecking: boolean;
  onRequestCheck: () => void;
}

export type DetectionFormHandle = {
  /** Triggers the same validation + privacy flow as the primary button. */
  requestCheck: () => void;
};

function TextDetectionInput({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}) {
  return (
    <div>
      <div className="relative">
        <Textarea
          placeholder={UI_TEXT.detection.textPlaceholder}
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
          }}
          maxLength={1000}
          className="min-h-[170px] resize-none text-base bg-muted/40 border-2 border-border focus:border-primary text-foreground placeholder:text-muted-foreground rounded-xl pb-8"
          disabled={disabled}
        />
        <div
          className={`absolute right-3 bottom-2 text-sm ${
            value.length > 900 ? "text-red-500" : "text-gray-500"
          }`}
        >
          {value.length} / 1000 characters
        </div>
      </div>

      <p className="mt-2 text-sm text-primary text-center whitespace-nowrap">
        Privacy notice: For scam detection only. Do not enter sensitive personal
        information.
      </p>
    </div>
  );
}

function ImageDetectionInput({
  file,
  disabled,
  onDrop,
  onDragOver,
  onPick,
  onFileChange,
  onRemove,
}: {
  file: File | null;
  disabled?: boolean;
  onDrop: (e: DragEvent<HTMLDivElement>) => void;
  onDragOver: (e: DragEvent<HTMLDivElement>) => void;
  onPick: () => void;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onRemove: () => void;
}) {
  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      className="border-2 border-dashed border-border rounded-xl p-10 text-center hover:border-primary transition-colors cursor-pointer bg-muted/35 hover:bg-primary/10"
      onClick={onPick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onPick();
        }
      }}
      role="button"
      tabIndex={0}
    >
      {!file ? (
        <>
          <Upload className="w-12 h-12 text-primary mx-auto mb-3" />
          <p className="text-gray-700 mb-1 font-medium">
            {UI_TEXT.detection.imageDropTitle}
          </p>
          <p className="text-sm text-gray-500">
            {UI_TEXT.detection.imageDropHint}
          </p>
        </>
      ) : (
        <>
          {/*image preview*/}
          <img
            src={URL.createObjectURL(file)}
            alt="Preview"
            className="max-h-48 mx-auto rounded-lg mb-3 object-contain"
          />

          <p className="text-sm text-gray-600">{file.name}</p>

          <p className="text-xs text-gray-400 mt-1">Click to change image</p>
          {/*remove button*/}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="text-red-500 text-xm mt-2 hover:underline"
          >
            Remove image
          </button>
        </>
      )}

      <input
        id="image-upload"
        type="file"
        accept="image/*"
        onChange={onFileChange}
        className="hidden"
        disabled={disabled}
      />
    </div>
  );
}

function URLDetectionInput({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}) {
  return (
    <div className="space-y-2">
      <label htmlFor="url-check-input" className="sr-only">
        {UI_TEXT.detection.tabUrl}
      </label>
      <Input
        id="url-check-input"
        type="url"
        placeholder={UI_TEXT.detection.urlPlaceholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        maxLength={2048}
        disabled={disabled}
        className="h-12 text-base bg-muted/35 border-2 border-border focus:border-primary rounded-xl"
      />
    </div>
  );
}

function QRCodeDetectionInput({
  file,
  disabled,
  onDrop,
  onDragOver,
  onPick,
  onFileChange,
}: {
  file: File | null;
  disabled?: boolean;
  onDrop: (e: DragEvent<HTMLDivElement>) => void;
  onDragOver: (e: DragEvent<HTMLDivElement>) => void;
  onPick: () => void;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      className="border-2 border-dashed border-border rounded-xl p-10 text-center hover:border-primary transition-colors cursor-pointer bg-muted/35 hover:bg-primary/10"
      onClick={onPick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onPick();
        }
      }}
      role="button"
      tabIndex={0}
    >
      <QrCode className="w-12 h-12 text-primary mx-auto mb-3" aria-hidden />
      <p className="text-gray-700 mb-1 font-medium">
        {UI_TEXT.detection.qrDropTitle}
      </p>
      <p className="text-sm text-gray-500">
        {file ? file.name : UI_TEXT.detection.qrDropHint}
      </p>
      <input
        id="qr-upload"
        type="file"
        accept="image/*"
        onChange={onFileChange}
        className="hidden"
        disabled={disabled}
      />
    </div>
  );
}

/** Pixel crop is in displayed `<img>` CSS pixels; map to natural size for export. */
async function getCroppedFile(
  imageEl: HTMLImageElement,
  pixelCrop: PixelCrop,
  fileName: string,
): Promise<File> {
  const scaleX = imageEl.naturalWidth / imageEl.width;
  const scaleY = imageEl.naturalHeight / imageEl.height;
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  if (!ctx) {
    throw new Error("Could not create canvas context");
  }

  const outW = Math.max(1, Math.round(pixelCrop.width * scaleX));
  const outH = Math.max(1, Math.round(pixelCrop.height * scaleY));
  canvas.width = outW;
  canvas.height = outH;

  ctx.drawImage(
    imageEl,
    pixelCrop.x * scaleX,
    pixelCrop.y * scaleY,
    pixelCrop.width * scaleX,
    pixelCrop.height * scaleY,
    0,
    0,
    outW,
    outH,
  );

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error("Canvas is empty"));
          return;
        }

        resolve(
          new File([blob], fileName, {
            type: "image/jpeg",
          }),
        );
      },
      "image/jpeg",
      0.95,
    );
  });
}

/**
 * Tabbed detection inputs (text, image, URL, QR) with shared actions.
 */
const DetectionFormInner = forwardRef<DetectionFormHandle, DetectionFormProps>(
  function DetectionForm(props, ref) {
    const {
      activeTab,
      onTabChange,
      textInput,
      onTextChange,
      urlInput,
      onUrlChange,
      imageFile,
      qrFile,
      onImageFile,
      onQrFile,
      error,
      isChecking,
      onRequestCheck,
    } = props;

    const [showCropModal, setShowCropModal] = useState(false);
    const [tempImageUrl, setTempImageUrl] = useState<string | null>(null);
    const [tempImageName, setTempImageName] = useState("cropped-image.jpg");
    const cropImageRef = useRef<HTMLImageElement>(null);

    const [crop, setCrop] = useState<Crop>();
    const [completedCrop, setCompletedCrop] = useState<PixelCrop | null>(null);

    useImperativeHandle(
      ref,
      () => ({
        requestCheck: () => onRequestCheck(),
      }),
      [onRequestCheck],
    );

    const onCropImageLoad = useCallback(
      (e: SyntheticEvent<HTMLImageElement>) => {
        const { width, height } = e.currentTarget;
        setCrop(
          centerCrop({ unit: "%", width: 100, height: 100 }, width, height),
        );
        setCompletedCrop(null);
      },
      [],
    );

    const resetCropState = useCallback(() => {
      if (tempImageUrl) {
        URL.revokeObjectURL(tempImageUrl);
      }

      setTempImageUrl(null);
      setTempImageName("cropped-image.jpg");
      setShowCropModal(false);
      setCrop(undefined);
      setCompletedCrop(null);
    }, [tempImageUrl]);

    const handleCropCancel = useCallback(() => {
      resetCropState();
    }, [resetCropState]);

    const handleCropSave = useCallback(async () => {
      const img = cropImageRef.current;
      if (!img || !crop) return;

      try {
        const pixelCrop =
          completedCrop ?? convertToPixelCrop(crop, img.width, img.height);
        const croppedFile = await getCroppedFile(
          img,
          pixelCrop,
          `cropped-${tempImageName}`,
        );

        onImageFile(croppedFile);
        resetCropState();
      } catch (err) {
        console.error("Crop failed:", err);
      }
    }, [completedCrop, crop, onImageFile, resetCropState, tempImageName]);

    const handleFileChange = useCallback(
      (e: ChangeEvent<HTMLInputElement>, type: "image" | "qr") => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (type === "image") {
          const imageUrl = URL.createObjectURL(file);
          setTempImageUrl(imageUrl);
          setTempImageName(file.name);
          setShowCropModal(true);
          return;
        }

        onQrFile(file);
      },
      [onQrFile],
    );

    const handleDrop = useCallback(
      (e: DragEvent<HTMLDivElement>, type: "image" | "qr") => {
        e.preventDefault();

        const file = e.dataTransfer.files?.[0];
        if (!file?.type.startsWith("image/")) return;

        if (type === "image") {
          const imageUrl = URL.createObjectURL(file);
          setTempImageUrl(imageUrl);
          setTempImageName(file.name);
          setShowCropModal(true);
          return;
        }

        onQrFile(file);
      },
      [onQrFile],
    );

    const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
    }, []);

    const tabValue = useMemo(() => activeTab, [activeTab]);
    const analysisSteps = useMemo(() => {
      if (activeTab === "image") {
        return ["Upload", "Extract Text", "Check Risks", "Red Flags"];
      }
      if (activeTab === "qr") {
        return ["Upload", "Decode QR", "Check Risks", "Red Flags"];
      }
      return ["Upload", "Check Risks", "Red Flags"];
    }, [activeTab]);
    const [currentStepIndex, setCurrentStepIndex] = useState(0);

    useEffect(() => {
      if (!isChecking) {
        setCurrentStepIndex(0);
        return;
      }
      setCurrentStepIndex(0);
      const interval = window.setInterval(() => {
        setCurrentStepIndex((prev) => {
          const maxStep = Math.max(0, analysisSteps.length - 1);
          if (prev >= maxStep) return maxStep;
          return prev + 1;
        });
      }, 1200);
      return () => window.clearInterval(interval);
    }, [analysisSteps.length, isChecking]);

    return (
      <div className="relative bg-card rounded-3xl shadow-sm border border-border p-8 md:p-10">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-1 bg-primary rounded-full" />

        <Tabs value={tabValue} onValueChange={onTabChange} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-6 bg-muted/50 border border-border h-auto p-1 gap-1 rounded-full">
            <TabsTrigger
              value="text"
              className="rounded-full py-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-muted-foreground font-semibold"
            >
              <FileSearch className="w-4 h-4 mr-1 shrink-0" />
              {UI_TEXT.detection.tabText}
            </TabsTrigger>
            <TabsTrigger
              value="image"
              className="rounded-full py-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-muted-foreground font-semibold"
            >
              <Upload className="w-4 h-4 mr-1 shrink-0" />
              {UI_TEXT.detection.tabImage}
            </TabsTrigger>
            <TabsTrigger
              value="url"
              className="rounded-full py-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-muted-foreground font-semibold"
            >
              <LinkIcon className="w-4 h-4 mr-1 shrink-0" />
              {UI_TEXT.detection.tabUrl}
            </TabsTrigger>
            <TabsTrigger
              value="qr"
              className="rounded-full py-2 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-muted-foreground font-semibold"
            >
              <QrCode className="w-4 h-4 mr-1 shrink-0" />
              {UI_TEXT.detection.tabQR}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="text" className="space-y-4 mt-0">
            <TextDetectionInput
              value={textInput}
              onChange={onTextChange}
              disabled={isChecking}
            />
          </TabsContent>

          <TabsContent value="image" className="space-y-4 mt-0">
            <ImageDetectionInput
              file={imageFile}
              disabled={isChecking}
              onDrop={(e) => handleDrop(e, "image")}
              onDragOver={handleDragOver}
              onPick={() => document.getElementById("image-upload")?.click()}
              onFileChange={(e) => handleFileChange(e, "image")}
              onRemove={() => onImageFile(null)}
            />
          </TabsContent>

          <TabsContent value="url" className="space-y-4 mt-0">
            <URLDetectionInput
              value={urlInput}
              onChange={onUrlChange}
              disabled={isChecking}
            />
          </TabsContent>

          <TabsContent value="qr" className="space-y-4 mt-0">
            <QRCodeDetectionInput
              file={qrFile}
              disabled={isChecking}
              onDrop={(e) => handleDrop(e, "qr")}
              onDragOver={handleDragOver}
              onPick={() => document.getElementById("qr-upload")?.click()}
              onFileChange={(e) => handleFileChange(e, "qr")}
            />
          </TabsContent>
        </Tabs>

        {error && (
          <div
            className="flex items-center gap-2 text-red-700 bg-red-50 px-4 py-3 rounded-xl mb-4 border-2 border-red-200"
            role="alert"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" aria-hidden />
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        {isChecking ? (
          <div className="mt-6 rounded-2xl border border-primary/35 bg-primary/10 p-4 md:p-5 animate-fade-in">
            <div className="relative transition-all duration-500 ease-out">
              <div className="absolute top-4 left-0 right-0 h-1 bg-primary/25 rounded-full" />
              <div
                className="absolute top-4 left-0 h-1 bg-primary rounded-full transition-all duration-700"
                style={{
                  width: `${(currentStepIndex / Math.max(analysisSteps.length - 1, 1)) * 100}%`,
                }}
              />
              <div
                className="relative grid gap-2"
                style={{
                  gridTemplateColumns: `repeat(${analysisSteps.length}, minmax(0, 1fr))`,
                }}
              >
                {analysisSteps.map((step, index) => (
                  <div
                    key={step}
                    className="flex flex-col items-center text-center transition-transform duration-500"
                  >
                    {index < currentStepIndex ? (
                      <span className="w-8 h-8 rounded-full bg-primary text-primary-foreground inline-flex items-center justify-center border-2 border-primary/50">
                        <Check className="w-4 h-4" />
                      </span>
                    ) : index === currentStepIndex ? (
                      <span className="w-8 h-8 rounded-full border-2 border-primary bg-background inline-flex items-center justify-center">
                        <LoaderCircle className="w-4 h-4 animate-spin text-primary" />
                      </span>
                    ) : (
                      <span className="w-8 h-8 rounded-full border-2 border-primary/50 bg-background" />
                    )}
                    <p className="mt-3 text-xs md:text-sm font-semibold text-primary">
                      {step}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <Button
            type="button"
            onClick={onRequestCheck}
            className="w-full h-14 text-base font-semibold bg-primary hover:bg-secondary text-primary-foreground border-0 transition-all mt-6 rounded-xl shadow-md"
          >
            <Shield className="w-5 h-5 mr-2" aria-hidden />
            {UI_TEXT.detection.buttonCheck}
          </Button>
        )}

        {showCropModal && tempImageUrl && (
          <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
            <div className="bg-white w-full max-w-2xl rounded-2xl shadow-xl overflow-hidden">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">
                  Crop image
                </h3>
                <p className="text-sm text-gray-500">
                  Select the suspicious part of the image before analysis.
                </p>
              </div>

              <div className="relative w-full min-h-[320px] max-h-[min(70vh,520px)] bg-black flex items-center justify-center p-2 overflow-auto">
                <ReactCrop
                  crop={crop}
                  onChange={(_pixelCrop, percentCrop) => setCrop(percentCrop)}
                  onComplete={(c) => setCompletedCrop(c)}
                  keepSelection
                  minWidth={32}
                  minHeight={32}
                  className="max-w-full"
                >
                  <img
                    ref={cropImageRef}
                    src={tempImageUrl}
                    alt="Crop preview"
                    className="max-w-full max-h-[min(60vh,480px)] w-auto h-auto block"
                    onLoad={onCropImageLoad}
                  />
                </ReactCrop>
              </div>

              <div className="p-4 border-t border-gray-200">
                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCropCancel}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    disabled={!crop}
                    onClick={() => void handleCropSave()}
                  >
                    Continue
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  },
);

export const DetectionForm = memo(DetectionFormInner);
