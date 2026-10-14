"use client"

import { useState } from "react"
import { ChevronIcon } from "@/components/ui/icons"
import { formatDateRange, formatNumber } from "@/lib/format"
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
  if (col.type === "date") return formatDateRange(col.min_date, col.max_date) ?? "—"
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

function detail(col: ColumnProfile, categories: { value: string; count: number }[]): [string, string][] {
  if (col.type === "numeric") {
    return [
      ["Mín.", fmt(col.min_val, 2)],
      ["P25", fmt(col.p25, 2)],
      ["Mediana", fmt(col.p50, 2)],
      ["P75", fmt(col.p75, 2)],
      ["Máx.", fmt(col.max_val, 2)],
    ]
  }
  return categories.map((c) => [c.value, formatNumber(c.count)])
}

function ColumnRow({ col }: { col: ColumnProfile }) {
  const [expanded, setExpanded] = useState(false)
  // Numeric columns show their five-number summary; categorical and boolean ones every category
  // with its count (S4). Date and text columns have nothing more to show.
  const categories = col.type === "categorical" || col.type === "boolean" ? (col.top_categories ?? []) : []
  const expandable = col.type === "numeric" || categories.length > 0

  return (
    <>
      <tr className="border-b border-ln">
        <td className="py-1 pr-4 align-middle">
          {expandable ? (
            <button
              type="button"
              aria-expanded={expanded}
              onClick={() => setExpanded((v) => !v)}
              className="flex min-h-11 items-center gap-3 text-left font-medium text-fg"
            >
              {/* The 36 px relief button is the visual; the whole 44 px row cell is the target. */}
              <span className="btn-row inline-flex size-9 shrink-0 items-center justify-center">
                <ChevronIcon className={expanded ? "rotate-90" : undefined} />
              </span>
              {col.name}
            </button>
          ) : (
            <span className="flex min-h-11 items-center gap-3 text-fg">
              <span aria-hidden="true" className="size-9 shrink-0" />
              {col.name}
            </span>
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
              {detail(col, categories).map(([label, value]) => (
                <div key={label} className="flex gap-2">
                  <dt className="text-f3">{label}</dt>
                  <dd className="font-medium tabular-nums text-fg">{value}</dd>
                </div>
              ))}
            </dl>
          </td>
        </tr>
      )}
    </>
  )
}

/** Every profiled column; numeric, categorical and boolean rows expand to their detail. */
export function ColumnTable({ columns }: { columns: ColumnProfile[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-fg">
          <tr>
            <th className="py-2 pr-4 pl-12 font-semibold">Columna</th>
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
    </div>
  )
}
