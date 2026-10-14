"use client"

import { ChartGrid } from "@/components/charts/ChartGrid"
import { InsightsPanel } from "@/components/insights/InsightsPanel"
import { PredictionsPanel } from "@/components/predictions/PredictionsPanel"
import type { Analysis } from "@/types/api"
import { ColumnTable } from "./ColumnTable"

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

      {profile && <ColumnTable columns={profile.columns} />}
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
