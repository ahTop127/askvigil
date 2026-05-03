import type { LucideIcon } from "lucide-react";

/** Supported detection input channels. */
export type DetectionType = "text" | "image" | "url" | "qr";

/** Normalized scam risk bucket. */
export type RiskLevel = "high" | "medium" | "low";

/**
 * Single user submission to the scam detection pipeline.
 *
 * @property type - Which channel was used
 * @property content - Plain text, URL string, or binary file
 */
export interface ScamDetectionInput {
  type: DetectionType;
  content: string | File;
}

/**
 * Result returned after analyzing user content (mock or real API).
 *
 * @property score - 0–100 risk score
 * @property riskLevel - Derived band from score
 * @property explanation - Human-readable summary
 * @property scamType - Internal scam category id
 * @property timestamp - ISO time of completion
 */
export interface ScamDetectionResult {
  score: number;
  riskLevel: RiskLevel;
  explanation: string;
  scamType: string;
  timestamp: string;
  detectionType?: DetectionType;
  overallRiskScore?: number;
  steps?: DetectionStepState[];
  suspiciousItems?: SuspiciousItem[];
  extractedText?: string;
  originalText?: string;
  submittedUrl?: string;
  redirectUrl?: string;
  qrDecodedContent?: string;
  qrContentType?: "url" | "sms" | "contact" | "plain-text";
  qrUrlReportAnalysis?: Record<string, unknown> | Record<string, unknown>[];
  /** URL scan: top signals from `unified_text_analysis.url_analysis[0]` meta fields. */
  urlMetaFeatures?: UrlMetaFeatureHighlight[];
  /** Unified scan ran both text + URL branches (text channel only). */
  dualTextUrlDetection?: boolean;
  /** URL-branch payload for dual-mode summary tab (includes branch score tier for guidance). */
  urlDetectionSummary?: UrlDetectionSummary;
  guidance?: string[];
  immediateGuidanceTitle?: string;
  immediateGuidanceSummary?: string;
  immediateGuidanceDontDo?: string[];
  immediateGuidanceSaferAction?: string[];
  relatedCase?: ScamCase;
}

export type DetectionStepStatus =
  | "completed"
  | "current"
  | "pending"
  | "failed";

export interface DetectionStepState {
  key: string;
  label: string;
  status: DetectionStepStatus;
}

export interface SuspiciousItem {
  text: string;
  reason: string;
}

/** One highlighted dimension from backend URL meta vector (0–1, independent). */
export interface UrlMetaFeatureHighlight {
  label: string;
  score: number;
  severity: "high" | "medium" | "low";
  explanation: string;
}

/** URL branch snapshot when unified scan returns both text + URL analysis (text input only). */
export interface UrlDetectionSummary {
  displayUrl: string;
  urlRiskScore: number;
  urlRiskLevel: RiskLevel;
  urlMetaFeatures?: UrlMetaFeatureHighlight[];
}

export interface ScamCase {
  id: string;
  title: string;
  summary: string;
  scamType: string;
  platform: string;
  date: string;
  whatHappened: string;
  warningSigns: string[];
  lesson: string;
  sourceUrl: string;
}

/**
 * Page-specific visuals and copy for a scam category.
 * Guidance and Learning pages use different images and gradients.
 */
export interface ScamTypePageCopy {
  /** Short paragraph shown on the card */
  description: string;
  /** Remote image URL for the card artwork */
  image: string;
  /** Tailwind gradient utility classes for the card header */
  bgColor: string;
  imageClass?: string;
}

/**
 * Shared scam category used on Guidance and Learning listings.
 *
 * @property id - Route segment, e.g. `job-scam`
 * @property title - Full display title
 * @property shortTitle - Compact label for horizontal nav
 * @property icon - Lucide icon component
 * @property guidance - Guidance page variant
 * @property learning - Learning page variant
 */
export interface ScamType {
  id: string;
  title: string;
  shortTitle: string;
  icon: LucideIcon;
  guidance: ScamTypePageCopy;
  learning: ScamTypePageCopy;
}

/**
 * Persisted onboarding / alert preferences for the current browser.
 */
export interface UserPreferences {
  topics: string[];
  goal: string;
  wantsAlerts: boolean;
  savedAt: string;
}

/** One actionable step in post-scam guidance. */
export interface GuidanceStep {
  id: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
}

/** Emergency hotline or agency contact. */
export interface EmergencyContact {
  name: string;
  phone: string;
  description: string;
}

/** Structured guidance payload for a scam type (mock API shape). */
export interface GuidanceContent {
  scamType: string;
  steps: GuidanceStep[];
  emergencyContacts: EmergencyContact[];
}

/** Learning article / module payload (mock API shape). */
export interface LearningContent {
  id: string;
  title: string;
  summary: string;
  sections: { heading: string; body: string }[];
}
