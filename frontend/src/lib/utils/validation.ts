import { APP_CONFIG } from "@lib/config/app";
import type { DetectionType } from "@lib/types";
import { ERROR_MESSAGES } from "@lib/constants/text";

export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

const URL_REGEX =
  /^(https?:\/\/)?([\w-]+\.)+[\w-]+(\/[\w\-./?%&=+#]*)?$/i;

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidUrl(url: string): boolean {
  const t = url.trim();
  if (!t) return false;
  try {
    const u = new URL(t.startsWith("http") ? t : `https://${t}`);
    return Boolean(u.hostname);
  } catch {
    return URL_REGEX.test(t);
  }
}

export function isValidEmail(email: string): boolean {
  return EMAIL_REGEX.test(email.trim());
}

export function isValidImageFile(file: File): boolean {
  if (file.size > APP_CONFIG.detection.maxFileSize) {
    return false;
  }
  return APP_CONFIG.detection.supportedImageFormats.includes(
    file.type as (typeof APP_CONFIG.detection.supportedImageFormats)[number]
  );
}

export function isValidQRCodeFile(file: File): boolean {
  return isValidImageFile(file);
}

export function isValidTextInput(text: string): boolean {
  const t = text.trim();
  return t.length > 0 && t.length <= APP_CONFIG.detection.maxTextLength;
}

/**
 * Validates a detection payload before calling the API.
 */
export function validateDetectionInput(
  type: DetectionType,
  content: string | File
): ValidationResult {
  switch (type) {
    case "text": {
      const text = typeof content === "string" ? content : "";
      if (!text.trim()) {
        return { isValid: false, error: ERROR_MESSAGES.textInput };
      }
      if (text.length > APP_CONFIG.detection.maxTextLength) {
        return { isValid: false, error: ERROR_MESSAGES.textTooLong };
      }
      return { isValid: true };
    }
    case "image":
    case "qr": {
      if (!(content instanceof File)) {
        return { isValid: false, error: ERROR_MESSAGES.imageUpload };
      }
      if (!isValidImageFile(content)) {
        return {
          isValid: false,
          error: content.size > APP_CONFIG.detection.maxFileSize
            ? ERROR_MESSAGES.fileTooLarge
            : ERROR_MESSAGES.unsupportedImage,
        };
      }
      return { isValid: true };
    }
    case "url": {
      const url = typeof content === "string" ? content : "";
      if (!url.trim()) {
        return { isValid: false, error: ERROR_MESSAGES.urlInput };
      }
      if (!isValidUrl(url.trim())) {
        return { isValid: false, error: ERROR_MESSAGES.invalidUrl };
      }
      return { isValid: true };
    }
    default:
      return { isValid: false, error: ERROR_MESSAGES.textInput };
  }
}
