import type { Insights } from "@/types/api"
import { InsightCard } from "./InsightCard"

interface Props {
  insights: Insights
}

// One accent only: trends in the accent, anomalies in ink, the rest secondary (S2).
const SECTIONS = [
  { key: "trends" as const, label: "Tendencias", color: "text-au" },
  { key: "anomalies" as const, label: "Anomalías", color: "text-fg" },
  { key: "correlations" as const, label: "Correlaciones", color: "text-f2" },
  { key: "recommendations" as const, label: "Recomendaciones", color: "text-f2" },
]

export function InsightsPanel({ insights }: Props) {
  const total = Object.values(insights).flat().length
  if (total === 0) return null

  return (
    <div className="space-y-4">
      <h2 className="font-serif text-2xl text-fg">Insights generados por IA</h2>

      <div className="grid grid-cols-1 gap-x-10 gap-y-8 md:grid-cols-2">
        {SECTIONS.map(({ key, label, color }) => {
          const items = insights[key]
          if (!items.length) return null
          return (
            <section key={key} className="min-w-0">
              <h3
                className={`border-b border-fg pb-2 text-xs font-semibold uppercase tracking-[0.06em] ${color}`}
              >
                {label}
              </h3>
              {items.map((item, i) => (
                <InsightCard key={i} item={item} />
              ))}
            </section>
          )
        })}
      </div>
    </div>
  )
}
