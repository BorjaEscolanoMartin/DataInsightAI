"use client"

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { AXIS_LINE, AXIS_TICK, GRID_STROKE, TOOLTIP_PROPS } from "./chartTheme"

interface Props {
  data: { name: string; count: number }[]
}

export function CategoricalBarChart({ data }: Props) {
  const height = Math.max(160, data.length * 28)

  return (
    <div data-orientation="horizontal">
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
    </div>
  )
}

/** One vertical column per value of a whole-number column, in value order: a distribution, not
 *  a ranking (W2). */
export function ValueColumnChart({ data }: Props) {
  return (
    <div data-orientation="vertical">
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} barCategoryGap="30%">
          <CartesianGrid stroke={GRID_STROKE} vertical={false} />
          <XAxis dataKey="name" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} interval={0} />
          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={40} />
          <Tooltip {...TOOLTIP_PROPS} />
          <Bar dataKey="count" name="Filas" fill="var(--fg)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
