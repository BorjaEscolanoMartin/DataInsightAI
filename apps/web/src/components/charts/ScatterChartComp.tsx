"use client"

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts"

interface Props {
  data: { x: number | null; y: number | null }[]
  xCol: string
  yCol: string
}

export function ScatterChartComp({ data, xCol, yCol }: Props) {
  const clean = data.filter((d) => d.x !== null && d.y !== null) as { x: number; y: number }[]

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ScatterChart margin={{ right: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis
          dataKey="x"
          name={xCol}
          type="number"
          tick={{ fontSize: 10, fill: "#6b7280" }}
          axisLine={false}
          tickLine={false}
          label={{ value: xCol, position: "insideBottom", offset: -2, fontSize: 10, fill: "#6b7280" }}
        />
        <YAxis
          dataKey="y"
          name={yCol}
          type="number"
          tick={{ fontSize: 10, fill: "#6b7280" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
          itemStyle={{ color: "#fcd34d", fontSize: 11 }}
          cursor={{ strokeDasharray: "3 3" }}
        />
        <Scatter data={clean} fill="#f59e0b" opacity={0.55} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
