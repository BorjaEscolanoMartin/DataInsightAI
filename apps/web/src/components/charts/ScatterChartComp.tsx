"use client"

import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { numberTick, scatterAxis } from "./axis"
import { AXIS_LINE, AXIS_TICK, GRID_STROKE, chartTooltip } from "./chartTheme"
import { useReducedMotion } from "@/lib/motion"

interface Props {
  data: { x: number | null; y: number | null }[]
  xCol: string
  yCol: string
}

export function ScatterChartComp({ data, xCol, yCol }: Props) {
  const reducedMotion = useReducedMotion()
  const clean = data.filter((d) => d.x !== null && d.y !== null) as { x: number; y: number }[]
  // Axes fitted to the points with a 5 % margin, never below 0 for non-negative data (W4).
  const xAxis = scatterAxis(clean.map((d) => d.x))
  const yAxis = scatterAxis(clean.map((d) => d.y))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ScatterChart margin={{ right: 8, bottom: 8 }}>
        <CartesianGrid stroke={GRID_STROKE} />
        <XAxis
          dataKey="x"
          name={xCol}
          type="number"
          domain={xAxis?.domain}
          ticks={xAxis?.ticks}
          tickFormatter={numberTick}
          tick={AXIS_TICK}
          axisLine={AXIS_LINE}
          tickLine={false}
          label={{ value: xCol, position: "insideBottom", offset: -4, ...AXIS_TICK }}
        />
        <YAxis
          dataKey="y"
          name={yCol}
          type="number"
          domain={yAxis?.domain}
          ticks={yAxis?.ticks}
          tickFormatter={numberTick}
          tick={AXIS_TICK}
          axisLine={AXIS_LINE}
          tickLine={false}
          width={56}
        />
        <Tooltip {...chartTooltip(reducedMotion)} cursor={{ stroke: "var(--ln)" }} />
        {/* One series. A 0,45 fill alone falls under 3:1 on the light background; the opaque 1 px
            stroke keeps each point's edge at 4,69:1 (light) and 10,31:1 (dark) (S21). */}
        <Scatter isAnimationActive={!reducedMotion} data={clean} fill="var(--au)" fillOpacity={0.45} stroke="var(--au)" strokeWidth={1} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
