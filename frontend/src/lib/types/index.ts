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
  steps?: DetectionStepState[];
  suspiciousItems?: SuspiciousItem[];
  extractedText?: string;
  originalText?: string;
  submittedUrl?: string;
  redirectUrl?: string;
  qrDecodedContent?: string;
  qrContentType?: "url" | "sms" | "contact" | "plain-text";
  guidance?: string[];
  relatedCase?: ScamCase;
}

export type DetectionStepStatus = "completed" | "current" | "pending" | "failed";

export interface DetectionStepState {
  key: string;
  label: string;
  status: DetectionStepStatus;
}

export interface SuspiciousItem {
  text: string;
  reason: string;
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
