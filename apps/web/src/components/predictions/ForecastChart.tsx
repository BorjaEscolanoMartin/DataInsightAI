"use client"

import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts"
import type { ForecastOut } from "@/types/api"

interface Props {
  forecast: ForecastOut
}

export function ForecastChart({ forecast }: Props) {
  const data = forecast.points.map((p) => ({
    ds: p.ds,
    yhat: +p.yhat.toFixed(2),
    yhat_lower: +p.yhat_lower.toFixed(2),
    yhat_upper: +p.yhat_upper.toFixed(2),
    band: [+p.yhat_lower.toFixed(2), +p.yhat_upper.toFixed(2)] as [number, number],
  }))

  const tickCount = Math.min(6, data.length)
  const step = Math.max(1, Math.floor(data.length / tickCount))
  const ticks = data.filter((_, i) => i % step === 0).map((d) => d.ds)

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-400">
        <span>
          Objetivo: <strong className="text-gray-200">{forecast.target_column}</strong>
        </span>
        <span>
          Fecha: <strong className="text-gray-200">{forecast.date_column}</strong>
        </span>
        <span>
          Horizonte: <strong className="text-gray-200">{forecast.horizon_days} días</strong>
        </span>
        {forecast.mape !== null && (
          <span>
            MAPE backtest: <strong className="text-indigo-300">{forecast.mape.toFixed(1)}%</strong>
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            dataKey="ds"
            ticks={ticks}
            tick={{ fontSize: 11, fill: "#6b7280" }}
            stroke="#374151"
          />
          <YAxis tick={{ fontSize: 11, fill: "#6b7280" }} stroke="#374151" width={60} />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #374151", fontSize: 12 }}
            labelStyle={{ color: "#e5e7eb" }}
            itemStyle={{ color: "#a5b4fc" }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: "#9ca3af" }} />
          <Area
            type="monotone"
            dataKey="yhat_upper"
            fill="#4338ca"
            stroke="transparent"
            fillOpacity={0.15}
            name="IC superior"
          />
          <Area
            type="monotone"
            dataKey="yhat_lower"
            fill="#111827"
            stroke="transparent"
            fillOpacity={1}
            name="IC inferior"
          />
          <Line
            type="monotone"
            dataKey="yhat"
            stroke="#818cf8"
            strokeWidth={2}
            dot={false}
            name="Predicción"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
