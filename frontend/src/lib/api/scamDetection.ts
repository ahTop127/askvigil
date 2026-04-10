import type { ScamDetectionInput, ScamDetectionResult } from "@lib/types";
import { generateMockDetectionResult } from "@lib/utils/mockData";
import { logger } from "@lib/utils/logger";

/**
 * Runs scam analysis on the given payload.
 * Currently returns mock data; swap implementation for HTTP client later.
 */
export async function detectScam(
  input: ScamDetectionInput
): Promise<ScamDetectionResult> {
  logger.info("detectScam called", { type: input.type });
  try {
    await new Promise((r) => setTimeout(r, 1800));
    const result = generateMockDetectionResult(input);
    logger.info("detectScam completed", { score: result.score });
    return result;
  } catch (e) {
    logger.error("detectScam failed", e instanceof Error ? e : undefined);
    throw e instanceof Error ? e : new Error("Detection failed");
  }
}
