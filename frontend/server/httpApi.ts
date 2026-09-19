import { randomUUID } from "node:crypto";
import type { IncomingMessage, ServerResponse } from "node:http";
import { createRequire } from "node:module";
import { runTextScan, type ScanInputType } from "./scanPipeline.js";

const caseRows = createRequire(import.meta.url)(
  "./data/scam-cases.json",
) as Omit<CaseRow, "id">[];

type CaseRow = {
  id: number;
  title: string;
  content: string;
  source: string | null;
  url_link: string | null;
  scam_type: string;
  platform: string;
  news_date: string;
};

const CASE_LIBRARY: CaseRow[] = (caseRows as Omit<CaseRow, "id">[]).map(
  (row, index) => ({ id: index + 1, ...row }),
);

const STATS_PUBLIC = {
  users_protected: 0,
  checks_daily: 0,
  links_analysed: 0,
  total_checks: 0,
};

const EMPTY_TREND = {
  days: 7,
  risk_level: "all",
  input_types: [],
  points: [],
};

const EMPTY_INPUT_DIST = {
  text_count: 0,
  image_count: 0,
  url_count: 0,
  qr_count: 0,
  total: 0,
};

const EMPTY_RISK_DIST = {
  low_count: 0,
  medium_count: 0,
  high_count: 0,
  unknown_count: 0,
  total: 0,
};

const EMPTY_RANKING = { total_cases: 0, items: [] };

export async function handleAskvigilApi(
  req: IncomingMessage,
  res: ServerResponse,
  env: Record<string, string | undefined>,
): Promise<void> {
  const url = getRequestPath(req);

  try {
    if (req.method === "GET" && url === "/api/v1/session/init") {
      const sessionId = randomUUID();
      res.setHeader(
        "Set-Cookie",
        `session_id=${sessionId}; Path=/; SameSite=Lax`,
      );
      sendJson(res, 200, { status: "ok", session_id: sessionId });
      return;
    }

    if (req.method === "GET" && url === "/api/v1/stats/public") {
      sendJson(res, 200, STATS_PUBLIC);
      return;
    }
    if (req.method === "GET" && url === "/api/v1/stats/detection-trend") {
      sendJson(res, 200, EMPTY_TREND);
      return;
    }
    if (
      req.method === "GET" &&
      url === "/api/v1/stats/input-type-distribution"
    ) {
      sendJson(res, 200, EMPTY_INPUT_DIST);
      return;
    }
    if (
      req.method === "GET" &&
      url === "/api/v1/stats/risk-level-distribution"
    ) {
      sendJson(res, 200, EMPTY_RISK_DIST);
      return;
    }
    if (req.method === "GET" && url === "/api/v1/stats/scam-type-ranking") {
      sendJson(res, 200, EMPTY_RANKING);
      return;
    }

    if (req.method === "GET" && url === "/api/v1/learning/categories") {
      sendJson(res, 200, []);
      return;
    }
    if (req.method === "GET" && url.startsWith("/api/v1/learning/quizzes")) {
      sendJson(res, 200, []);
      return;
    }

    if (req.method === "POST" && url === "/api/v1/detection/scan") {
      const form = await readFormData(req);
      const inputType = asInputType(form.get("input_type"));
      const text = stringifyFormValue(form.get("text"));
      const result = await runTextScan({ inputType, text }, env);
      sendJson(res, 200, result);
      return;
    }

    if (req.method === "POST" && url === "/api/v1/scam/filter") {
      const body = JSON.parse(
        (await readRawBody(req)).toString("utf8") || "{}",
      ) as {
        scam_type?: string | null;
        platform?: string | null;
        time_range?: number;
      };
      sendJson(res, 200, filterCases(body));
      return;
    }

    const caseMatch = url.match(/^\/api\/v1\/scam\/(\d+)$/);
    if (req.method === "GET" && caseMatch) {
      const found = CASE_LIBRARY.find((row) => row.id === Number(caseMatch[1]));
      if (!found) {
        sendJson(res, 404, { detail: "Scam case not found" });
        return;
      }
      sendJson(res, 200, found);
      return;
    }

    sendJson(res, 404, { detail: `No handler for ${url}` });
  } catch (error) {
    const status =
      error && typeof error === "object" && "status" in error
        ? Number((error as { status?: number }).status) || 500
        : 500;
    const detail =
      error instanceof Error ? error.message : "Internal server error";
    sendJson(res, status, { detail });
  }
}

