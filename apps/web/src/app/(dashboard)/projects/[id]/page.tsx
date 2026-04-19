"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import { useProject, useProjectDatasets, useUploadDataset, useAnalysisPoll } from "@/lib/queries"
import { api } from "@/lib/api"
import { Dropzone } from "@/components/upload/Dropzone"
import { ChartGrid } from "@/components/charts/ChartGrid"
import { InsightsPanel } from "@/components/insights/InsightsPanel"
import { PredictionsPanel } from "@/components/predictions/PredictionsPanel"
import type { ColumnProfile, DatasetWithAnalysis } from "@/types/api"

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

function ProfilingTable({ data }: { data: DatasetWithAnalysis }) {
  const { dataset, analysis } = data
  const profile = analysis.profile

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-6 rounded-xl border border-gray-800 bg-gray-900 p-5">
        <Stat label="Archivo" value={dataset.filename} />
        <Stat label="Filas" value={(profile?.row_count ?? dataset.row_count ?? 0).toLocaleString()} />
        <Stat label="Columnas" value={(profile?.column_count ?? dataset.column_count ?? 0).toString()} />
        <Stat label="Tamaño" value={`${(dataset.size_bytes / 1024).toFixed(1)} KB`} />
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

const STATUS_LABEL: Record<string, string> = {
  pending: "En cola...",
  running: "Analizando datos...",
  completed: "Completado",
  failed: "Error en el análisis",
}

export default function ProjectPage() {
  const params = useParams<{ id: string }>()
  const qc = useQueryClient()
  const { data: project } = useProject(params.id)
  const { data: datasets, isLoading } = useProjectDatasets(params.id)
  const upload = useUploadDataset(params.id)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)

  const latest = datasets?.[0]
  const latestAnalysis = latest?.analysis
  const isInProgress =
    latestAnalysis?.status === "pending" || latestAnalysis?.status === "running"

  const { data: polledAnalysis } = useAnalysisPoll(
    isInProgress ? latestAnalysis?.id : undefined
  )

  useEffect(() => {
    if (polledAnalysis?.status === "completed" || polledAnalysis?.status === "failed") {
      qc.invalidateQueries({ queryKey: ["projects", params.id, "datasets"] })
    }
  }, [polledAnalysis?.status, params.id, qc])

  const activeAnalysis = polledAnalysis ?? latestAnalysis
  const analyzing = activeAnalysis?.status === "pending" || activeAnalysis?.status === "running"

  async function handleDownloadPdf(analysisId: string, filename: string) {
    setDownloading(true)
    try {
      const blob = await api.downloadPdf(`/api/analyses/${analysisId}/report.pdf`)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `informe_${filename.replace(".csv", "")}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setDownloading(false)
    }
  }

  async function handleFile(file: File) {
    setUploadError(null)
    try {
      await upload.mutateAsync(file)
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Error al subir el archivo")
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/projects" className="text-sm text-gray-500 hover:text-gray-300">
          ← Proyectos
        </Link>
        <span className="text-gray-700">/</span>
        <h1 className="text-xl font-bold text-gray-100">{project?.name ?? "..."}</h1>
      </div>

      {isLoading ? (
        <p className="text-gray-500">Cargando...</p>
      ) : latest ? (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-gray-400">Dataset</h2>
            <div className="flex items-center gap-2">
              {activeAnalysis?.status === "completed" && activeAnalysis?.id && (
                <button
                  onClick={() => handleDownloadPdf(activeAnalysis.id, latest.dataset.filename)}
                  disabled={downloading}
                  className="rounded-lg border border-indigo-700 px-3 py-1.5 text-sm text-indigo-400 transition hover:border-indigo-500 hover:text-indigo-200 disabled:opacity-50"
                >
                  {downloading ? "Generando..." : "↓ Informe PDF"}
                </button>
              )}
              <label className="cursor-pointer rounded-lg border border-gray-700 px-3 py-1.5 text-sm text-gray-400 transition hover:border-gray-500 hover:text-gray-200">
                Subir nuevo CSV
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                  disabled={upload.isPending || analyzing}
                />
              </label>
            </div>
          </div>

          {uploadError && (
            <p className="rounded-lg bg-red-900/20 px-3 py-2 text-sm text-red-400">{uploadError}</p>
          )}

          {analyzing ? (
            <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-gray-800 bg-gray-900/50 py-16">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-700 border-t-indigo-500" />
              <p className="text-sm text-gray-400">
                {STATUS_LABEL[activeAnalysis?.status ?? "pending"]}
              </p>
            </div>
          ) : activeAnalysis?.status === "failed" ? (
            <div className="rounded-xl border border-red-900/50 bg-red-900/10 p-5">
              <p className="text-sm text-red-400">
                El análisis falló: {latestAnalysis?.status ?? "error desconocido"}
              </p>
            </div>
          ) : (
            <ProfilingTable data={{ dataset: latest.dataset, analysis: activeAnalysis ?? latest.analysis }} />
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            Sube un archivo CSV para obtener el perfilado automático del dataset.
          </p>
          <Dropzone onFile={handleFile} isLoading={upload.isPending} />
          {uploadError && (
            <p className="rounded-lg bg-red-900/20 px-3 py-2 text-sm text-red-400">{uploadError}</p>
          )}
        </div>
      )}
    </div>
  )
}
