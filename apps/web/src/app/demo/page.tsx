"use client"

import Link from "next/link"
import { useState } from "react"
import { AnalysisView } from "@/components/analysis/AnalysisView"
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
    <div className="min-h-screen bg-gray-950">
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <span className="text-lg font-bold">
            DataInsight <span className="text-indigo-400">AI</span>
            <span className="ml-2 text-sm font-normal text-gray-400">Demo</span>
          </span>
          <Link href="/login" className="text-sm text-indigo-400 hover:underline">
            Iniciar sesión
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <p
          role="note"
          className="rounded-lg border border-amber-800 bg-amber-950/40 px-4 py-3 text-sm text-amber-300"
        >
          Datos sintéticos: ambos conjuntos se han generado para esta demo y no corresponden a
          ningún negocio real.
        </p>

        <div className="flex flex-wrap gap-2" role="group" aria-label="Conjunto de datos">
          {EXAMPLE_IDS.map((id) => (
            <button
              key={id}
              type="button"
              aria-pressed={id === selected}
              onClick={() => setSelected(id)}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                id === selected
                  ? "bg-indigo-600 text-white"
                  : "border border-gray-700 text-gray-300 hover:bg-gray-800"
              }`}
            >
              {EXAMPLES[id].label}
            </button>
          ))}
        </div>

        {/* A key per dataset resets the view's own state (expanded column rows). */}
        <AnalysisView
          key={selected}
          filename={fixture.filename}
          sizeBytes={fixture.size_bytes}
          rowCount={fixture.row_count}
          columnCount={fixture.column_count}
          analysis={fixture.analysis}
        />
      </main>
    </div>
  )
}
