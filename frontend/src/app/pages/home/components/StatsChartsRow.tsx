import { memo, useEffect, useState } from "react";
import { motion } from "motion/react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import {
  fetchInputTypeDistribution,
  fetchRiskLevelDistribution,
  fetchScanTypeRanking,
  type InputTypeDistribution,
  type RiskLevelDistribution,
  type ScanTypeRankingResponse,
} from "@lib/api/detectionTrend";

/* ── helpers ── */
function pct(n: number, total: number) {
  if (!total) return "0%";
  return `${Math.round((n / total) * 100)}%`;
}

/** ScamTypeEnum.JOB_SCAM → Job Scam */
function fmtScamType(raw: string): string {
  return raw
    .replace(/^ScamTypeEnum\./i, "")
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ── shared mini-card wrapper ── */
function MiniCard({
  title,
  delay,
  children,
}: {
  title: string;
  delay: number;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay, ease: "easeOut" }}
      className="flex flex-col overflow-hidden rounded-2xl bg-gradient-to-br from-[#0f1929] to-[#1a2a40] shadow-[0_4px_32px_rgba(0,0,0,0.24)]"
    >
      <p className="px-5 pb-1 pt-4 text-xs font-semibold uppercase tracking-widest text-indigo-400">
        {title}
      </p>
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
    </motion.div>
  );
}

/* ── mini skeleton ── */
function MiniSkeleton() {
  return (
    <div className="flex h-[160px] items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500/30 border-t-indigo-500" />
    </div>
  );
}

function MiniError() {
  return (
    <div className="flex h-[160px] items-center justify-center text-xs text-slate-600">
      Unable to load
    </div>
  );
}

/* ── 1. Input Type Distribution (donut) ── */
const INPUT_COLORS: Record<string, string> = {
  Text: "#10B981",
  Image: "#3B82F6",
  URL: "#F59E0B",
  QR: "#EC4899",
};

function InputTypeDonut() {
  const [data, setData] = useState<InputTypeDistribution | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let ok = true;
    fetchInputTypeDistribution()
      .then((d) => ok && setData(d))
      .catch(() => ok && setErr(true));
    return () => { ok = false; };
  }, []);

  if (err) return <MiniError />;
  if (!data) return <MiniSkeleton />;

  const slices = [
    { name: "Text",  value: data.text_count  },
    { name: "Image", value: data.image_count },
    { name: "URL",   value: data.url_count   },
    { name: "QR",    value: data.qr_count    },
  ].filter((s) => s.value > 0);

  return (
    <div className="flex items-center gap-2 px-3 pb-4 pt-1">
      <ResponsiveContainer width="50%" height={140}>
        <PieChart>
          <Pie
            data={slices}
            cx="50%"
            cy="50%"
            innerRadius={38}
            outerRadius={58}
            paddingAngle={2}
            dataKey="value"
            animationBegin={100}
            animationDuration={700}
          >
            {slices.map((s) => (
              <Cell key={s.name} fill={INPUT_COLORS[s.name]} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#1e2d3d",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 10,
              fontSize: 12,
            }}
            itemStyle={{ color: "#e2e8f0" }}
            labelStyle={{ display: "none" }}
          />
        </PieChart>
      </ResponsiveContainer>

      <ul className="flex flex-col gap-1.5 text-[11px]">
        {slices.map((s) => (
          <li key={s.name} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 shrink-0 rounded-full"
              style={{ background: INPUT_COLORS[s.name] }}
            />
            <span className="text-slate-400">{s.name}</span>
            <span className="ml-auto pl-2 font-bold tabular-nums text-white">
              {pct(s.value, data.total)}
            </span>
          </li>
        ))}
        <li className="mt-1 border-t border-white/10 pt-1 text-slate-500">
          Total&nbsp;
          <span className="font-semibold text-slate-300">{data.total}</span>
        </li>
      </ul>
    </div>
  );
}

/* ── 2. Risk Level Distribution (donut) ── */
const RISK_COLORS: Record<string, string> = {
  High:    "#EF4444",
  Medium:  "#F59E0B",
  Low:     "#10B981",
  Unknown: "#6B7280",
};

