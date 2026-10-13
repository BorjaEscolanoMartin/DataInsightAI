"use client"

import Link from "next/link"
import { useState } from "react"
import { AnalysisView, type AnalysisViewProps } from "@/components/analysis/AnalysisView"
import ventas from "@/data/demo/ventas.json"
import viviendas from "@/data/demo/viviendas.json"

// Precomputed by apps/api/demo/generate_demo_fixture.py: the page makes no request.
interface DemoFixture {
  filename: string
  size_bytes: number
  row_count: number | null
  column_count: number | null
  analysis: AnalysisViewProps["analysis"]
}

const EXAMPLES = [
  { id: "ventas", label: "Ventas diarias · previsión", fixture: ventas as DemoFixture },
  { id: "viviendas", label: "Viviendas · regresión", fixture: viviendas as DemoFixture },
]

export default function DemoPage() {
  const [selected, setSelected] = useState(EXAMPLES[0].id)
  const { fixture } = EXAMPLES.find((example) => example.id === selected) ?? EXAMPLES[0]

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
          {EXAMPLES.map((example) => (
            <button
              key={example.id}
              type="button"
              aria-pressed={example.id === selected}
              onClick={() => setSelected(example.id)}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                example.id === selected
                  ? "bg-indigo-600 text-white"
                  : "border border-gray-700 text-gray-300 hover:bg-gray-800"
              }`}
            >
              {example.label}
            </button>
          ))}
        </div>

        <AnalysisView
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
