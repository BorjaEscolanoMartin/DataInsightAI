"use client"

import Link from "next/link"
import { useState } from "react"
import { AnalysisView } from "@/components/analysis/AnalysisView"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { Logo } from "@/components/ui/Logo"
import { Segmented } from "@/components/ui/Segmented"
import { PRIMARY_BUTTON, TEXT_LINK } from "@/components/ui/styles"
import { housingFixture, salesFixture } from "@/data/demo"

// Precomputed fixtures, imported statically: the page makes no request.
const EXAMPLES = {
  ventas: { label: "Ventas diarias · previsión", fixture: salesFixture },
  viviendas: { label: "Viviendas · regresión", fixture: housingFixture },
} as const

type ExampleId = keyof typeof EXAMPLES

const EXAMPLE_IDS = Object.keys(EXAMPLES) as ExampleId[]

export default function DemoPage() {
  // The first example (the order of EXAMPLES, which is also the button order) is the default.
  const [selected, setSelected] = useState<ExampleId>(EXAMPLE_IDS[0])
  const { fixture } = EXAMPLES[selected]

  return (
    <div className="min-h-screen">
      <header className="border-b border-fg">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-2">
          <Logo href="/demo" />
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link href="/login" className={TEXT_LINK}>
              Iniciar sesión
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-10">
        <p role="note" className="border-l-2 border-au pl-3 text-sm text-f2">
          Datos sintéticos: ambos conjuntos se han generado para esta demo y no corresponden a
          ningún negocio real.
        </p>

        <Segmented
          label="Conjunto de datos"
          options={EXAMPLE_IDS.map((id) => ({ value: id, label: EXAMPLES[id].label }))}
          value={selected}
          onChange={setSelected}
          stretchBelowSm
        />

        {/* A key per dataset resets the view's own state (expanded column rows). */}
        <AnalysisView
          key={selected}
          filename={fixture.filename}
          sizeBytes={fixture.size_bytes}
          rowCount={fixture.row_count}
          columnCount={fixture.column_count}
          analysis={fixture.analysis}
          eyebrow="Demo · datos sintéticos"
          actions={
            <Link href="/signup" className={PRIMARY_BUTTON}>
              Analiza tu propio CSV
            </Link>
          }
        />
      </main>
    </div>
  )
}
