"use client"

import { useState } from "react"
import { formatNumber } from "@/lib/format"
import type { ColumnProfile } from "@/types/api"

const TYPE_LABELS: Record<ColumnProfile["type"], string> = {
  numeric: "numérica",
  categorical: "categórica",
  date: "fecha",
  text: "texto",
  boolean: "booleana",
}

function fmt(n: number | undefined, decimals: number): string {
  return n === undefined || n === null ? "—" : formatNumber(n, decimals)
}

function summary(col: ColumnProfile): string {
  if (col.type === "numeric") {
    const parts = [`media ${fmt(col.mean, 1)}`, `desviación ${fmt(col.std, 1)}`]
    if ((col.outlier_count ?? 0) > 0) parts.push(`${formatNumber(col.outlier_count!)} atípicos`)
    return parts.join(" · ")
  }
  const top = col.top_categories ?? []
  if (top.length === 0) return "—"
  const shown = top.slice(0, 3).map((c) => `${c.value} ${formatNumber(c.count)}`).join(" · ")
  return top.length > 3 ? `${shown}…` : shown
}

function ColumnRow({ col }: { col: ColumnProfile }) {
  const [expanded, setExpanded] = useState(false)
  // Only numeric columns have a distribution to show (S4).
  const expandable = col.type === "numeric"

  return (
    <>
      <tr className="border-b border-ln">
        <td className="py-1 pr-4 align-middle">
          {expandable ? (
            <button
              type="button"
              aria-expanded={expanded}
              onClick={() => setExpanded((v) => !v)}
              className="flex min-h-11 items-center gap-1.5 text-left font-medium text-fg hover:text-au"
            >
              {col.name}
              <span aria-hidden="true" className="text-xs text-f3">
                {expanded ? "▾" : "▸"}
              </span>
            </button>
          ) : (
            <span className="flex min-h-11 items-center text-fg">{col.name}</span>
          )}
        </td>
        <td className="py-1 pr-4 text-f2">{TYPE_LABELS[col.type] ?? col.type}</td>
        <td className="py-1 pr-4 text-right tabular-nums">
          {col.null_count > 0 ? (
            <span className="text-au">
              {formatNumber(col.null_count)} ({formatNumber(col.null_pct, 1)} %)
            </span>
          ) : (
            "0"
          )}
        </td>
        <td className="py-1 pr-4 text-right tabular-nums">{formatNumber(col.unique_count)}</td>
        <td className="py-1 text-f2">{summary(col)}</td>
      </tr>
      {expanded && expandable && (
        <tr className="border-b border-ln bg-s2">
          <td colSpan={5} className="px-3 py-2">
            <dl className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
              {[
                ["Mín.", col.min_val],
                ["P25", col.p25],
                ["Mediana", col.p50],
                ["P75", col.p75],
                ["Máx.", col.max_val],
              ].map(([label, value]) => (
                <div key={label as string} className="flex gap-2">
                  <dt className="text-f3">{label}</dt>
                  <dd className="font-medium tabular-nums text-fg">{fmt(value as number | undefined, 2)}</dd>
                </div>
              ))}
            </dl>
          </td>
        </tr>
      )}
    </>
  )
}

/** Every profiled column; numeric rows expand to their five-number summary. */
export function ColumnTable({ columns }: { columns: ColumnProfile[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-fg">
          <tr>
            <th className="py-2 pr-4 font-semibold">Columna</th>
            <th className="py-2 pr-4 font-semibold">Tipo</th>
            <th className="py-2 pr-4 text-right font-semibold">Nulos</th>
            <th className="py-2 pr-4 text-right font-semibold">Únicos</th>
            <th className="py-2 font-semibold">Resumen</th>
          </tr>
        </thead>
        <tbody>
          {columns.map((col) => (
            <ColumnRow key={col.name} col={col} />
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-f3">Pulsa una columna numérica para ver su distribución.</p>
    </div>
  )
}
