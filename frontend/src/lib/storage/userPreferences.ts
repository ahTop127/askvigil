import { APP_CONFIG } from "@lib/config/app";
import type { UserPreferences } from "@lib/types";

const KEY = APP_CONFIG.storageKeys.userPreferences;

function storageAvailable(): boolean {
  try {
    const k = "__askvigil_test__";
    localStorage.setItem(k, "1");
    localStorage.removeItem(k);
    return true;
  } catch {
    return false;
  }
}

export function getUserPreferences(): UserPreferences | null {
  if (!storageAvailable()) return null;
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as UserPreferences;
    if (!parsed || typeof parsed !== "object") return null;
    return parsed;
  } catch {
    return null;
  }
}

export function saveUserPreferences(preferences: UserPreferences): void {
  if (!storageAvailable()) return;
  try {
    localStorage.setItem(KEY, JSON.stringify(preferences));
  } catch {
    /* ignore quota / private mode */
  }
}

export function clearUserPreferences(): void {
  if (!storageAvailable()) return;
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}

export function hasUserPreferences(): boolean {
  return getUserPreferences() !== null;
}
