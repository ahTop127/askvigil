import { beforeEach, describe, expect, it, vi } from "vitest";
import { detectScam } from "./scamDetection";

describe("detectScam qr mapping", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("maps modalities.qr.url_report_analysis to qrUrlReportAnalysis", async () => {
    const payload = {
      modalities: {
        qr: {
          decoded_items: [
            {
              decoded_content: "https://www.bilibili.com",
              urls: ["https://www.bilibili.com"],
            },
          ],
          qr_urls: ["https://www.bilibili.com"],
          url_analysis: [
            {
              risk_score: 1.0,
              resolved_url: "https://www.bilibili.com",
              resolved_successfully: true,
              decision: "flagged",
            },
          ],
          url_report_analysis: [
            {
              "Website Address": "https://www.bilibili.com",
              "Detections Counts": "0/92",
              "Domain Registration": "2004-10-21",
              Status: "Safe",
              "Last Analysis": "2026-05-02 02:01",
            },
          ],
        },
      },
      unified_text_analysis: null,
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const result = await detectScam({
      type: "qr",
      content: new File(["dummy"], "qr.png", { type: "image/png" }),
    });

    expect(result.qrDecodedContent).toBe("https://www.bilibili.com");
    expect(result.qrUrlReportAnalysis).toEqual(payload.modalities.qr.url_report_analysis);
  });
});
