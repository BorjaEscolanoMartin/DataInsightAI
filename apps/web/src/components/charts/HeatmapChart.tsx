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

function formatR(r: number): string {
  return formatNumber(r, 2, 2)
}

export function HeatmapChart({ columns, data }: Props) {
  const lookup = new Map(data.map((d) => [`${d.x}||${d.y}`, d.value]))
  const value = (row: string, col: string) => lookup.get(`${row}||${col}`) ?? 0

  const pairs = columns.flatMap((a, i) =>
    columns.slice(i + 1).map((b) => `${a} y ${b}: ${formatR(value(a, b))}`),
  )

  return (
    <div className="overflow-x-auto">
      <div
        role="img"
        aria-label={`Coeficientes de correlación. ${pairs.join("; ")}`}
        className="grid gap-[3px] text-sm"
        style={{ gridTemplateColumns: `78px repeat(${columns.length}, minmax(44px, 1fr))` }}
      >
        <span />
        {columns.map((col) => (
          <span key={col} className="truncate text-center text-xs text-f3" title={col}>
            {col}
          </span>
        ))}
        {columns.map((row) => [
          <span key={row} className="self-center truncate text-xs text-f3" title={row}>
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
