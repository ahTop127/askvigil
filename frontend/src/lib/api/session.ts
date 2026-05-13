import { APP_CONFIG } from "@lib/config/app";
import { logger } from "@lib/utils/logger";

const STORAGE_KEY = "askvigil_session_id";

interface SessionInitResponse {
  status?: string;
  message?: string;
  session_id?: string;
}

function readFromStorage(): string | null {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v && v.trim() ? v.trim() : null;
  } catch {
    return null;
  }
}

function writeToStorage(id: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, id);
  } catch {
    /** Quota or privacy-mode failure: ignore, in-memory session will still work for the tab. */
  }
}

export function getStoredSessionId(): string | null {
  return readFromStorage();
}

/** In-flight de-dupe so multiple boot-time callers reuse one network request. */
let inflight: Promise<string | null> | null = null;

/** GET /v1/session/init — creates or refreshes the user's session cookie + id. */
export async function initSession(): Promise<string | null> {
  if (inflight) return inflight;

  inflight = (async () => {
    try {
      const endpoint = `${APP_CONFIG.api.baseUrl.replace(/\/$/, "")}/v1/session/init`;
      const response = await fetch(endpoint, {
        method: "GET",
        headers: { Accept: "application/json" },
        credentials: "include",
      });

      if (!response.ok) {
        logger.warn("Session init failed", { status: response.status });
        return readFromStorage();
      }

      const data = (await response.json()) as SessionInitResponse;
      const id =
        typeof data.session_id === "string" ? data.session_id.trim() : "";
      if (id) {
        writeToStorage(id);
        logger.info("Session initialized");
        return id;
      }
      return readFromStorage();
    } catch (e) {
      logger.error("Session init error", e instanceof Error ? e : undefined);
      return readFromStorage();
    } finally {
      /** Clear so a forced re-init (e.g. after logout) can run a fresh request. */
      inflight = null;
    }
  })();

  return inflight;
}

/** Returns the cached session id, otherwise triggers a one-time init. */
export async function ensureSessionId(): Promise<string | null> {
  const cached = readFromStorage();
  if (cached) return cached;
  return initSession();
}
