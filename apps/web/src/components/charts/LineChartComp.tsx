"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts"

interface Props {
  data: { date: string; value: number | null }[]
  yColumn: string
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("es-ES", { day: "2-digit", month: "short" })
  } catch {
    return iso
  }
}

export function TimeSeriesChart({ data, yColumn }: Props) {
  const formatted = data.map((d) => ({ ...d, label: formatDate(d.date) }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={formatted} margin={{ right: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 9, fill: "#6b7280" }}
          interval="preserveStartEnd"
          tickLine={false}
        />
        <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
          labelStyle={{ color: "#d1d5db", fontSize: 11 }}
          itemStyle={{ color: "#6ee7b7" }}
          formatter={(v: number) => [v, yColumn]}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="#10b981"
          dot={false}
          strokeWidth={1.5}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
