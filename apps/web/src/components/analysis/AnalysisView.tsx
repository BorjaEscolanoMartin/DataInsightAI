"use client"

import { useState } from "react"
import { ChartGrid } from "@/components/charts/ChartGrid"
import { InsightsPanel } from "@/components/insights/InsightsPanel"
import { PredictionsPanel } from "@/components/predictions/PredictionsPanel"
import type { Analysis, ColumnProfile } from "@/types/api"

const TYPE_COLORS: Record<string, string> = {
  numeric: "bg-blue-900/40 text-blue-300",
  categorical: "bg-purple-900/40 text-purple-300",
  date: "bg-green-900/40 text-green-300",
  text: "bg-yellow-900/40 text-yellow-300",
  boolean: "bg-orange-900/40 text-orange-300",
}

function fmt(n: number | undefined, decimals = 2): string {
  if (n === undefined || n === null) return "—"
  return n.toLocaleString("es-ES", { maximumFractionDigits: decimals })
}

function ColumnRow({ col }: { col: ColumnProfile }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <>
      <tr
        className="cursor-pointer border-b border-gray-800 hover:bg-gray-800/50"
        onClick={() => setExpanded((v) => !v)}
      >
        <td className="px-4 py-3 font-mono text-sm text-gray-200">{col.name}</td>
        <td className="px-4 py-3">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${TYPE_COLORS[col.type] ?? ""}`}>
            {col.type}
          </span>
        </td>
        <td className="px-4 py-3 text-right text-sm text-gray-400">
          {col.null_pct.toFixed(1)}%
          {col.null_count > 0 && (
            <span className="ml-1 text-xs text-gray-600">({col.null_count})</span>
          )}
        </td>
        <td className="px-4 py-3 text-right text-sm text-gray-400">{col.unique_count.toLocaleString()}</td>
        <td className="px-4 py-3 text-sm text-gray-500">
          {col.type === "numeric" && (
            <span>
              μ {fmt(col.mean)} · σ {fmt(col.std)}
            </span>
          )}
          {(col.type === "categorical" || col.type === "boolean") &&
            col.top_categories
              ?.slice(0, 3)
              .map((c) => c.value)
              .join(", ")}
        </td>
      </tr>
      {expanded && col.type === "numeric" && (
        <tr className="border-b border-gray-800 bg-gray-900/50">
          <td colSpan={5} className="px-8 py-3">
            <div className="flex flex-wrap gap-6 text-xs text-gray-400">
              <span>Min: <strong className="text-gray-200">{fmt(col.min_val)}</strong></span>
              <span>P25: <strong className="text-gray-200">{fmt(col.p25)}</strong></span>
              <span>P50: <strong className="text-gray-200">{fmt(col.p50)}</strong></span>
              <span>P75: <strong className="text-gray-200">{fmt(col.p75)}</strong></span>
              <span>Max: <strong className="text-gray-200">{fmt(col.max_val)}</strong></span>
              {(col.outlier_count ?? 0) > 0 && (
                <span className="text-amber-400">⚠ {col.outlier_count} outliers (IQR)</span>
              )}
            </div>
          </td>
        </tr>
      )}
      {expanded && col.top_categories && (
        <tr className="border-b border-gray-800 bg-gray-900/50">
          <td colSpan={5} className="px-8 py-3">
            <div className="flex flex-wrap gap-2">
              {col.top_categories.map((c) => (
                <span key={c.value} className="rounded bg-gray-800 px-2 py-0.5 text-xs text-gray-300">
                  {c.value} <span className="text-gray-500">({c.count})</span>
                </span>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export interface AnalysisViewProps {
  filename: string
  sizeBytes: number
  rowCount: number | null
  columnCount: number | null
  analysis: Pick<Analysis, "profile" | "insights" | "predictions">
}

/** The analysis of one dataset: summary, insights, predictions, charts and column profiling. */
export function AnalysisView({ filename, sizeBytes, rowCount, columnCount, analysis }: AnalysisViewProps) {
  const profile = analysis.profile

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-6 rounded-xl border border-gray-800 bg-gray-900 p-5">
        <Stat label="Archivo" value={filename} />
        <Stat label="Filas" value={(profile?.row_count ?? rowCount ?? 0).toLocaleString()} />
        <Stat label="Columnas" value={(profile?.column_count ?? columnCount ?? 0).toString()} />
        <Stat label="Tamaño" value={`${(sizeBytes / 1024).toFixed(1)} KB`} />
        {profile?.date_column_candidate && (
          <Stat label="Columna fecha" value={profile.date_column_candidate} highlight />
        )}
      </div>

      {analysis.insights && <InsightsPanel insights={analysis.insights} />}

      {analysis.predictions && <PredictionsPanel predictions={analysis.predictions} />}

      {profile?.charts && profile.charts.length > 0 && (
        <ChartGrid charts={profile.charts} />
      )}

      {profile && (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-left">
            <thead className="border-b border-gray-800 bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">Columna</th>
                <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">Tipo</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Nulos</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Únicos</th>
                <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">Resumen</th>
              </tr>
            </thead>
            <tbody>
              {profile.columns.map((col) => (
                <ColumnRow key={col.name} col={col} />
              ))}
            </tbody>
          </table>
          <p className="px-4 py-2 text-xs text-gray-600">Haz clic en una fila para ver más detalles</p>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-sm font-semibold ${highlight ? "text-indigo-400" : "text-gray-200"}`}>
        {value}
      </p>
    </div>
  )
}
