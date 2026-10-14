"use client"

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { formatIsoDate } from "@/lib/format"
import { AXIS_LINE, AXIS_TICK, GRID_STROKE, TOOLTIP_PROPS } from "./chartTheme"

interface Props {
  data: { date: string; value: number | null }[]
  yColumn: string
}

export function TimeSeriesChart({ data, yColumn }: Props) {
  const formatted = data.map((d) => ({ ...d, label: formatIsoDate(d.date, { year: false }) ?? d.date }))

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={formatted} margin={{ right: 8 }}>
        <CartesianGrid stroke={GRID_STROKE} vertical={false} />
        {/* minTickGap lets Recharts drop ticks on narrow screens instead of overlapping them. */}
        <XAxis
          dataKey="label"
          tick={AXIS_TICK}
          axisLine={AXIS_LINE}
          interval="preserveStartEnd"
          minTickGap={32}
          tickLine={false}
        />
        <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={48} />
        <Tooltip {...TOOLTIP_PROPS} formatter={(v: number) => [v, yColumn]} />
        <Line
          type="linear"
          dataKey="value"
          stroke="var(--fg)"
          dot={false}
          strokeWidth={1.25}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
