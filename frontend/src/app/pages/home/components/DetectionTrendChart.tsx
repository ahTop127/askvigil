import { memo, useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  fetchDetectionTrend,
  type TrendPoint,
  type TrendDays,
  type TrendRiskLevel,
} from "@lib/api/detectionTrend";

/* ── palette ── */
const SERIES = [
  {
    key: "total_count",
    label: "Total",
    color: "#6366F1",
    gradient: "grad-total",
  },
  { key: "text", label: "Text", color: "#10B981", gradient: "grad-text" },
  { key: "url", label: "URL", color: "#F59E0B", gradient: "grad-url" },
  { key: "image", label: "Image", color: "#3B82F6", gradient: "grad-image" },
  { key: "qr", label: "QR", color: "#EC4899", gradient: "grad-qr" },
] as const;

type SeriesKey = (typeof SERIES)[number]["key"];

const RISK_OPTIONS: { value: TrendRiskLevel; label: string }[] = [
  { value: "all", label: "All" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

/* ── helpers ── */
function shortDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-MY", { month: "short", day: "numeric" });
}

/* ── custom tooltip ── */
type TooltipPayload = {
  color: string;
  name: string;
  value: number;
  dataKey: string;
};

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-white/10 bg-[#1a2332]/90 px-4 py-3 shadow-2xl backdrop-blur-sm">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </p>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2 text-sm">
          <span
            className="inline-block h-2 w-2 shrink-0 rounded-full"
            style={{ background: p.color }}
          />
          <span className="text-slate-300">{p.name}</span>
          <span className="ml-auto pl-4 font-bold tabular-nums text-white">
            {p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/* ── skeleton ── */
function Skeleton() {
  return (
    <div className="flex h-[280px] items-end gap-1 px-4 pb-2">
      {Array.from({ length: 14 }).map((_, i) => (
        <div
          key={i}
          className="flex-1 animate-pulse rounded-t-sm bg-slate-200/60"
          style={{ height: `${30 + ((i * 17 + 40) % 55)}%` }}
        />
      ))}
    </div>
  );
}

/* ── main component ── */
export const DetectionTrendChart = memo(function DetectionTrendChart() {
  const [days, setDays] = useState<TrendDays>(7);
  const [risk, setRisk] = useState<TrendRiskLevel>("all");
  const [points, setPoints] = useState<TrendPoint[]>([]);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const [visible, setVisible] = useState<Set<SeriesKey>>(
    new Set(["total_count"]),
  );

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    fetchDetectionTrend(days, risk)
      .then((res) => {
        if (!cancelled) {
          setPoints(res.points.map((p) => ({ ...p, date: shortDate(p.date) })));
          setStatus("ok");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [days, risk]);

  function toggleSeries(key: SeriesKey) {
    setVisible((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size > 1) next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="mt-14 overflow-hidden rounded-3xl bg-gradient-to-br from-[#0f1929] to-[#1a2a40] shadow-[0_8px_48px_rgba(0,0,0,0.28)]"
    >
      {/* header */}
      <div className="flex flex-wrap items-start justify-between gap-4 px-6 pb-0 pt-6 md:px-8 md:pt-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400">
            Live Analytics
          </p>
          <h3 className="mt-1 text-xl font-bold text-white md:text-2xl">
            Detection Trend
          </h3>
        </div>

        {/* controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* risk level */}
          <div className="flex overflow-hidden rounded-full border border-white/10 text-xs font-semibold">
            {RISK_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setRisk(opt.value)}
                className={`px-3 py-1.5 transition-colors ${
                  risk === opt.value
                    ? "bg-indigo-600 text-white"
                    : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* day range */}
          <div className="flex overflow-hidden rounded-full border border-white/10 text-xs font-semibold">
            {([7, 30] as TrendDays[]).map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 transition-colors ${
                  days === d
                    ? "bg-indigo-600 text-white"
                    : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                }`}
              >
                {d}D
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* series toggles */}
      <div className="mt-4 flex flex-wrap gap-2 px-6 md:px-8">
        {SERIES.map((s) => {
          const on = visible.has(s.key);
          return (
            <button
              key={s.key}
              type="button"
              onClick={() => toggleSeries(s.key)}
              className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold transition-all ${
                on
                  ? "border-transparent text-white"
                  : "border-white/10 bg-white/5 text-slate-500 hover:text-slate-300"
              }`}
              style={
                on
                  ? { background: s.color + "33", borderColor: s.color + "55" }
                  : {}
              }
            >
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ background: on ? s.color : "#4b5563" }}
              />
              {s.label}
            </button>
          );
        })}
      </div>

      {/* chart area */}
      <div className="px-2 pb-6 pt-4 md:px-4">
        <AnimatePresence mode="wait">
          {status === "loading" ? (
            <motion.div
              key="skeleton"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <Skeleton />
            </motion.div>
          ) : status === "error" ? (
            <motion.div
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex h-[280px] items-center justify-center text-sm text-slate-500"
            >
              Unable to load trend data
            </motion.div>
          ) : (
            <motion.div
              key={`chart-${days}-${risk}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.35 }}
            >
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart
                  data={points}
                  margin={{ top: 8, right: 16, left: -8, bottom: 0 }}
                >
                  <defs>
                    {SERIES.map((s) => (
                      <linearGradient
                        key={s.gradient}
                        id={s.gradient}
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor={s.color}
                          stopOpacity={0.35}
                        />
                        <stop
                          offset="95%"
                          stopColor={s.color}
                          stopOpacity={0.0}
                        />
                      </linearGradient>
                    ))}
                  </defs>

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.05)"
                  />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: "#64748b", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: "#64748b", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip
                    content={<CustomTooltip />}
                    cursor={{ stroke: "rgba(255,255,255,0.1)", strokeWidth: 1 }}
                  />
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ display: "none" }}
                  />

                  {SERIES.filter((s) => visible.has(s.key)).map((s) => (
                    <Area
                      key={s.key}
                      type="monotone"
                      dataKey={s.key}
                      name={s.label}
                      stroke={s.color}
                      strokeWidth={2}
                      fill={`url(#${s.gradient})`}
                      dot={false}
                      activeDot={{ r: 4, strokeWidth: 0 }}
                      animationDuration={800}
                      animationEasing="ease-out"
                    />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
});
