"use client"

import { formatNumber } from "@/lib/format"

interface HeatmapDatum {
  x: string
  y: string
  value: number
}

interface Props {
  columns: string[]
  data: HeatmapDatum[]
}

/** Cell background: the accent for positive r, a neutral tone for negative r, from 10 % (r = 0)
 *  to 50 % (|r| = 1) over the page background (docs: odd/tasks/redesign.md, S13). */
export function correlationCellColor(r: number): string {
  const share = Math.round(10 + 40 * Math.min(1, Math.abs(r)))
  const tone = r < 0 ? "--f3" : "--au"
  return `color-mix(in srgb, var(${tone}) ${share}%, var(--bg))`
}

/** More variables than this take the whole width of the chart grid, with their full names (W5). */
const MAX_COMPACT_COLUMNS = 4
/** A wide heatmap keeps its cells readable on a phone and scrolls sideways in its box. */
const WIDE_MIN_WIDTH = 620

export function isWideHeatmap(columns: string[]): boolean {
  return columns.length > MAX_COMPACT_COLUMNS
}

function formatR(r: number): string {
  return formatNumber(r, 2, 2)
}

export function HeatmapChart({ columns, data }: Props) {
  const lookup = new Map(data.map((d) => [`${d.x}||${d.y}`, d.value]))
  const value = (row: string, col: string) => lookup.get(`${row}||${col}`) ?? 0

  const pairs = columns.flatMap((a, i) =>
    columns.slice(i + 1).map((b) => `${a} y ${b}: ${formatR(value(a, b))}`),
  )

  const wide = isWideHeatmap(columns)
  // Compact: names cut to fit one cell of the grid. Wide: whole names, the row labels as wide as
  // the longest one.
  const name = wide ? "text-f3" : "truncate text-f3"

  return (
    // A wide heatmap scrolls sideways on narrow screens: its box takes the keyboard focus so the
    // hidden columns can be reached with the arrow keys.
    <div
      className="overflow-x-auto focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-au"
      {...(wide && {
        role: "region",
        "aria-label": "Mapa de correlaciones, desplazable en horizontal",
        tabIndex: 0,
      })}
    >
      <div
        role="img"
        aria-label={`Coeficientes de correlación. ${pairs.join("; ")}`}
        className="grid gap-[3px] text-sm"
        style={{
          gridTemplateColumns: wide
            ? `max-content repeat(${columns.length}, minmax(44px, 1fr))`
            : `78px repeat(${columns.length}, minmax(44px, 1fr))`,
          minWidth: wide ? `${WIDE_MIN_WIDTH}px` : undefined,
        }}
      >
        <span />
        {columns.map((col) => (
          <span key={col} className={`${name} self-end text-center text-xs`} title={col}>
            {col}
          </span>
        ))}
        {columns.map((row) => [
          <span key={row} className={`${name} self-center pr-2 text-right text-xs`} title={row}>
            {row}
          </span>,
          ...columns.map((col) => {
            const r = value(row, col)
            return (
              <span
                key={`${row}||${col}`}
                className="flex h-11 items-center justify-center font-medium tabular-nums text-fg"
                style={{ background: correlationCellColor(r) }}
              >
                {formatR(r)}
              </span>
            )
          }),
        ])}
      </div>
    </div>
  )
}
