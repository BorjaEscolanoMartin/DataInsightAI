"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import { useProject, useProjectDatasets, useUploadDataset, useAnalysisPoll } from "@/lib/queries"
import { api } from "@/lib/api"
import { Dropzone } from "@/components/upload/Dropzone"
import { AnalysisView } from "@/components/analysis/AnalysisView"

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
            <AnalysisView
              filename={latest.dataset.filename}
              sizeBytes={latest.dataset.size_bytes}
              rowCount={latest.dataset.row_count}
              columnCount={latest.dataset.column_count}
              analysis={activeAnalysis ?? latest.analysis}
            />
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
