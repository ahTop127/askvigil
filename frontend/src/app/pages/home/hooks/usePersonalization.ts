import { useCallback, useState } from "react";
import { APP_CONFIG } from "@lib/config/app";
import { SUCCESS_MESSAGES } from "@lib/constants/text";
import {
  getUserPreferences,
  hasUserPreferences,
  saveUserPreferences,
} from "@lib/storage/userPreferences";
import type { UserPreferences } from "@lib/types";
import { logger } from "@lib/utils/logger";

function readDismissed(): boolean {
  try {
    return (
      localStorage.getItem(APP_CONFIG.storageKeys.preferencesDismissed) ===
      "true"
    );
  } catch {
    return false;
  }
}

export interface UsePersonalizationReturn {
  showCard: boolean;
  showDialog: boolean;
  selectedTopics: string[];
  selectedGoal: string;
  wantsAlerts: string;
  toggleTopic: (topic: string) => void;
  setGoal: (goal: string) => void;
  setWantsAlerts: (value: string) => void;
  savePreferences: () => Promise<void>;
  dismissCard: () => void;
  openDialog: () => void;
  closeDialog: () => void;
}

const TOPICS = [
  "phishing",
  "job-scams",
  "investment",
  "romance",
] as const;

export function usePersonalization(): UsePersonalizationReturn {
  const [showCard, setShowCard] = useState(
    () => !hasUserPreferences() && !readDismissed()
  );
  const [showDialog, setShowDialog] = useState(false);
  const [selectedTopics, setSelectedTopics] = useState<string[]>(() => {
    const p = getUserPreferences();
    return p?.topics ?? [];
  });
  const [selectedGoal, setSelectedGoal] = useState(
    () => getUserPreferences()?.goal ?? ""
  );
  const [wantsAlerts, setWantsAlertsState] = useState(() => {
    const p = getUserPreferences();
    if (!p) return "";
    return p.wantsAlerts ? "yes" : "no";
  });

  const toggleTopic = useCallback((topic: string) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  }, []);

  const setGoal = useCallback((goal: string) => {
    setSelectedGoal(goal);
  }, []);

  const setWantsAlerts = useCallback((value: string) => {
    setWantsAlertsState(value);
  }, []);

  const savePreferences = useCallback(async () => {
    const prefs: UserPreferences = {
      topics: selectedTopics,
      goal: selectedGoal,
      wantsAlerts: wantsAlerts === "yes",
      savedAt: new Date().toISOString(),
    };
    saveUserPreferences(prefs);
    logger.info(SUCCESS_MESSAGES.preferencesSaved, prefs);

    if (wantsAlerts === "yes") {
      try {
        const permission = await Notification.requestPermission();
        if (permission === "granted") {
          new Notification("AskVigil Alerts Enabled", {
            body: "You'll receive alerts about scam updates matching your interests.",
            icon: "/favicon.ico",
          });
        }
      } catch {
        logger.warn("Notification permission not available");
      }
    }

    setShowDialog(false);
    setShowCard(false);
  }, [selectedTopics, selectedGoal, wantsAlerts]);

  const dismissCard = useCallback(() => {
    setShowCard(false);
    try {
      localStorage.setItem(
        APP_CONFIG.storageKeys.preferencesDismissed,
        "true"
      );
    } catch {
      /* ignore */
    }
  }, []);

  const openDialog = useCallback(() => setShowDialog(true), []);
  const closeDialog = useCallback(() => setShowDialog(false), []);

  return {
    showCard,
    showDialog,
    selectedTopics,
    selectedGoal,
    wantsAlerts,
    toggleTopic,
    setGoal,
    setWantsAlerts,
    savePreferences,
    dismissCard,
    openDialog,
    closeDialog,
  };
}

export const PERSONALIZATION_TOPICS = TOPICS;
