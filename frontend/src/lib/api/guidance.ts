import type { GuidanceContent } from "@lib/types";
import { generateMockGuidanceContent } from "@lib/utils/mockData";
import { logger } from "@lib/utils/logger";

export async function getScamTypeDetails(id: string): Promise<GuidanceContent> {
  logger.info("getScamTypeDetails", { id });
  await new Promise((r) => setTimeout(r, 200));
  return generateMockGuidanceContent(id);
}

export async function getEmergencyContacts() {
  const g = await getScamTypeDetails("generic");
  return g.emergencyContacts;
}
