/**
 * Central application configuration (env-aware).
 * Use `as const` for literal type inference on nested keys.
 */
export const APP_CONFIG = {
  name: "AskVigil",
  version: "1.0.0",

  api: {
    baseUrl: "/api",
    timeout: 30_000,
  },

  detection: {
    maxFileSize: 5 * 1024 * 1024,
    supportedImageFormats: ["image/jpeg", "image/png", "image/webp"] as const,
    maxTextLength: 5000,
  },

  riskLevels: {
    high: {
      minScore: 70,
      color: "#EF4444",
      icon: "AlertCircle" as const,
    },
    medium: {
      minScore: 40,
      color: "#F59E0B",
      icon: "AlertCircle" as const,
    },
    low: {
      minScore: 0,
      color: "#10B981",
      icon: "Shield" as const,
    },
  },

  /** localStorage keys (legacy keys preserved for existing users) */
  storageKeys: {
    detectionHistory: "askvigil_history",
  },
} as const;

export type AppConfig = typeof APP_CONFIG;
