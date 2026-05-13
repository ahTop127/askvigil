import { memo, useEffect, useState } from "react";
import { motion } from "motion/react";
import { MoreHorizontal } from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  fetchDetectionTrend,
  fetchInputTypeDistribution,
  fetchRiskLevelDistribution,
  fetchScanTypeRanking,
  type TrendPoint,
  type TrendDays,
  type TrendRiskLevel,
  type TrendInputType,
  type InputTypeDistribution,
  type RiskLevelDistribution,
  type ScanTypeRankingResponse,
} from "@lib/api/detectionTrend";

/** AskVigil theme (see frontend/src/styles/theme.css) */
const BRAND = {
  primary: "#5178eb",
  secondary: "#477de8",
  ink: "#213034",
  muted: "#64748b",
  border: "#e2e8f0",
  shell: "#e8eef5",
  success: "#0d9f6e",
  warn: "#ea8c3c",
  danger: "#e85d5d",
  slate: "#94a3b8",
} as const;

type LoadStatus = "loading" | "ok" | "error";

function shortDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-MY", {
    month: "short",
    day: "numeric",
  });
}

function pct(n: number, total: number) {
  return total ? `${Math.round((n / total) * 100)}%` : "—";
}

function fmtScam(raw: string) {
  return raw
    .replace(/^ScamTypeEnum\./i, "")
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

const LIGHT_TOOLTIP = {
  contentStyle: {
    background: "#ffffff",
    border: `1px solid ${BRAND.border}`,
    borderRadius: 12,
    fontSize: 12,
    padding: "8px 12px",
    boxShadow: "0 8px 24px rgba(33,48,52,0.08)",
  },
  itemStyle: { color: BRAND.ink },
  labelStyle: { color: BRAND.muted, fontSize: 11 },
};

function Spinner() {
  return (
    <div className="flex h-[220px] items-center justify-center">
      <div
        className="h-8 w-8 animate-spin rounded-full border-2 border-[#5178eb]/25 border-t-[#5178eb]"
        aria-hidden
      />
    </div>
  );
}

function Err() {
  return (
    <div className="flex h-[220px] items-center justify-center text-sm text-gray-500">
      Unable to load
    </div>
  );
}

/** Light outer shell + white inner (reference layout) */
function ChartShell({
  title,
  subtitle,
  children,
  delay = 0,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.45, delay, ease: "easeOut" }}
      className="rounded-2xl p-1.5 shadow-sm sm:p-2"
      style={{ backgroundColor: BRAND.shell }}
    >
      <div className="flex h-full min-h-[280px] flex-col overflow-hidden rounded-xl border border-gray-100/90 bg-white shadow-[0_1px_3px_rgba(33,48,52,0.06)]">
        <div className="flex items-start justify-between gap-2 border-b border-gray-100 px-4 py-3">
          <div className="min-w-0">
            <h3 className="truncate text-sm font-semibold text-[#213034] md:text-base">
              {title}
            </h3>
            {subtitle ? (
              <p className="mt-0.5 text-xs text-gray-500">{subtitle}</p>
            ) : null}
          </div>
          <button
            type="button"
            className="shrink-0 rounded-md p-1 text-gray-400 transition-colors hover:bg-gray-50 hover:text-gray-600"
            aria-label="More"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </div>
        <div className="min-h-0 flex-1 p-2 md:p-3">{children}</div>
      </div>
    </motion.div>
  );
}

/* ── Trend: multi-series area, brand-forward palette ── */
const TREND_SERIES = [
  {
    key: "total_count",
    label: "Total",
    color: BRAND.primary,
    grad: "av-total",
  },
  { key: "text", label: "Text", color: BRAND.success, grad: "av-text" },
  { key: "url", label: "URL", color: BRAND.warn, grad: "av-url" },
  { key: "image", label: "Image", color: BRAND.secondary, grad: "av-image" },
  { key: "qr", label: "QR", color: "#8b5cf6", grad: "av-qr" },
] as const;
const TREND_RISKS: TrendRiskLevel[] = ["all", "low", "medium", "high"];
const TREND_INPUTS: TrendInputType[] = ["text", "image", "url", "qr"];

