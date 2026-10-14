"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Rectangle,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type BarProps,
  type RectangleProps,
} from "recharts"
import { AXIS_LINE, AXIS_TICK, GRID_STROKE, TOOLTIP_PROPS } from "./chartTheme"
import type { HistogramBar, HistogramView } from "./histogram"

interface Props {
  view: HistogramView
}

// Outlier bins stand a few pixels apart from the bins inside the IQR range (W1).
const OUTLIER_GAP = 4

interface TickProps {
  x: number
  y: number
  payload: { index: number }
}

export function HistogramChart({ view }: Props) {
  const { bars, axis } = view
  const firstInner = bars.findIndex((b) => b.side === null)
  const lastInner = bars.findLastIndex((b) => b.side === null)

  // Axis labels: the first and last bound of the inner bins, and each outlier bin's own label
  // in the accent under it.
  const tick = ({ x, y, payload }: TickProps) => {
    const bar = bars[payload.index]
    const label = (text: string, anchor: "start" | "end", fill: string, dy: number) => (
      <text x={x} y={y} dy={dy} textAnchor={anchor} fontSize={AXIS_TICK.fontSize} fill={fill}>
        {text}
      </text>
    )
    if (!axis || !bar) return <g />
    if (bar.side === "above") return label(bar.range, "end", "var(--au)", 26)
    if (bar.side === "below") return label(bar.range, "start", "var(--au)", 26)
    if (payload.index === firstInner) return label(axis.first, "start", AXIS_TICK.fill, 12)
    if (payload.index === lastInner) return label(axis.last, "end", AXIS_TICK.fill, 12)
    return <g />
  }

  const shape: BarProps["shape"] = (props: unknown) => {
    const bar = props as RectangleProps & { payload?: HistogramBar }
    const side = bar.payload?.side
    const shift = side === "above" ? OUTLIER_GAP : side === "below" ? -OUTLIER_GAP : 0
    return <Rectangle {...bar} x={(bar.x ?? 0) + shift} />
  }

  return (
    <ResponsiveContainer width="100%" height={axis ? 214 : 200}>
      <BarChart data={bars} barCategoryGap={1}>
        <CartesianGrid stroke={GRID_STROKE} vertical={false} />
        {axis ? (
          <XAxis dataKey="range" tick={tick} axisLine={AXIS_LINE} interval={0} tickLine={false} height={34} />
        ) : (
          <XAxis
            dataKey="range"
            tick={AXIS_TICK}
            axisLine={AXIS_LINE}
            interval="preserveStartEnd"
            minTickGap={16}
            tickLine={false}
          />
        )}
        <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={40} />
        <Tooltip {...TOOLTIP_PROPS} />
        <Bar dataKey="count" name="Filas" fill="var(--fg)" shape={shape}>
          {bars.map((b, i) => (
            <Cell key={i} fill={b.side ? "var(--au)" : "var(--fg)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