function getRequestPath(req: IncomingMessage): string {
  const headerPath = firstHeader(
    req.headers["x-invoke-path"],
    req.headers["x-forwarded-uri"],
    req.headers["x-vercel-original-url"],
  );
  if (headerPath.includes("/v1/")) {
    return normalizeApiPath(headerPath);
  }

  const queryPath = readQueryPath(req);
  if (queryPath) {
    return normalizeApiPath(`/api/${queryPath}`);
  }

  return normalizeApiPath(req.url ?? "/");
}

function firstHeader(...values: Array<string | string[] | undefined>): string {
  for (const value of values) {
    const raw = Array.isArray(value) ? value[0] : value;
    if (typeof raw === "string" && raw.trim()) return raw;
  }
  return "";
}

function readQueryPath(req: IncomingMessage): string | null {
  const query = (req as IncomingMessage & { query?: Record<string, unknown> })
    .query;
  const value = query?.path;
  if (Array.isArray(value)) {
    const joined = value.filter((item) => typeof item === "string").join("/");
    return joined || null;
  }
  if (typeof value === "string" && value.trim() && !value.includes("[...]")) {
    return value.replace(/^\/+/, "");
  }

  const fromUrl = new URL(
    req.url ?? "/",
    "http://askvigil.local",
  ).searchParams.get("path");
  if (fromUrl && !fromUrl.includes("[...]")) {
    return fromUrl.replace(/^\/+/, "");
  }
  return null;
}

function normalizeApiPath(raw: string): string {
  const path = (raw.split("?")[0] || "/").replace(/\/+$/, "") || "/";
  if (path.includes("/v1/")) {
    return `/api${path.slice(path.indexOf("/v1/"))}`;
  }
  if (path.startsWith("/api/")) return path;
  if (path.startsWith("/v1/")) return `/api${path}`;
  if (path === "/api") return "/api";
  return path.startsWith("/") ? `/api${path}` : `/api/${path}`;
}

function filterCases(body: {
  scam_type?: string | null;
  platform?: string | null;
  time_range?: number;
}): CaseRow[] {
  const start = rangeStart(body.time_range ?? 0);
  return CASE_LIBRARY.filter((row) => {
    if (body.scam_type && row.scam_type !== body.scam_type) return false;
    if (body.platform && row.platform !== body.platform) return false;
    if (start && row.news_date < start) return false;
    return true;
  }).sort((a, b) => b.news_date.localeCompare(a.news_date));
}

function rangeStart(timeRange: number): string | null {
  if (timeRange === 0) return null;
  const days = timeRange === 1 ? 90 : timeRange === 2 ? 180 : 365;
  const start = new Date();
  start.setUTCDate(start.getUTCDate() - days);
  return start.toISOString().slice(0, 10);
}

async function readRawBody(req: IncomingMessage): Promise<Buffer> {
  if ("body" in req && typeof req.body === "string") {
    return Buffer.from(req.body);
  }
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

async function readFormData(req: IncomingMessage): Promise<FormData> {
  const body = await readRawBody(req);
  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (typeof value === "string") headers.set(key, value);
    else if (Array.isArray(value)) headers.set(key, value.join(", "));
  }
  const request = new Request("http://127.0.0.1/api/v1/detection/scan", {
    method: "POST",
    headers,
    body: new Uint8Array(body),
  });
  return request.formData();
}

function asInputType(value: FormDataEntryValue | null): ScanInputType {
  const raw = stringifyFormValue(value);
  if (raw === "image" || raw === "url" || raw === "qr" || raw === "text") {
    return raw;
  }
  return "text";
}

function stringifyFormValue(value: FormDataEntryValue | null): string {
  if (typeof value === "string") return value;
  return "";
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  if (res.writableEnded) return;
  res.statusCode = status;
  res.setHeader("content-type", "application/json; charset=utf-8");
  res.end(JSON.stringify(body));
}
