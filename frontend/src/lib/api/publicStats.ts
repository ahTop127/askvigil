import { APP_CONFIG } from "@lib/config/app";
import { logger } from "@lib/utils/logger";

/** GET /api/v1/stats/public */
export type PublicStats = {
  users_protected: number;
  checks_daily: number;
  links_analysed: number;
  total_checks: number;
};

function isFiniteNumber(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

function parsePublicStats(raw: unknown): PublicStats | null {
  if (!raw || typeof raw !== "object") return null;
  const o = raw as Record<string, unknown>;
  const users_protected = o.users_protected;
  const checks_daily = o.checks_daily;
  const links_analysed = o.links_analysed;
  const total_checks = o.total_checks;
  if (
    !isFiniteNumber(users_protected) ||
    !isFiniteNumber(checks_daily) ||
    !isFiniteNumber(links_analysed) ||
    !isFiniteNumber(total_checks)
  ) {
    return null;
  }
  return {
    users_protected: Math.max(0, Math.round(users_protected)),
    checks_daily: Math.max(0, Math.round(checks_daily)),
    links_analysed: Math.max(0, Math.round(links_analysed)),
    total_checks: Math.max(0, Math.round(total_checks)),
  };
}

export async function fetchPublicStats(): Promise<PublicStats> {
  const endpoint = `${APP_CONFIG.api.baseUrl.replace(/\/$/, "")}/v1/stats/public`;
  const response = await fetch(endpoint, {
    method: "GET",
    headers: { Accept: "application/json" },
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Public stats request failed (${response.status})`);
  }
  const raw = (await response.json()) as unknown;
  const parsed = parsePublicStats(raw);
  if (!parsed) {
    logger.warn("fetchPublicStats: unexpected response shape", raw);
    throw new Error("Invalid public stats response");
  }
  return parsed;
}
