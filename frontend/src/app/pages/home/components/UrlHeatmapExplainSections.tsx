import type { ReactNode } from "react";
import type { UrlHeatmapFusionWeights, UrlTokenHeatmapEntry } from "@lib/types";
import {
  heatmapScaleCap,
  heatmapSpanStyleForUrlToken,
  maxFusedScoreInBatch,
  type HeatmapBranchMode,
} from "@lib/utils/urlHeatmapDisplay";

function TokenHeatmapHighlightedText({
  base,
  tokens,
  fusion,
  mode,
}: {
  base: string;
  tokens: UrlTokenHeatmapEntry[];
  fusion?: UrlHeatmapFusionWeights | null;
  mode: HeatmapBranchMode;
}) {
  if (!base || tokens.length === 0) return null;

  const sorted = [...tokens].sort((a, b) => a.start_char - b.start_char);
  const scaleCap = heatmapScaleCap(sorted);
  const batchMaxFused = fusion ? maxFusedScoreInBatch(sorted, fusion, mode) : 0;

  const parts: ReactNode[] = [];
  let cursor = 0;
  const flushGap = (until: number) => {
    if (until > cursor) {
      parts.push(
        <span key={`ng-${cursor}`} className="text-slate-700">
          {base.slice(cursor, until)}
        </span>,
      );
      cursor = until;
    }
  };

  for (const e of sorted) {
    if (e.start_char > cursor) flushGap(e.start_char);
    const slice = base.slice(e.start_char, e.end_char);
    const style = heatmapSpanStyleForUrlToken(
      e,
      fusion ?? undefined,
      scaleCap,
      mode,
      batchMaxFused,
    );
    parts.push(
      <span key={`${e.start_char}:${e.end_char}`} style={style}>
        {slice}
      </span>,
    );
    cursor = e.end_char;
  }
  flushGap(base.length);

  const textClass =
    mode === "url"
      ? "font-mono text-[13px] leading-normal break-all md:text-sm"
      : "text-[13px] leading-relaxed whitespace-pre-wrap break-words md:text-sm";

  return <p className={textClass}>{parts}</p>;
}

const COPY = {
  url: {
    title: "Which parts of the link mattered most",
    bodyWithFusion:
      "Colored sections are the pieces of the address that had the strongest pull on this result. Most of the link may stay plain—only the standouts are highlighted. Lighter amber means a smaller influence; deeper amber or red means a stronger one.",
    bodyLegacy:
      "Colored sections show which pieces of the address looked most like known risky links or moved the score the most. Lighter shading means a smaller influence; deeper color means a stronger one.",
  },
  text: {
    title: "Which parts of the message mattered most",
    bodyWithFusion:
      "Colored sections are the phrases that had the strongest pull on this result. Most of the message may stay plain—only the standouts are highlighted. Lighter amber means a smaller influence; deeper amber or red means a stronger one.",
    bodyLegacy:
      "Colored sections show which phrases looked most like known scam messages or moved the score the most. Lighter shading means a smaller influence; deeper color means a stronger one.",
  },
} as const;

export function UrlHeatmapExplainSections({
  baseUrl,
  tokens,
  fusion,
  embedded = false,
  mode = "url",
}: {
  baseUrl: string;
  tokens: UrlTokenHeatmapEntry[];
  fusion?: UrlHeatmapFusionWeights | null;
  embedded?: boolean;
  mode?: HeatmapBranchMode;
}) {
  const copy = COPY[mode];

  return (
    <div className={embedded ? "mt-3" : "mt-4 border-t border-slate-200 pt-4"}>
      <div>
        <h4 className="mb-1.5 text-base font-semibold text-slate-900">
          {copy.title}
        </h4>
        <p className="mb-2 text-xs text-slate-500">
          {fusion ? copy.bodyWithFusion : copy.bodyLegacy}
        </p>
        <div className="rounded-lg border border-slate-200 bg-slate-50/80 px-3 py-2.5">
          <TokenHeatmapHighlightedText
            base={baseUrl}
            tokens={tokens}
            fusion={fusion}
            mode={mode}
          />
        </div>
      </div>
    </div>
  );
}
