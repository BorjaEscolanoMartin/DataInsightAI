"use client"

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { countAxis, numberTick } from "./axis"
import { AXIS_LINE, AXIS_TICK, GRID_STROKE, chartTooltip } from "./chartTheme"
import { useReducedMotion } from "@/lib/motion"

interface Props {
  data: { name: string; count: number }[]
}

// The label column fits the longest category name (as in the mockup), estimated at the 11 px
// tick font: jsdom and the first render cannot measure text.
const LABEL_CHAR_WIDTH = 6.2
const LABEL_GAP = 8
const LABEL_MIN_WIDTH = 32
const LABEL_MAX_WIDTH = 140

/** Width of the category label column: the longest name plus the gap before the bars, between
 *  32 and 140 px (longer names are cut by the axis). */
export function categoryLabelWidth(names: string[]): number {
  const longest = Math.max(0, ...names.map((n) => n.length))
  const width = Math.ceil(longest * LABEL_CHAR_WIDTH) + LABEL_GAP
  return Math.min(LABEL_MAX_WIDTH, Math.max(LABEL_MIN_WIDTH, width))
}

export function CategoricalBarChart({ data }: Props) {
  const reducedMotion = useReducedMotion()
  const height = Math.max(160, data.length * 28)
  const axis = countAxis(Math.max(0, ...data.map((d) => d.count)))

  return (
    <div data-orientation="horizontal">
      <ResponsiveContainer width="100%" height={height}>
        {/* The right margin keeps the last tick label («1.000») whole. */}
        {/* Each bar takes 60 % of its row, as in the mockup: Recharts leaves barCategoryGap on
            each side of the bar, so 20 % + 60 % + 20 %. */}
        <BarChart data={data} layout="vertical" barCategoryGap="20%" margin={{ left: 8, right: 24 }}>
          <CartesianGrid stroke={GRID_STROKE} horizontal={false} />
          <XAxis
            type="number"
            domain={axis.domain}
            ticks={axis.ticks}
            tickFormatter={numberTick}
            tick={AXIS_TICK}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ ...AXIS_TICK, fill: "var(--f2)" }}
            axisLine={false}
            width={categoryLabelWidth(data.map((d) => d.name))}
            tickMargin={LABEL_GAP}
            tickLine={false}
          />
          <Tooltip {...chartTooltip(reducedMotion)} />
          <Bar isAnimationActive={!reducedMotion} dataKey="count" name="Filas" fill="var(--fg)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** One vertical column per value of a whole-number column, in value order: a distribution, not
 *  a ranking (W2). */
export function ValueColumnChart({ data }: Props) {
  const reducedMotion = useReducedMotion()
  const axis = countAxis(Math.max(0, ...data.map((d) => d.count)))
  return (
    <div data-orientation="vertical">
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} barCategoryGap="30%">
          <CartesianGrid stroke={GRID_STROKE} vertical={false} />
          <XAxis dataKey="name" tick={AXIS_TICK} axisLine={AXIS_LINE} tickLine={false} interval={0} />
          <YAxis
            domain={axis.domain}
            ticks={axis.ticks}
            tickFormatter={numberTick}
            tick={AXIS_TICK}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip {...chartTooltip(reducedMotion)} />
          <Bar isAnimationActive={!reducedMotion} dataKey="count" name="Filas" fill="var(--fg)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
