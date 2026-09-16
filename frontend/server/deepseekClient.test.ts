import { describe, expect, it } from "vitest";
import {
  extractAssistantText,
  normalizeScanResult,
  parseJsonObject,
} from "./deepseekClient";
import { buildScanResponse } from "./scanPipeline";

describe("deepseek JSON mapping", () => {
  it("reads text blocks and ignores thinking", () => {
    const text = extractAssistantText({
      content: [
        { type: "thinking", thinking: "secret" },
        { type: "text", text: '{"risk_score":0.9}' },
      ],
    });
    expect(text).toContain("risk_score");
  });

  it("parses fenced JSON and normalizes scam types", () => {
    const parsed = parseJsonObject(
      '```json\n{"risk_score": 82, "scam_type": "OTP Scam", "reasons": [{"text": "TAC", "reason": "asks for a code"}]}\n```',
    );
    const result = normalizeScanResult(parsed);
    expect(result.risk_score).toBe(0.82);
    expect(result.scam_type).toBe("otp-scam");
    expect(result.reasons[0]?.text).toBe("TAC");
  });

  it("builds the frontend scan contract", () => {
    const payload = buildScanResponse(
      { inputType: "text", text: "Send OTP now" },
      {
        risk_score: 0.91,
        scam_type: "otp-scam",
        reasons: [{ text: "OTP", reason: "Requests a one-time password." }],
        guidance: {
          title: "Do not share the code",
          summary: "This looks like an OTP scam.",
          dont_do: ["Do not send the code"],
          safer_action: ["Call the bank using the number on your card"],
        },
      },
    );
    const unified = payload.unified_text_analysis as {
      overall_risk_score: number;
      text_analysis: { scam_type: { predicted_type: string } };
    };
    expect(unified.overall_risk_score).toBe(0.91);
    expect(unified.text_analysis.scam_type.predicted_type).toBe("otp-scam");
  });
});
