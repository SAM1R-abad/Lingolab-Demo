"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LevelBreakdownEntry } from "@/services/types";

export function LevelBreakdownChart({ data }: { data: LevelBreakdownEntry[] }) {
  const chartData = data.map((entry) => ({
    level: entry.level,
    score: entry.score_percent,
    passed: entry.passed,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
          <XAxis dataKey="level" tick={{ fontSize: 12, fill: "#64748B" }} axisLine={{ stroke: "#E2E8F0" }} />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 12, fill: "#64748B" }}
            axisLine={{ stroke: "#E2E8F0" }}
            unit="%"
          />
          <ReferenceLine y={80} stroke="#F59E0B" strokeDasharray="4 4" label={{ value: "Pass 80%", fontSize: 11, fill: "#F59E0B", position: "insideTopRight" }} />
          <Tooltip
            formatter={(value: number) => [`${value}%`, "Score"]}
            contentStyle={{ borderRadius: 8, borderColor: "#E2E8F0", fontSize: 12 }}
          />
          <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={48}>
            {chartData.map((entry) => (
              <Cell key={entry.level} fill={entry.passed ? "#44766C" : "#EF4444"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
