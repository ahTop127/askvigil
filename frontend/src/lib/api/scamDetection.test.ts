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
    expect(result.qrUrlReportAnalysis).toEqual(
      payload.modalities.qr.url_report_analysis,
    );
  });

  it("maps meta_labels and meta_vector from unified url_analysis for URL detection", async () => {
    const meta_labels = [
      "Path Ratio",
      "TLD Tier",
      "Entropy",
      "Dot Count",
      "Digit Ratio",
      "Special Chars",
      "Subdomain Flag",
      "Path Depth",
    ];
    const meta_vector = [
      0.16, 0, 0.5655639171600342, 0.4, 0.23199999332427979, 0.7, 0,
      0.6000000238418579,
    ];
    const payload = {
      unified_text_analysis: {
        overall_risk_score: 0.3632,
        text_analysis: null,
        url_analysis: [
          {
            risk_score: 0.3632,
            meta_labels,
            meta_vector,
          },
        ],
      },
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const result = await detectScam({
      type: "text",
      content: "https://example.com/x",
    });

    expect(result.submittedUrl).toBe("https://example.com/x");
    expect(result.urlMetaFeatures?.map((f) => f.label)).toEqual([
      "Special Chars",
      "Path Depth",
      "Entropy",
    ]);
  });

  it("sets dualTextUrlDetection and urlDetectionSummary when unified scan has both text_analysis and url_analysis (text input)", async () => {
    const meta_labels = ["Path Ratio", "TLD Tier"];
    const meta_vector = [0.2, 0.9];
    const payload = {
      unified_text_analysis: {
        overall_risk_score: 0.55,
        text_analysis: {
          risk_score: 0.4,
          scam_type: { predicted_type: "phishing" },
          immediate_guidance: { summary: "Mixed content looks risky." },
        },
        url_analysis: [
          {
            risk_score: 0.85,
            resolved_url: "https://resolved.example/phish",
            meta_labels,
            meta_vector,
          },
        ],
      },
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const result = await detectScam({
      type: "text",
      content: "Please pay at https://short.ly/x — urgent",
    });

    expect(result.dualTextUrlDetection).toBe(true);
    expect(result.urlDetectionSummary?.displayUrl).toBe(
      "https://resolved.example/phish",
    );
    expect(result.urlDetectionSummary?.urlMetaFeatures?.length).toBeGreaterThan(
      0,
    );
    expect(result.urlMetaFeatures).toBeUndefined();
  });

  it("does not enable URL branch or submittedUrl when url_analysis is missing or empty", async () => {
    const payload = {
      unified_text_analysis: {
        overall_risk_score: 0.41,
        text_analysis: {
          risk_score: 0.41,
          scam_type: { predicted_type: "job_scam" },
        },
        url_analysis: [],
      },
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const result = await detectScam({
      type: "text",
      content: "https://example.com/only-line",
    });

    expect(result.submittedUrl).toBeUndefined();
    expect(result.urlMetaFeatures).toBeUndefined();
    expect(result.dualTextUrlDetection).toBeFalsy();
  });

  it("URL tab sets submittedUrl only when backend returned analyzable url_analysis", async () => {
    const payload = {
      unified_text_analysis: {
        overall_risk_score: 0.7,
        text_analysis: null,
        url_analysis: [
          {
            risk_score: 0.72,
            resolved_url: "https://phish.example/login",
            meta_labels: ["Entropy"],
            meta_vector: [0.5],
          },
        ],
      },
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const result = await detectScam({
      type: "text",
      content: "https://phish.example/login",
      submissionChannel: "url_tab",
    });

    expect(result.submittedUrl).toBe("https://phish.example/login");
    expect(result.dualTextUrlDetection).toBeFalsy();
    expect(result.urlMetaFeatures?.length).toBeGreaterThan(0);
  });

  it("URL tab does not set submittedUrl when url_analysis is absent", async () => {
    const payload = {
      unified_text_analysis: {
        overall_risk_score: 0.2,
        text_analysis: { risk_score: 0.2 },
        url_analysis: [],
      },
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const result = await detectScam({
      type: "text",
      content: "https://safe.example/",
      submissionChannel: "url_tab",
    });

    expect(result.submittedUrl).toBeUndefined();
  });

  it("does not enable dual text/url when submitted from URL strip (url_tab)", async () => {
    const payload = {
      unified_text_analysis: {
        overall_risk_score: 0.55,
        text_analysis: {
          risk_score: 0.3,
          scam_type: { predicted_type: "job_scam" },
        },
        url_analysis: [
          {
            risk_score: 0.8,
            resolved_url: "https://x.example/hook",
            meta_labels: ["Entropy"],
            meta_vector: [0.5],
          },
        ],
      },
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    const result = await detectScam({
      type: "text",
      content: "https://x.example/hook",
      submissionChannel: "url_tab",
    });

    expect(result.dualTextUrlDetection).toBeFalsy();
    expect(result.urlDetectionSummary).toBeUndefined();
  });
});
