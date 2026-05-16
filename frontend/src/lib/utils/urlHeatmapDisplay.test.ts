import type { UrlTokenHeatmapEntry } from "@lib/types";
import { describe, expect, it } from "vitest";
import {
  computeUnifiedSegmentIntensity,
  heatmapScaleCap,
  heatmapSpanStyle,
  heatmapSpanStyleForUrlToken,
  parseUrlTokenHeatmap,
  standardizeUrlForHeatmap,
} from "./urlHeatmapDisplay";

describe("standardizeUrlForHeatmap", () => {
  it("lowercases, forces https, strips www", () => {
    expect(standardizeUrlForHeatmap("HTTPS://WWW.Example.COM/path")).toBe(
      "https://example.com/path",
    );
  });
});

describe("parseUrlTokenHeatmap", () => {
  it("parses API-shaped rows", () => {
    const rows = parseUrlTokenHeatmap([
      {
        token_text: "ab",
        start_char: 0,
        end_char: 2,
        xgb_predictive_delta: 0.05,
        semantic_similarity: -0.1,
        is_lexical_match: true,
      },
    ]);
    expect(rows).toHaveLength(1);
    expect(rows[0].token_text).toBe("ab");
    expect(rows[0].xgb_predictive_delta).toBe(0.05);
  });

  it("parses ui_signals when present", () => {
    const rows = parseUrlTokenHeatmap([
      {
        token_text: "a",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0,
        semantic_similarity: 0,
        is_lexical_match: false,
        ui_signals: {
          norm_xgb: 0.8,
          norm_semantic: 0.2,
          is_lexical: false,
        },
      },
    ]);
    expect(rows[0].ui_signals?.norm_xgb).toBe(0.8);
    expect(rows[0].ui_signals?.is_lexical).toBe(0);
  });
});

describe("computeUnifiedSegmentIntensity", () => {
  it("URL mode combines weights per spec", () => {
    const fusion = {
      effective_xgb_weight: 0.5,
      effective_db_weight: 0.5,
    };
    const signals = {
      norm_xgb: 1,
      norm_semantic: 1,
      is_lexical: 1,
    };
    expect(
      computeUnifiedSegmentIntensity(signals, fusion, "url"),
    ).toBeCloseTo(1, 5);
    expect(
      computeUnifiedSegmentIntensity(
        {
          norm_xgb: 0.5,
          norm_semantic: 0,
          is_lexical: 0,
        },
        fusion,
        "text",
      ),
    ).toBeCloseTo(0.25, 5);
  });
});

