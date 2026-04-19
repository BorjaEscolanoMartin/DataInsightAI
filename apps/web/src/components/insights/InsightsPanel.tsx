"use client"

import { useState } from "react"
import type { Insights } from "@/types/api"
import { InsightCard } from "./InsightCard"

interface Props {
  insights: Insights
}

const SECTIONS = [
  { key: "trends"          as const, label: "Tendencias",      color: "text-blue-400"   },
  { key: "anomalies"       as const, label: "Anomalías",       color: "text-amber-400"  },
  { key: "correlations"    as const, label: "Correlaciones",   color: "text-purple-400" },
  { key: "recommendations" as const, label: "Recomendaciones", color: "text-green-400"  },
]

export function InsightsPanel({ insights }: Props) {
  const [open, setOpen] = useState<Record<string, boolean>>({
    trends: true,
    anomalies: true,
    correlations: true,
    recommendations: true,
  })

  const total = Object.values(insights).flat().length
  if (total === 0) return null

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-gray-400">
        Insights generados por IA
        <span className="ml-2 rounded-full bg-indigo-900/40 px-2 py-0.5 text-xs text-indigo-300">
          {total}
        </span>
      </h2>

      {SECTIONS.map(({ key, label, color }) => {
        const items = insights[key]
        if (!items.length) return null
        const isOpen = open[key]
        return (
          <div key={key} className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
            <button
              onClick={() => setOpen((s) => ({ ...s, [key]: !s[key] }))}
              className="flex w-full items-center justify-between px-5 py-3 hover:bg-gray-800/50 transition-colors"
            >
              <span className={`text-sm font-semibold ${color}`}>
                {label}
                <span className="ml-2 text-xs text-gray-500">({items.length})</span>
              </span>
              <span className="text-gray-600 text-xs">{isOpen ? "▲" : "▼"}</span>
            </button>
            {isOpen && (
              <div className="grid gap-3 px-5 pb-5 sm:grid-cols-2">
                {items.map((item, i) => (
                  <InsightCard key={i} item={item} category={key} />
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
