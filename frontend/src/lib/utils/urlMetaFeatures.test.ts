import { describe, expect, it } from "vitest";
import { buildUrlMetaHighlights } from "./urlMetaFeatures";

describe("buildUrlMetaHighlights", () => {
  it("returns empty arrays for invalid input", () => {
    expect(buildUrlMetaHighlights(undefined, undefined)).toEqual([]);
    expect(buildUrlMetaHighlights([], [])).toEqual([]);
    expect(buildUrlMetaHighlights(["a"], null)).toEqual([]);
  });

  it("excludes zero scores and scores below per-label thresholds", () => {
    const labels = [
      "Path Ratio",
      "TLD Tier",
      "Entropy",
      "Dot Count",
      "Digit Ratio",
      "Special Chars",
      "Subdomain Flag",
      "Path Depth",
    ];
    const vector = [
      0.16, 0, 0.5655639171600342, 0.4, 0.23199999332427979, 0.7, 0,
      0.6000000238418579,
    ];
    const out = buildUrlMetaHighlights(labels, vector);
    expect(out.map((x) => x.label)).toEqual([
      "Special Chars",
      "Path Depth",
      "Entropy",
    ]);
    expect(out[0]?.severity).toBe("high");
    expect(out[1]?.severity).toBe("medium");
    expect(out[2]?.severity).toBe("medium");
  });

  it("caps at three items", () => {
    const labels = ["A", "B", "C", "D"];
    const vector = [0.9, 0.85, 0.8, 0.75];
    const out = buildUrlMetaHighlights(labels, vector, { maxItems: 3 });
    expect(out).toHaveLength(3);
    expect(out[0]?.label).toBe("A");
    expect(out[1]?.label).toBe("B");
    expect(out[2]?.label).toBe("C");
  });
});
