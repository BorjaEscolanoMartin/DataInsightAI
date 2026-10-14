"use client"

import type { ReactNode } from "react"
import { ChartGrid } from "@/components/charts/ChartGrid"
import { hasInsights, InsightsPanel } from "@/components/insights/InsightsPanel"
import { hasPredictions, PredictionsPanel } from "@/components/predictions/PredictionsPanel"
import { formatNumber } from "@/lib/format"
import type { Analysis } from "@/types/api"
import { ColumnTable } from "./ColumnTable"

export interface AnalysisViewProps {
  filename: string
  sizeBytes: number
  rowCount: number | null
  columnCount: number | null
  analysis: Pick<Analysis, "profile" | "insights" | "predictions">
  /** Short line above the file name, in the accent («Demo · datos sintéticos»). */
  eyebrow?: string
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
          {profile?.date_column_candidate && (
            <Stat label="Columna de fecha" value={profile.date_column_candidate} highlight />
          )}
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
      <header className="space-y-3">
        {eyebrow && (
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-au">{eyebrow}</p>
        )}
        <h1 className="font-serif text-4xl leading-tight text-fg [overflow-wrap:anywhere] md:text-5xl">
          {filename}
        </h1>
        <p className="text-f2">
          Perfil, hallazgos y predicciones generados automáticamente a partir del CSV.
        </p>
      </header>

      {sections.map((section, i) => (
        <Section key={section.title} number={String(i + 1).padStart(2, "0")} {...section} />
      ))}

      {actions && (
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-t-2 border-fg pt-6">
          {actions}
        </div>
      )}
    </article>
  )
}

function Section({ number, title, context, content }: SectionSpec & { number: string }) {
  return (
    <section className="grid grid-cols-1 gap-6 border-t-2 border-fg pt-5 md:grid-cols-[200px_minmax(0,1fr)] md:gap-10">
      <div>
        <h2 className="font-serif leading-tight text-fg">
          <span className="block text-lg tabular-nums text-au">{number}</span>{" "}
          <span className="block text-2xl">{title}</span>
        </h2>
        {context && <p className="mt-2 text-sm text-f2">{context}</p>}
      </div>
      <div className="min-w-0">{content}</div>
    </section>
  )
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-f3">{label}</dt>
      <dd
        className={`mt-1 font-serif text-4xl tabular-nums [overflow-wrap:anywhere] ${highlight ? "text-au" : "text-fg"}`}
      >
        {value}
      </dd>
    </div>
  )
}
