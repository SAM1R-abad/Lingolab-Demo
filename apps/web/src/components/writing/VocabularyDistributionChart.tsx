"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CEFRLevel } from "@/services/types";

const LEVEL_ORDER: CEFRLevel[] = ["A1", "A2", "B1", "B2", "C1", "C2"];

export function VocabularyDistributionChart({
  distribution,
  dominantLevel,
}: {
  distribution: Record<string, number>;
  dominantLevel: CEFRLevel | null;
}) {
  const total = Object.values(distribution).reduce((sum, n) => sum + n, 0) || 1;
  const chartData = LEVEL_ORDER.map((level) => ({
    level,
    percent: Math.round(((distribution[level] ?? 0) / total) * 100),
    count: distribution[level] ?? 0,
  }));
  const unknownCount = distribution["unknown"] ?? 0;

  return (
    <div className="flex flex-col gap-2">
      <div className="h-56 w-full">
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
            <Tooltip
              formatter={(value: number, _name, item) => [
                `${value}% (${item.payload.count} words)`,
                "Share of analyzed words",
              ]}
              contentStyle={{ borderRadius: 8, borderColor: "#E2E8F0", fontSize: 12 }}
            />
            <Bar dataKey="percent" radius={[6, 6, 0, 0]} maxBarSize={48}>
              {chartData.map((entry) => (
                <Cell key={entry.level} fill={entry.level === dominantLevel ? "#44766C" : "#A9CBB7"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-caption text-text-secondary">
        Dominant vocabulary level: <span className="font-medium text-text-primary">{dominantLevel ?? "n/a"}</span> -
        the most common CEFR level among the words used, not an overall proficiency verdict.
        {unknownCount > 0 && ` ${unknownCount} word(s) were not found in the CEFR wordlist and are excluded above.`}
      </p>
    </div>
  );
}
