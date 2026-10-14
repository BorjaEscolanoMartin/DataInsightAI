"use client"

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { AXIS_TICK, GRID_STROKE, TOOLTIP_PROPS } from "./chartTheme"

interface Props {
  data: { name: string; count: number }[]
}

export function CategoricalBarChart({ data }: Props) {
  const height = Math.max(160, data.length * 28)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid stroke={GRID_STROKE} horizontal={false} />
        <XAxis type="number" tick={AXIS_TICK} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ ...AXIS_TICK, fill: "var(--f2)" }}
          axisLine={false}
          width={100}
          tickLine={false}
        />
        <Tooltip {...TOOLTIP_PROPS} />
        <Bar dataKey="count" name="Filas" fill="var(--fg)" barSize={8} />
      </BarChart>
    </ResponsiveContainer>
  )
}
