import type { LearningContent } from "@lib/types";
import { generateMockLearningContent } from "@lib/utils/mockData";
import { logger } from "@lib/utils/logger";

export async function getScamKnowledge(id: string): Promise<LearningContent> {
  logger.info("getScamKnowledge", { id });
  await new Promise((r) => setTimeout(r, 200));
  return generateMockLearningContent(id);
}

export async function getAllLearningContent(): Promise<LearningContent[]> {
  const ids = ["job-scam", "phishing", "otp-scam", "qr-scam", "suspicious-link"];
  return Promise.all(ids.map((id) => getScamKnowledge(id)));
}
