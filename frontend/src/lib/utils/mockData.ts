/**
 * Mock factories for local development. Replace with real API responses in production.
 */
import type {
  GuidanceContent,
  LearningContent,
  RiskLevel,
  ScamDetectionInput,
  ScamDetectionResult,
} from "@lib/types";

const SCAM_IDS = [
  "job-scam",
  "phishing",
  "otp-scam",
  "qr-scam",
  "suspicious-link",
] as const;

function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Deterministic pseudo-random from optional seed (for tests). */
function rng(seed?: number) {
  const s = seed ?? Date.now() % 2147483647;
  return mulberry32(s);
}

export function generateRandomScamType(seed?: number): string {
  const r = rng(seed);
  return SCAM_IDS[Math.floor(r() * SCAM_IDS.length)];
}

export function generateMockExplanation(riskLevel: RiskLevel, seed?: number): string {
  const r = rng(seed);
  if (riskLevel === "high") {
    const explanations = [
      "This message contains urgent language and suspicious links.",
      "Multiple red flags detected: requests personal information and creates urgency.",
      "This message uses typical phishing tactics to steal information.",
    ];
    return explanations[Math.floor(r() * explanations.length)];
  }
  if (riskLevel === "medium") {
    return "Some suspicious patterns detected. Exercise caution and verify the sender.";
  }
  return "No suspicious patterns detected in this message. However, always remain vigilant.";
}

function scoreToRisk(score: number): RiskLevel {
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

export function generateMockDetectionResult(
  input: ScamDetectionInput,
  seed?: number
): ScamDetectionResult {
  const r = rng(seed);
  const score = Math.floor(r() * 100);
  const riskLevel = scoreToRisk(score);
  return {
    score,
    riskLevel,
    explanation: generateMockExplanation(riskLevel, seed),
    scamType: generateRandomScamType(seed),
    timestamp: new Date().toISOString(),
  };
}

export function generateMockGuidanceContent(scamType: string): GuidanceContent {
  return {
    scamType,
    steps: [
      {
        id: "1",
        title: "Stop and document",
        description: "Do not send more money or share more data. Save screenshots and messages.",
        priority: "high",
      },
      {
        id: "2",
        title: "Contact your bank",
        description: "If payment details were shared, notify your bank or card issuer immediately.",
        priority: "high",
      },
    ],
    emergencyContacts: [
      {
        name: "National Scam Response Centre (example)",
        phone: "997",
        description: "24/7 hotline for scam reports (mock data).",
      },
    ],
  };
}

export function generateMockLearningContent(id: string): LearningContent {
  return {
    id,
    title: `Understanding ${id.replace(/-/g, " ")}`,
    summary: "Mock learning summary — replace with CMS or API content.",
    sections: [
      { heading: "Overview", body: "Mock section body." },
      { heading: "Red flags", body: "Mock red flags list." },
    ],
  };
}
