"use client"

import type { ReactNode } from "react"
import { ChartGrid } from "@/components/charts/ChartGrid"
import { hasInsights, InsightsPanel } from "@/components/insights/InsightsPanel"
import { hasPredictions, PredictionsPanel } from "@/components/predictions/PredictionsPanel"
import { ReportHeader } from "@/components/ui/ReportHeader"
import { Section } from "@/components/ui/Section"
import { formatDateRange, formatNumber } from "@/lib/format"
import type { Analysis } from "@/types/api"
import { ColumnTable } from "./ColumnTable"

export interface AnalysisViewProps {
  filename: string
  sizeBytes: number
  rowCount: number | null
  columnCount: number | null
  analysis: Pick<Analysis, "profile" | "insights" | "predictions">
  /** Short line above the file name, in the accent («Demo · datos sintéticos»). */
  eyebrow?: ReactNode
  /** Calls to action shown after the last section. */
  actions?: ReactNode
}

interface SectionSpec {
  title: string
  context?: string
  content: ReactNode
}

/** The analysis of one dataset as an editorial report: header, numbered sections, actions. */
export function AnalysisView({
  filename,
  sizeBytes,
  rowCount,
  columnCount,
  analysis,
  eyebrow,
  actions,
}: AnalysisViewProps) {
  const { profile, insights, predictions } = analysis

  const sections: SectionSpec[] = [
    {
      title: "Dataset",
      content: (
        <dl className="grid grid-cols-2 gap-x-8 gap-y-6 md:grid-cols-4">
          <Stat label="Filas" value={formatNumber(profile?.row_count ?? rowCount ?? 0)} />
          <Stat label="Columnas" value={formatNumber(profile?.column_count ?? columnCount ?? 0)} />
          <Stat label="Tamaño" value={`${formatNumber(sizeBytes / 1024, 1, 1)} KB`} />
          {profile?.date_column_candidate && <DateStat profile={profile} />}
        </dl>
      ),
    },
  ]
  if (hasInsights(insights)) {
    sections.push({
      title: "Hallazgos",
      context: "Redactados por Claude a partir de los datos del CSV.",
      content: <InsightsPanel insights={insights} />,
    })
  }
  if (hasPredictions(predictions)) {
    sections.push({ title: "Predicciones", content: <PredictionsPanel predictions={predictions} /> })
  }
  if (profile && profile.charts.length > 0) {
    sections.push({
      title: "Gráficos",
      context: "Elegidos automáticamente según el tipo de cada columna.",
      content: <ChartGrid charts={profile.charts} />,
    })
  }
  if (profile) {
    sections.push({
      title: "Columnas",
      context: "Pulsa el nombre de una columna para ver su detalle.",
      content: <ColumnTable columns={profile.columns} />,
    })
  }

  return (
    <article className="space-y-14">
      <ReportHeader
        eyebrow={eyebrow}
        title={filename}
        lead="Perfil, hallazgos y predicciones generados automáticamente a partir del CSV."
        rule
      />

      {sections.map(({ title, context, content }, i) => (
        <Section key={title} number={String(i + 1).padStart(2, "0")} title={title} context={context}>
          {content}
        </Section>
      ))}

      {actions && (
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-t-2 border-fg pt-6">
          {actions}
        </div>
      )}
    </article>
  )
}

/** «Periodo» with the detected date column's range and its name below; an analysis without the
 *  range (older ones) keeps «Columna de fecha» (S2, S4). */
function DateStat({ profile }: { profile: NonNullable<Analysis["profile"]> }) {
  const name = profile.date_column_candidate!
  const column = profile.columns.find((c) => c.name === name)
  const range = formatDateRange(column?.min_date, column?.max_date)
  if (!range) return <Stat label="Columna de fecha" value={name} highlight />
  return <Stat label="Periodo" value={range} note={`columna ${name}`} highlight small />
}

function Stat({
  label,
  value,
  highlight,
  note,
  small,
}: {
  label: string
  value: string
  highlight?: boolean
  note?: string
  small?: boolean
}) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-f3">{label}</dt>
      <dd
        className={`mt-1 font-serif tabular-nums [overflow-wrap:anywhere] ${small ? "text-2xl" : "text-4xl"} ${highlight ? "text-au" : "text-fg"}`}
      >
        {value}
      </dd>
      {note && <dd className="mt-1 text-xs text-f3">{note}</dd>}
    </div>
  )
}
