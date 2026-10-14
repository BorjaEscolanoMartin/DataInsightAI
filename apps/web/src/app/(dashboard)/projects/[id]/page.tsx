"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { useQueryClient } from "@tanstack/react-query"
import { useProject, useProjectDatasets, useUploadDataset, useAnalysisPoll } from "@/lib/queries"
import { api } from "@/lib/api"
import { Dropzone } from "@/components/upload/Dropzone"
import { AnalysisView } from "@/components/analysis/AnalysisView"
import { ReportHeader } from "@/components/ui/ReportHeader"
import { Section } from "@/components/ui/Section"
import { PRIMARY_BUTTON, SECONDARY_BUTTON } from "@/components/ui/styles"
import { formatNumber } from "@/lib/format"

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

  const crumb = (
    <>
      <Link href="/projects" className="underline-offset-4 hover:underline">
        Proyectos
      </Link>{" "}
      / {project?.name ?? "…"}
    </>
  )
  const errorNote = uploadError && (
    <p role="alert" className="border-l-2 border-fg pl-3 text-sm text-fg">
      {uploadError}
    </p>
  )
  const uploadNew = (
    <UploadNewCsv disabled={upload.isPending || analyzing} onFile={handleFile} />
  )

  if (isLoading) {
    return <p className="text-f2">Cargando...</p>
  }

  if (!latest) {
    return (
      <div className="space-y-14">
        <ReportHeader
          eyebrow={crumb}
          title="Sube un CSV y DataInsight prepara el informe por ti"
          lead="Perfil de cada columna, hallazgos redactados por Claude y, si hay una columna de fecha, una previsión."
        />
        <Section
          number="01"
          title="Subir datos"
          context="Una fila por registro y una cabecera con el nombre de cada columna."
        >
          <div className="space-y-3">
            <Dropzone onFile={handleFile} isLoading={upload.isPending} />
            <p className="text-sm text-f2">
              ¿No tienes uno a mano?{" "}
              <Link href="/demo" className="text-au underline underline-offset-4">
                Mira el análisis de ejemplo
              </Link>
              .
            </p>
            {errorNote}
          </div>
        </Section>
      </div>
    )
  }

  if (analyzing || activeAnalysis?.status === "failed") {
    const failed = !analyzing
    return (
      <div className="space-y-14">
        <ReportHeader
          eyebrow={crumb}
          title={project?.name ?? latest.dataset.filename}
          lead="El análisis se actualiza solo cuando termina."
        />
        <Section number="01" title="Estado">
          <div className="space-y-4">
            <div
              role="status"
              className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border-b border-ln pb-3"
            >
              <p className="min-w-0 [overflow-wrap:anywhere]">
                <span className="font-medium text-fg">{latest.dataset.filename}</span>{" "}
                <span className="text-sm text-f2">
                  {formatNumber(latest.dataset.size_bytes / 1024, 1, 1)} KB
                </span>
              </p>
              <p className={`text-sm font-semibold ${failed ? "text-fg" : "text-au"}`}>
                {STATUS_LABEL[activeAnalysis?.status ?? "pending"]}
              </p>
            </div>
            {failed && uploadNew}
            {errorNote}
          </div>
        </Section>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {errorNote}
      <AnalysisView
        filename={latest.dataset.filename}
        sizeBytes={latest.dataset.size_bytes}
        rowCount={latest.dataset.row_count}
        columnCount={latest.dataset.column_count}
        analysis={activeAnalysis ?? latest.analysis}
        eyebrow={crumb}
        actions={
          <>
            {uploadNew}
            {activeAnalysis?.status === "completed" && activeAnalysis.id && (
              <button
                type="button"
                onClick={() => handleDownloadPdf(activeAnalysis.id, latest.dataset.filename)}
                disabled={downloading}
                className={SECONDARY_BUTTON}
              >
                {downloading ? "Generando..." : "Descargar el informe en PDF"}
              </button>
            )}
          </>
        }
      />
    </div>
  )
}

/** File input behind a button-styled label; the input stays focusable (sr-only, not hidden). */
function UploadNewCsv({ disabled, onFile }: { disabled: boolean; onFile: (file: File) => void }) {
  return (
    <label
      className={`${PRIMARY_BUTTON} focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-au has-[:disabled]:opacity-50`}
    >
      Subir nuevo CSV
      <input
        type="file"
        accept=".csv"
        className="sr-only"
        onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
        disabled={disabled}
      />
    </label>
  )
}