function TrendBlock({
  points,
  status,
  days,
  onDays,
  risk,
  onRisk,
  inputTypes,
  onToggleInputType,
}: {
  points: TrendPoint[];
  status: LoadStatus;
  days: TrendDays;
  onDays: (d: TrendDays) => void;
  risk: TrendRiskLevel;
  onRisk: (r: TrendRiskLevel) => void;
  inputTypes: TrendInputType[];
  onToggleInputType: (t: TrendInputType) => void;
}) {
  return (
    <ChartShell
      title="Detection trend"
      subtitle="Checks over the selected window"
    >
      <div className="mb-2 flex items-start justify-between gap-3">
        <div className="flex min-w-[68px] flex-col gap-1.5">
          {TREND_INPUTS.map((t) => {
            const active = inputTypes.includes(t);
            return (
              <button
                key={t}
                type="button"
                onClick={() => onToggleInputType(t)}
                className={`rounded-full border px-2 py-0.5 text-left text-[10px] font-semibold uppercase transition-colors ${
                  active
                    ? "border-[#5178eb]/30 bg-[#5178eb]/10 text-[#2f4fb5]"
                    : "border-gray-200 bg-white text-gray-500 hover:text-[#213034]"
                }`}
              >
                {t}
              </button>
            );
          })}
        </div>
        <div className="space-y-2">
          <div className="flex flex-wrap justify-end gap-2">
            <div className="inline-flex overflow-hidden rounded-full border border-gray-200 bg-gray-50/80 p-0.5 text-[10px] font-semibold">
              {([7, 30] as TrendDays[]).map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => onDays(d)}
                  className={`rounded-full px-2 py-0.5 transition-colors ${
                    days === d
                      ? "bg-[#5178eb] text-white shadow-sm"
                      : "text-gray-600 hover:bg-white hover:text-[#213034]"
                  }`}
                >
                  {d} days
                </button>
              ))}
            </div>
            <div className="inline-flex overflow-hidden rounded-full border border-gray-200 bg-gray-50/80 p-0.5 text-[10px] font-semibold">
              {TREND_RISKS.map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => onRisk(r)}
                  className={`rounded-full px-2 py-0.5 capitalize transition-colors ${
                    risk === r
                      ? "bg-[#5178eb] text-white shadow-sm"
                      : "text-gray-600 hover:bg-white hover:text-[#213034]"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="h-[220px] w-full">
        {status === "loading" ? (
          <Spinner />
        ) : status === "error" ? (
          <Err />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={points}
              margin={{ top: 8, right: 8, left: -12, bottom: 0 }}
            >
              <defs>
                {TREND_SERIES.map((s) => (
                  <linearGradient
                    key={s.grad}
                    id={s.grad}
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor={s.color} stopOpacity={0.22} />
                    <stop
                      offset="100%"
                      stopColor={s.color}
                      stopOpacity={0.02}
                    />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#eef2f7"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                tick={{ fill: BRAND.muted, fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: BRAND.muted, fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
                width={36}
              />
              <Tooltip
                {...LIGHT_TOOLTIP}
                cursor={{ stroke: BRAND.border, strokeWidth: 1 }}
              />
              {TREND_SERIES.map((s) => (
                <Area
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.label}
                  stroke={s.color}
                  strokeWidth={2}
                  fill={`url(#${s.grad})`}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 0, fill: s.color }}
                  animationDuration={750}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </ChartShell>
  );
}

/* ── Input type donut ── */
const INPUT_C: Record<string, string> = {
  Text: BRAND.primary,
  Image: BRAND.secondary,
  URL: BRAND.warn,
  QR: "#8b5cf6",
};