function RiskLevelDonut() {
  const [data, setData] = useState<RiskLevelDistribution | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let ok = true;
    fetchRiskLevelDistribution()
      .then((d) => ok && setData(d))
      .catch(() => ok && setErr(true));
    return () => { ok = false; };
  }, []);

  if (err) return <MiniError />;
  if (!data) return <MiniSkeleton />;

  const slices = [
    { name: "High",    value: data.high_count    },
    { name: "Medium",  value: data.medium_count  },
    { name: "Low",     value: data.low_count     },
    { name: "Unknown", value: data.unknown_count },
  ].filter((s) => s.value > 0);

  return (
    <div className="flex items-center gap-2 px-3 pb-4 pt-1">
      <ResponsiveContainer width="50%" height={140}>
        <PieChart>
          <Pie
            data={slices}
            cx="50%"
            cy="50%"
            innerRadius={38}
            outerRadius={58}
            paddingAngle={2}
            dataKey="value"
            animationBegin={100}
            animationDuration={700}
          >
            {slices.map((s) => (
              <Cell key={s.name} fill={RISK_COLORS[s.name]} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#1e2d3d",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 10,
              fontSize: 12,
            }}
            itemStyle={{ color: "#e2e8f0" }}
            labelStyle={{ display: "none" }}
          />
        </PieChart>
      </ResponsiveContainer>

      <ul className="flex flex-col gap-1.5 text-[11px]">
        {slices.map((s) => (
          <li key={s.name} className="flex items-center gap-1.5">
            <span
              className="inline-block h-2 w-2 shrink-0 rounded-full"
              style={{ background: RISK_COLORS[s.name] }}
            />
            <span className="text-slate-400">{s.name}</span>
            <span className="ml-auto pl-2 font-bold tabular-nums text-white">
              {pct(s.value, data.total)}
            </span>
          </li>
        ))}
        <li className="mt-1 border-t border-white/10 pt-1 text-slate-500">
          Total&nbsp;
          <span className="font-semibold text-slate-300">{data.total}</span>
        </li>
      </ul>
    </div>
  );
}

/* ── 3. Scan Type Ranking (horizontal bar) ── */
function ScanTypeBar() {
  const [data, setData] = useState<ScanTypeRankingResponse | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let ok = true;
    fetchScanTypeRanking(3)
      .then((d) => ok && setData(d))
      .catch(() => ok && setErr(true));
    return () => { ok = false; };
  }, []);

  if (err) return <MiniError />;
  if (!data) return <MiniSkeleton />;

  const rows = data.items.map((it) => ({
    name: fmtScamType(it.scam_type),
    count: it.count,
  }));

  return (
    <div className="px-2 pb-3 pt-1">
      <ResponsiveContainer width="100%" height={155}>
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 0, right: 20, left: 4, bottom: 0 }}
        >
          <CartesianGrid
            horizontal={false}
            stroke="rgba(255,255,255,0.04)"
          />
          <XAxis
            type="number"
            tick={{ fill: "#64748b", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={82}
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "#1e2d3d",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 10,
              fontSize: 12,
            }}
            itemStyle={{ color: "#e2e8f0" }}
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
          />
          <Bar
            dataKey="count"
            radius={[0, 4, 4, 0]}
            animationDuration={700}
            animationEasing="ease-out"
          >
            {rows.map((_, i) => {
              const opacity = 1 - i * 0.15;
              return <Cell key={i} fill={`rgba(99,102,241,${opacity})`} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ── exported row ── */
export const StatsChartsRow = memo(function StatsChartsRow() {
  return (
    <div className="mt-4 grid gap-4 sm:grid-cols-3">
      <MiniCard title="Input Type Mix" delay={0}>
        <InputTypeDonut />
      </MiniCard>

      <MiniCard title="Risk Distribution" delay={0.1}>
        <RiskLevelDonut />
      </MiniCard>

      <MiniCard title="Top Scam Types" delay={0.2}>
        <ScanTypeBar />
      </MiniCard>
    </div>
  );
});
