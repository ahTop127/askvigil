import {
  classifyWithDeepSeek,
  readDeepSeekEnv,
  type DeepSeekScanResult,
} from "./deepseekClient.js";

export type ScanInputType = "text" | "image" | "url" | "qr";

export type ScanRequest = {
  inputType: ScanInputType;
  text: string;
};

export function buildScanResponse(
  input: ScanRequest,
  result: DeepSeekScanResult,
): Record<string, unknown> {
  const percent = Math.round(result.risk_score * 100);
  const indicators = result.reasons.map((item) => ({
    category: result.scam_type,
    matched_terms: [item.text],
    reason: item.reason,
  }));

  const textAnalysis = {
    risk_score: result.risk_score,
    risk_score_percent: percent,
    scam_type: { predicted_type: result.scam_type },
    "input text": input.text,
    explainability: { matched_indicators: indicators },
    immediate_guidance: result.guidance,
  };

  const payload: Record<string, unknown> = {
    modalities: {},
    unified_text_analysis: {
      overall_risk_score: result.risk_score,
      text_analysis: textAnalysis,
      url_analysis: [] as unknown[],
    },
    metadata: { engine: "deepseek-flash" },
  };

  if (input.inputType === "url") {
    const unified = payload.unified_text_analysis as Record<string, unknown>;
    unified.url_analysis = [
      {
        risk_score: result.risk_score,
        decision: result.risk_score >= 0.7 ? "flagged" : "clear",
        resolved_url: input.text.trim(),
        resolved_successfully: true,
      },
    ];
  }

  return payload;
}

export async function runTextScan(
  input: ScanRequest,
  env: Record<string, string | undefined>,
): Promise<Record<string, unknown>> {
  if (input.inputType === "image" || input.inputType === "qr") {
    const error = new Error(
      "Image and QR scan are not connected yet. Paste the text or URL instead.",
    );
    (error as Error & { status: number }).status = 400;
    throw error;
  }
  const text = input.text.trim();
  if (!text) {
    const error = new Error("Must provide text or a file.");
    (error as Error & { status: number }).status = 400;
    throw error;
  }
  const classified = await classifyWithDeepSeek(text, readDeepSeekEnv(env));
  return buildScanResponse(input, classified);
}
