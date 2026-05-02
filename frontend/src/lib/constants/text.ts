/** User-visible validation and system errors */
export const ERROR_MESSAGES = {
  textInput: "Please enter message text to check.",
  imageUpload: "Please upload an image to check.",
  urlInput: "Please enter a URL to check.",
  qrUpload: "Please upload a QR code image to check.",
  invalidUrl: "This is not a valid URL. Please enter a valid link to check.",
  fileTooLarge: "File is too large. Please choose a smaller image.",
  unsupportedImage: "Unsupported image format.",
  textTooLong: "Text exceeds the maximum length allowed.",
  insufficientContent: "Content is insufficient and cannot be analyzed.",
  analysisFailed: "Unable to complete analysis. Please try again.",
  urlAnalyzeFailed: "Unable to analyze this URL. Please try again later.",
  unreachableUrl:
    "This URL could not be reached. Please check the link and try again.",
  qrDecodeFailed:
    "This is not a valid QR code. Please upload a valid QR code to check.",
} as const;

export const SUCCESS_MESSAGES = {
  detectionComplete: "Detection completed successfully",
  preferencesSaved: "Your preferences have been saved",
} as const;

/** Static marketing / UI copy (i18n-ready keys grouped by section) */
export const UI_TEXT = {
  hero: {
    titleLine1: "Secure Your",
    titleLine2: "Digital Journey.",
    subtitle:
      "Navigate where online threats meet the safety of awareness. AskVigil is your gateway to the empowering world of scam detection, where every check is a new discovery and every insight a story.",
    cta: "Get Protected",
    heroImageAlt: "University student concerned about phone security",
  },
  detection: {
    hubTitle: "Scam Detection Hub",
    hubSubtitle:
      "Check suspicious content in seconds and protect yourself online",
    startHere: "Start Here",
    tabText: "Text Message",
    tabImage: "Image/Screenshot",
    tabUrl: "URL Check",
    tabQR: "QR Code",
    textPlaceholder: "Paste suspicious message text here...",
    imageDropTitle: "Upload a screenshot or image",
    imageDropHint: "Drag and drop or click to browse",
    urlPlaceholder: "e.g. https://example.com or example.com",
    qrDropTitle: "Upload a QR code image",
    qrDropHint: "Drag and drop or click to browse",
    buttonCheck: "Check for Scams Now",
    analyzing: "Analyzing...",
  },
  privacy: {
    title: "Privacy Notice",
    description:
      "The URL you submit will be analyzed solely for scam detection. We do not store or share your data with third parties.",
    cancel: "Cancel",
    continue: "Continue",
  },
  result: {
    high: "High Risk Detected",
    medium: "Medium Risk",
    low: "Low Risk",
    scoreSuffix: "/ 100",
    guidanceCta: "Get Step-by-Step Guidance →",
    newAnalysis: "Start New Analysis",
  },
} as const;
