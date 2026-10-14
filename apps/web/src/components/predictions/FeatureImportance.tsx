"use client"

import { ResponsiveContainer, BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts"
import { AXIS_TICK, GRID_STROKE, chartTooltip } from "@/components/charts/chartTheme"
import { formatNumber } from "@/lib/format"
import type { RegressionOut } from "@/types/api"
import { useReducedMotion } from "@/lib/motion"

interface Props {
  regression: RegressionOut
}

export function FeatureImportance({ regression }: Props) {
  const reducedMotion = useReducedMotion()
  const data = [...regression.feature_importance]
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 12)
    .map((f) => ({ name: f.feature, importance: +(f.importance * 100).toFixed(1) }))

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-baseline gap-x-5 gap-y-1 text-sm text-f2">
        <span>
          R²:{" "}
          <strong className="font-serif text-2xl font-medium tabular-nums text-fg">
            {formatNumber(regression.r2, 3, 3)}
          </strong>
        </span>
        <span>
          RMSE: <strong className="font-medium tabular-nums text-fg">{formatNumber(regression.rmse, 2, 2)}</strong>
        </span>
      </div>
      <p className="text-xs text-f3">
        Objetivo: <strong className="font-medium text-f2">{regression.target_column}</strong>
      </p>

      <ResponsiveContainer width="100%" height={Math.max(160, data.length * 28)}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={GRID_STROKE} horizontal={false} />
          <XAxis type="number" unit="%" tick={AXIS_TICK} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ ...AXIS_TICK, fill: "var(--f2)" }}
            axisLine={false}
            tickLine={false}
            width={110}
          />
          <Tooltip {...chartTooltip(reducedMotion)} formatter={(v: number) => [`${v}%`, "Importancia"]} />
          <Bar isAnimationActive={!reducedMotion} dataKey="importance" barSize={10}>
            {/* The most important variable is the one highlighted in the accent. */}
            {data.map((d, i) => (
              <Cell key={d.name} fill={i === 0 ? "var(--au)" : "var(--fg)"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
