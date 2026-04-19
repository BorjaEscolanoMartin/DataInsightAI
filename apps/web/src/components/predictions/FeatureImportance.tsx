"use client"

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts"
import type { RegressionOut } from "@/types/api"

interface Props {
  regression: RegressionOut
}

export function FeatureImportance({ regression }: Props) {
  const data = [...regression.feature_importance]
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 12)
    .map((f) => ({ name: f.feature, importance: +(f.importance * 100).toFixed(1) }))

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-400">
        <span>
          Objetivo: <strong className="text-gray-200">{regression.target_column}</strong>
        </span>
        <span>
          R²: <strong className="text-indigo-300">{regression.r2.toFixed(3)}</strong>
        </span>
        <span>
          RMSE: <strong className="text-gray-200">{regression.rmse.toFixed(2)}</strong>
        </span>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 4, right: 16, left: 80, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
          <XAxis
            type="number"
            unit="%"
            tick={{ fontSize: 11, fill: "#6b7280" }}
            stroke="#374151"
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 11, fill: "#9ca3af" }}
            stroke="#374151"
            width={76}
          />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #374151", fontSize: 12 }}
            formatter={(v: number) => [`${v}%`, "Importancia"]}
          />
          <Bar dataKey="importance" fill="#6366f1" radius={[0, 3, 3, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
