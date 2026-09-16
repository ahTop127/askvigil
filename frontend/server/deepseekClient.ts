export type DeepSeekEnv = {
  apiKey: string;
  baseUrl: string;
  model: string;
};

export type ScamType = "phishing" | "job-scam" | "otp-scam" | "unknown";

export type DeepSeekScanResult = {
  risk_score: number;
  scam_type: ScamType;
  reasons: Array<{ text: string; reason: string }>;
  guidance: {
    title: string;
    summary: string;
    dont_do: string[];
    safer_action: string[];
  };
};

const SYSTEM_PROMPT = `You are a scam and fraud classifier for messages and URLs seen by people in Malaysia (English, Malay, or Chinese).

Return ONLY a JSON object. No markdown, no extra keys.
Schema:
{
  "risk_score": number between 0 and 1,
  "scam_type": "phishing" | "job-scam" | "otp-scam" | "unknown",
  "reasons": [{"text": string, "reason": string}],
  "guidance": {
    "title": string,
    "summary": string,
    "dont_do": string[],
    "safer_action": string[]
  }
}

Rules:
- risk_score is YOUR probability that this is a scam. 0 = clearly safe, 1 = clearly a scam.
- scam_type: phishing = fake login/bank/account; job-scam = fake job/task income; otp-scam = asking for OTP/TAC/verification code; unknown = not enough signal or not those types.
- reasons: 1 to 5 short items. "text" is a short span copied from the input when possible.
- If the input is only a URL, still fill the same schema.
- Do not invent facts about a website you cannot know. Use the visible string only.`;

type AnthropicContent =
  | { type: "text"; text: string }
  | { type: string; [key: string]: unknown };

type AnthropicMessage = {
  content?: AnthropicContent[];
  error?: { message?: string; type?: string };
};

export function readDeepSeekEnv(
  env: Record<string, string | undefined>,
): DeepSeekEnv {
  const apiKey = env.DEEPSEEK_API_KEY?.trim();
  if (!apiKey) {
    throw new Error("DEEPSEEK_API_KEY is missing");
  }
  return {
    apiKey,
    baseUrl: (
      env.DEEPSEEK_BASE_URL ?? "https://api.deepseek.com/anthropic"
    ).replace(/\/$/, ""),
    model: env.DEEPSEEK_MODEL?.trim() || "deepseek-flash",
  };
}

export async function classifyWithDeepSeek(
  input: string,
  env: DeepSeekEnv,
): Promise<DeepSeekScanResult> {
  const response = await fetch(`${env.baseUrl}/v1/messages`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": env.apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: env.model,
      max_tokens: 1024,
      temperature: 0,
      thinking: { type: "disabled" },
      system: SYSTEM_PROMPT,
      messages: [
        {
          role: "user",
          content: `Classify this user-submitted content:\n\n${input}`,
        },
      ],
    }),
  });

  const raw = (await response.json()) as AnthropicMessage;
  if (!response.ok) {
    const message =
      raw.error?.message ?? `DeepSeek request failed (${response.status})`;
    throw new Error(message);
  }

  const text = extractAssistantText(raw);
  return normalizeScanResult(parseJsonObject(text));
}

export function extractAssistantText(message: AnthropicMessage): string {
  const blocks = Array.isArray(message.content) ? message.content : [];
  const text = blocks
    .filter((block) => block.type === "text")
    .map((block) => (typeof block.text === "string" ? block.text : ""))
    .join("\n")
    .trim();
  if (!text) {
    throw new Error("DeepSeek returned empty text");
  }
  return text;
}

export function parseJsonObject(text: string): Record<string, unknown> {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  const candidate = (fenced?.[1] ?? text).trim();
  const start = candidate.indexOf("{");
  const end = candidate.lastIndexOf("}");
  if (start < 0 || end < 0 || end <= start) {
    throw new Error("DeepSeek did not return JSON");
  }
  const parsed: unknown = JSON.parse(candidate.slice(start, end + 1));
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("DeepSeek JSON was not an object");
  }
  return parsed as Record<string, unknown>;
}

export function normalizeScanResult(
  raw: Record<string, unknown>,
): DeepSeekScanResult {
  const score = clamp01(toNumber(raw.risk_score));
  return {
    risk_score: score,
    scam_type: normalizeScamType(raw.scam_type),
    reasons: toReasons(raw.reasons),
    guidance: toGuidance(raw.guidance),
  };
}

function toNumber(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const n = Number(value);
    if (Number.isFinite(n)) return n;
  }
  return 0;
}

function clamp01(value: number): number {
  const scaled = value > 1 && value <= 100 ? value / 100 : value;
  return Math.max(0, Math.min(1, scaled));
}

function normalizeScamType(value: unknown): ScamType {
  const raw = typeof value === "string" ? value.trim().toLowerCase() : "";
  const compact = raw.replace(/[\s-]+/g, "_");
  if (compact === "phishing") return "phishing";
  if (compact === "job_scam" || compact === "jobscam") return "job-scam";
  if (compact === "otp_scam" || compact === "otpscam") return "otp-scam";
  return "unknown";
}

function toReasons(
  value: unknown,
): Array<{ text: string; reason: string }> {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const o = item as Record<string, unknown>;
      const text = asText(o.text) ?? asText(o.span) ?? "signal";
      const reason = asText(o.reason);
      if (!reason) return null;
      return { text, reason };
    })
    .filter((item): item is { text: string; reason: string } => item !== null)
    .slice(0, 5);
}

function toGuidance(value: unknown): DeepSeekScanResult["guidance"] {
  const o =
    value && typeof value === "object"
      ? (value as Record<string, unknown>)
      : {};
  return {
    title: asText(o.title) ?? "Scam check result",
    summary: asText(o.summary) ?? "Review the highlighted signals before acting.",
    dont_do: toStringList(o.dont_do),
    safer_action: toStringList(o.safer_action),
  };
}

function asText(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function toStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (item): item is string => typeof item === "string" && item.trim().length > 0,
  );
}
