"use client"

import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { AXIS_LINE, AXIS_TICK, GRID_STROKE, TOOLTIP_PROPS } from "./chartTheme"

interface Props {
  data: { x: number | null; y: number | null }[]
  xCol: string
  yCol: string
}

export function ScatterChartComp({ data, xCol, yCol }: Props) {
  const clean = data.filter((d) => d.x !== null && d.y !== null) as { x: number; y: number }[]

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ScatterChart margin={{ right: 8, bottom: 8 }}>
        <CartesianGrid stroke={GRID_STROKE} />
        <XAxis
          dataKey="x"
          name={xCol}
          type="number"
          tick={AXIS_TICK}
          axisLine={AXIS_LINE}
          tickLine={false}
          label={{ value: xCol, position: "insideBottom", offset: -4, ...AXIS_TICK }}
        />
        <YAxis dataKey="y" name={yCol} type="number" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} width={48} />
        <Tooltip {...TOOLTIP_PROPS} cursor={{ stroke: "var(--ln)" }} />
        <Scatter data={clean} fill="var(--fg)" fillOpacity={0.6} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
