import { APP_CONFIG } from "@lib/config/app";
import type { ScamCase } from "@lib/types";

type ScamTypeApi =
  | "JOB_SCAM"
  | "phishing"
  | "qr_code_scam"
  | "otp_scam"
  | "suspicious_link";
type PlatformApi =
  | "whatsapp"
  | "facebook"
  | "tiktok"
  | "phone_call"
  | "phone_message"
  | "email"
  | "other";

interface ScamCaseApiResponse {
  id: number;
  title: string;
  content: string;
  scam_type: string;
  platform: string;
  news_date: string;
  source?: string | null;
  url_link?: string | null;
}

interface ScamCaseFilterRequest {
  scam_type: ScamTypeApi | null;
  platform: PlatformApi | null;
  time_range: 0 | 1 | 2 | 3;
}

function buildUrl(path: string): string {
  return `${APP_CONFIG.api.baseUrl.replace(/\/$/, "")}${path}`;
}

function mapScamTypeToApi(scamType: string): ScamTypeApi | null {
  switch (scamType) {
    case "job-scam":
      return "JOB_SCAM";
    case "phishing":
      return "phishing";
    case "qr-scam":
      return "qr_code_scam";
    case "otp-scam":
      return "otp_scam";
    case "suspicious-link":
      return "suspicious_link";
    default:
      return null;
  }
}

function mapPlatformToApi(platform: string): PlatformApi | null {
  switch (platform) {
    case "WhatsApp":
      return "whatsapp";
    case "Telegram":
    case "Social Media":
      return "other";
    case "SMS":
      return "phone_message";
    case "Email":
      return "email";
    case "Phone Call":
      return "phone_call";
    default:
      return null;
  }
}

function mapDateToApi(date: string): 0 | 1 | 2 | 3 {
  switch (date) {
    case "3m":
      return 1;
    case "6m":
      return 2;
    case "30d":
      return 1;
    case "90d":
      return 2;
    case "1y":
      return 3;
    default:
      return 0;
  }
}

function normalizeScamType(type: string): string {
  switch (type) {
    case "JOB_SCAM":
      return "job-scam";
    case "qr_code_scam":
      return "qr-scam";
    case "otp_scam":
      return "otp-scam";
    case "suspicious_link":
      return "suspicious-link";
    case "phishing":
      return "phishing";
    default:
      return "suspicious-link";
  }
}

function normalizePlatform(platform: string): string {
  switch (platform) {
    case "whatsapp":
      return "WhatsApp";
    case "facebook":
    case "tiktok":
      return "Social Media";
    case "phone_call":
      return "Phone Call";
    case "phone_message":
      return "SMS";
    case "email":
      return "Email";
    default:
      return "Other";
  }
}

function toSummary(content: string): string {
  const trimmed = content.trim();
  if (!trimmed) return "No summary available.";
  if (trimmed.length <= 180) return trimmed;
  return `${trimmed.slice(0, 180).trimEnd()}...`;
}

function mapCase(item: ScamCaseApiResponse): ScamCase {
  return {
    id: String(item.id),
    title: item.title,
    summary: toSummary(item.content),
    scamType: normalizeScamType(item.scam_type),
    platform: normalizePlatform(item.platform),
    date: item.news_date,
    whatHappened: item.content,
    warningSigns: [],
    lesson: item.source ?? "Refer to the source link for verified details.",
    sourceUrl: item.url_link ?? "",
  };
}

async function readError(response: Response): Promise<string | null> {
  try {
    const json = (await response.json()) as { detail?: unknown };
    if (typeof json.detail === "string" && json.detail.trim()) return json.detail;
    return null;
  } catch {
    return null;
  }
}

export async function fetchScamCases(filters: {
  scamType: string;
  platform: string;
  date: string;
}): Promise<ScamCase[]> {
  const payload: ScamCaseFilterRequest = {
    scam_type: mapScamTypeToApi(filters.scamType),
    platform: mapPlatformToApi(filters.platform),
    time_range: mapDateToApi(filters.date),
  };

  const response = await fetch(buildUrl("/v1/scam/filter"), {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail ?? `Failed to fetch scam cases (${response.status})`);
  }

  const data = (await response.json()) as ScamCaseApiResponse[];
  return data.map(mapCase);
}

export async function fetchScamCaseById(caseId: string): Promise<ScamCase> {
  const response = await fetch(buildUrl(`/v1/scam/${encodeURIComponent(caseId)}`), {
    method: "GET",
    headers: { Accept: "application/json" },
    credentials: "include",
  });

  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail ?? `Failed to fetch case detail (${response.status})`);
  }

  const data = (await response.json()) as ScamCaseApiResponse;
  return mapCase(data);
}
