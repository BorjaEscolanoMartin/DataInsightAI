"use client"

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { AXIS_LINE, AXIS_TICK, GRID_STROKE, TOOLTIP_PROPS } from "./chartTheme"

interface Props {
  data: { bin: string; count: number }[]
}

export function HistogramChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} barCategoryGap={1}>
        <CartesianGrid stroke={GRID_STROKE} vertical={false} />
        <XAxis
          dataKey="bin"
          tick={AXIS_TICK}
          axisLine={AXIS_LINE}
          interval="preserveStartEnd"
          minTickGap={16}
          tickLine={false}
        />
        <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={40} />
        <Tooltip {...TOOLTIP_PROPS} />
        <Bar dataKey="count" name="Filas" fill="var(--fg)" />
      </BarChart>
    </ResponsiveContainer>
  )
}