function InputBlock({
  data,
  status,
}: {
  data: InputTypeDistribution | null;
  status: LoadStatus;
}) {
  const slices = data
    ? [
        { name: "Text", value: data.text_count },
        { name: "Image", value: data.image_count },
        { name: "URL", value: data.url_count },
        { name: "QR", value: data.qr_count },
      ].filter((s) => s.value > 0)
    : [];

  return (
    <ChartShell
      title="Input type mix"
      subtitle="How people submit checks"
      delay={0.05}
    >
      <div className="flex h-[220px] items-center gap-2 md:gap-4">
        {status === "loading" ? (
          <Spinner />
        ) : status === "error" ? (
          <Err />
        ) : (
          <>
            <ResponsiveContainer width="52%" height="100%">
              <PieChart>
                <Pie
                  data={slices}
                  cx="50%"
                  cy="50%"
                  innerRadius="42%"
                  outerRadius="72%"
                  paddingAngle={2}
                  dataKey="value"
                  animationDuration={700}
                >
                  {slices.map((s) => (
                    <Cell
                      key={s.name}
                      fill={INPUT_C[s.name]}
                      stroke="#fff"
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
                <Tooltip {...LIGHT_TOOLTIP} />
              </PieChart>
            </ResponsiveContainer>
            <ul className="flex min-w-0 flex-1 flex-col gap-2 text-xs md:text-sm">
              {slices.map((s) => (
                <li key={s.name} className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ background: INPUT_C[s.name] }}
                  />
                  <span className="truncate text-gray-600">{s.name}</span>
                  <span className="ml-auto shrink-0 font-semibold tabular-nums text-[#213034]">
                    {pct(s.value, data!.total)}
                  </span>
                </li>
              ))}
              <li className="mt-1 border-t border-gray-100 pt-2 text-gray-500">
                Total{" "}
                <span className="font-semibold text-[#213034]">
                  {data?.total}
                </span>
              </li>
            </ul>
          </>
        )}
      </div>
    </ChartShell>
  );
}

/* ── Risk donut ── */
const RISK_C: Record<string, string> = {
  High: BRAND.danger,
  Medium: BRAND.warn,
  Low: BRAND.success,
  Unknown: BRAND.slate,
};

function RiskBlock({
  data,
  status,
}: {
  data: RiskLevelDistribution | null;
  status: LoadStatus;
}) {
  const slices = data
    ? [
        { name: "High", value: data.high_count },
        { name: "Medium", value: data.medium_count },
        { name: "Low", value: data.low_count },
        { name: "Unknown", value: data.unknown_count },
      ].filter((s) => s.value > 0)
    : [];

  return (
    <ChartShell
      title="Risk distribution"
      subtitle="Outcome severity split"
      delay={0.1}
    >
      <div className="flex h-[220px] items-center gap-2 md:gap-4">
        {status === "loading" ? (
          <Spinner />
        ) : status === "error" ? (
          <Err />
        ) : (
          <>
            <ResponsiveContainer width="52%" height="100%">
              <PieChart>
                <Pie
                  data={slices}
                  cx="50%"
                  cy="50%"
                  innerRadius="42%"
                  outerRadius="72%"
                  paddingAngle={2}
                  dataKey="value"
                  animationDuration={700}
                >
                  {slices.map((s) => (
                    <Cell
                      key={s.name}
                      fill={RISK_C[s.name]}
                      stroke="#fff"
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
                <Tooltip {...LIGHT_TOOLTIP} />
              </PieChart>
            </ResponsiveContainer>
            <ul className="flex min-w-0 flex-1 flex-col gap-2 text-xs md:text-sm">
              {slices.map((s) => (
                <li key={s.name} className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ background: RISK_C[s.name] }}
                  />
                  <span className="truncate text-gray-600">{s.name}</span>
                  <span className="ml-auto shrink-0 font-semibold tabular-nums text-[#213034]">
                    {pct(s.value, data!.total)}
                  </span>
                </li>
              ))}
              <li className="mt-1 border-t border-gray-100 pt-2 text-gray-500">
                Total{" "}
                <span className="font-semibold text-[#213034]">
                  {data?.total}
                </span>
              </li>
            </ul>
          </>
        )}
      </div>
    </ChartShell>
  );
}

/* ── Scam ranking bars ── */
function ScamBlock({
  data,
  status,
}: {
  data: ScanTypeRankingResponse | null;
  status: LoadStatus;
}) {
  const rows = (data?.items ?? []).map((it) => ({
    name: fmtScam(it.scam_type),
    count: it.count,
  }));

  return (
    <ChartShell
      title="Top scam types"
      subtitle="Most frequent categories"
      delay={0.15}
    >
      <div className="h-[220px] w-full">
        {status === "loading" ? (
          <Spinner />
        ) : status === "error" ? (
          <Err />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={rows}
              layout="vertical"
              margin={{ top: 4, right: 12, left: 0, bottom: 0 }}
            >
              <CartesianGrid horizontal={false} stroke="#eef2f7" />
              <XAxis
                type="number"
                tick={{ fill: BRAND.muted, fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={88}
                tick={{ fill: BRAND.muted, fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                {...LIGHT_TOOLTIP}
                cursor={{ fill: "rgba(81,120,235,0.06)" }}
              />
              <Bar
                dataKey="count"
                radius={[0, 6, 6, 0]}
                animationDuration={700}
              >
                {rows.map((_, i) => (
                  <Cell
                    key={i}
                    fill={
                      i === 0
                        ? BRAND.primary
                        : i === 1
                          ? BRAND.secondary
                          : BRAND.warn
                    }
                    fillOpacity={1 - i * 0.12}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </ChartShell>
  );
}

export const AnalyticsCarousel = memo(function AnalyticsCarousel() {
  const [trendDays, setTrendDays] = useState<TrendDays>(7);
  const [trendRisk, setTrendRisk] = useState<TrendRiskLevel>("all");
  const [trendInputTypes, setTrendInputTypes] = useState<TrendInputType[]>([]);
  const [trendPoints, setTrendPoints] = useState<TrendPoint[]>([]);
  const [trendStatus, setTrendStatus] = useState<LoadStatus>("loading");

  const [inputDist, setInputDist] = useState<InputTypeDistribution | null>(
    null,
  );
  const [inputStatus, setInputStatus] = useState<LoadStatus>("loading");

  const [riskDist, setRiskDist] = useState<RiskLevelDistribution | null>(null);
  const [riskStatus, setRiskStatus] = useState<LoadStatus>("loading");

  const [scamRank, setScamRank] = useState<ScanTypeRankingResponse | null>(
    null,
  );
  const [scamStatus, setScamStatus] = useState<LoadStatus>("loading");

  useEffect(() => {
    let cancelled = false;
    setTrendStatus("loading");
    fetchDetectionTrend(trendDays, trendRisk, trendInputTypes)
      .then((res) => {
        if (!cancelled) {
          setTrendPoints(
            res.points.map((p) => ({ ...p, date: shortDate(p.date) })),
          );
          setTrendStatus("ok");
        }
      })
      .catch(() => {
        if (!cancelled) setTrendStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [trendDays, trendRisk, trendInputTypes]);

  function toggleTrendInputType(next: TrendInputType) {
    setTrendInputTypes((prev) =>
      prev.includes(next) ? prev.filter((t) => t !== next) : [...prev, next],
    );
  }

  useEffect(() => {
    let cancelled = false;

    fetchInputTypeDistribution()
      .then((d) => {
        if (!cancelled) {
          setInputDist(d);
          setInputStatus("ok");
        }
      })
      .catch(() => {
        if (!cancelled) setInputStatus("error");
      });

    fetchRiskLevelDistribution()
      .then((d) => {
        if (!cancelled) {
          setRiskDist(d);
          setRiskStatus("ok");
        }
      })
      .catch(() => {
        if (!cancelled) setRiskStatus("error");
      });

    fetchScanTypeRanking(3)
      .then((d) => {
        if (!cancelled) {
          setScamRank(d);
          setScamStatus("ok");
        }
      })
      .catch(() => {
        if (!cancelled) setScamStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="mt-10"
    >
      <h3 className="mb-6 font-bold leading-tight text-[36px] text-[#213034]">
        Analytics overview
      </h3>

      <div className="grid gap-4 sm:gap-5 md:grid-cols-[minmax(0,1.3fr)_minmax(0,0.7fr)]">
        <TrendBlock
          points={trendPoints}
          status={trendStatus}
          days={trendDays}
          onDays={setTrendDays}
          risk={trendRisk}
          onRisk={setTrendRisk}
          inputTypes={trendInputTypes}
          onToggleInputType={toggleTrendInputType}
        />
        <InputBlock data={inputDist} status={inputStatus} />
        <RiskBlock data={riskDist} status={riskStatus} />
        <ScamBlock data={scamRank} status={scamStatus} />
      </div>
    </motion.div>
  );
});