describe("heatmapSpanStyleForUrlToken", () => {
  it("uses fused ui path when signals + fusion provided", () => {
    const fusion = { effective_xgb_weight: 0.77, effective_db_weight: 0.23 };
    const style = heatmapSpanStyleForUrlToken(
      {
        token_text: "x",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0,
        semantic_similarity: 0,
        is_lexical_match: false,
        ui_signals: { norm_xgb: 0.9, norm_semantic: 0.8, is_lexical: 0 },
      },
      fusion,
      0.02,
      "url",
    );
    expect(style.backgroundColor).toMatch(/^rgb\(/);
  });

  it("low tier (bottom third of relative ramp) has no fill", () => {
    const fusion = { effective_xgb_weight: 0.5, effective_db_weight: 0.5 };
    const low = heatmapSpanStyleForUrlToken(
      {
        token_text: "a",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0,
        semantic_similarity: 0,
        is_lexical_match: false,
        ui_signals: { norm_xgb: 0, norm_semantic: 0, is_lexical: 0 },
      },
      fusion,
      0.02,
      "url",
      0.5,
    );
    expect(low.backgroundColor).toBe("transparent");

    const high = heatmapSpanStyleForUrlToken(
      {
        token_text: "b",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0,
        semantic_similarity: 0,
        is_lexical_match: false,
        ui_signals: { norm_xgb: 1, norm_semantic: 1, is_lexical: 1 },
      },
      fusion,
      0.02,
      "url",
      1,
    );
    expect(high.backgroundColor).toMatch(/^rgb\(/);
  });

  it("high tier only when relative ramp is near URL peak (>= 0.98)", () => {
    const fusion = { effective_xgb_weight: 1, effective_db_weight: 0 };
    const nearPeak = heatmapSpanStyleForUrlToken(
      {
        token_text: "a",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0,
        semantic_similarity: 0,
        is_lexical_match: false,
        ui_signals: { norm_xgb: 0.95, norm_semantic: 0, is_lexical: 0 },
      },
      fusion,
      0.02,
      "url",
      1,
    );
    const atPeak = heatmapSpanStyleForUrlToken(
      {
        token_text: "b",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0,
        semantic_similarity: 0,
        is_lexical_match: false,
        ui_signals: { norm_xgb: 1, norm_semantic: 0, is_lexical: 0 },
      },
      fusion,
      0.02,
      "url",
      1,
    );
    expect(nearPeak.backgroundColor).not.toBe(atPeak.backgroundColor);
    expect(atPeak.backgroundColor).toBe("rgb(220, 38, 38)");
  });

  it("falls back without ui_signals", () => {
    const style = heatmapSpanStyleForUrlToken(
      {
        token_text: "x",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0.05,
        semantic_similarity: 0,
        is_lexical_match: false,
      },
      undefined,
      heatmapScaleCap([
        {
          token_text: "x",
          start_char: 0,
          end_char: 1,
          xgb_predictive_delta: 0.05,
          semantic_similarity: 0,
          is_lexical_match: false,
        },
      ]),
      "url",
    );
    expect(style.backgroundColor).toMatch(/^rgb\(/);
  });
});

describe("heatmapScaleCap", () => {
  it("uses a cap below lone outlier max so other tokens gain range", () => {
    const entries = [
      mockEntry(0, 0),
      mockEntry(0, 0),
      mockEntry(0, 0),
      mockEntry(0.01, 0),
      mockEntry(0.052, 0),
    ];
    const cap = heatmapScaleCap(entries);
    expect(cap).toBeLessThanOrEqual(0.052);
    expect(cap).toBeGreaterThan(0.01);
  });

  it("returns a floor when all deltas are zero", () => {
    expect(heatmapScaleCap([mockEntry(0, 0), mockEntry(0, 0)])).toBe(0.02);
  });
});

function mockEntry(delta: number, sem: number): UrlTokenHeatmapEntry {
  return {
    token_text: "x",
    start_char: 0,
    end_char: 1,
    xgb_predictive_delta: delta,
    semantic_similarity: sem,
    is_lexical_match: false,
  };
}

describe("heatmapSpanStyle", () => {
  it("varies background continuously with delta", () => {
    const cap = 0.1;
    const a = heatmapSpanStyle(
      {
        token_text: "a",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0.02,
        semantic_similarity: 0,
        is_lexical_match: false,
      },
      cap,
    );
    const b = heatmapSpanStyle(
      {
        token_text: "b",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0.08,
        semantic_similarity: 0,
        is_lexical_match: false,
      },
      cap,
    );
    expect(a.backgroundColor).not.toBe(b.backgroundColor);
  });

  it("legacy: negative delta has no fill, positive shows color", () => {
    const cap = 0.1;
    const neg = heatmapSpanStyle(
      {
        token_text: "n",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: -0.08,
        semantic_similarity: 0,
        is_lexical_match: false,
      },
      cap,
    );
    const pos = heatmapSpanStyle(
      {
        token_text: "p",
        start_char: 0,
        end_char: 1,
        xgb_predictive_delta: 0.08,
        semantic_similarity: 0,
        is_lexical_match: false,
      },
      cap,
    );
    expect(neg.backgroundColor).toBe("transparent");
    expect(pos.backgroundColor).toMatch(/^rgb\(/);
  });
});
