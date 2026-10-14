import type { Insights } from "@/types/api"
import { InsightCard } from "./InsightCard"

interface Props {
  insights: Insights
}

// The four category titles share one style, in the accent (S20).
const SECTIONS = [
  { key: "trends" as const, label: "Tendencias" },
  { key: "anomalies" as const, label: "Anomalías" },
  { key: "correlations" as const, label: "Correlaciones" },
  { key: "recommendations" as const, label: "Recomendaciones" },
]

export function hasInsights(insights: Insights | null | undefined): insights is Insights {
  return !!insights && Object.values(insights).flat().length > 0
}

export function InsightsPanel({ insights }: Props) {
  if (!hasInsights(insights)) return null

  return (
    <div>
      <div className="grid grid-cols-1 gap-x-10 gap-y-8 md:grid-cols-2">
        {SECTIONS.map(({ key, label }) => {
          const items = insights[key]
          if (!items.length) return null
          return (
            <section key={key} className="min-w-0">
              <h3
                className="border-b border-fg pb-2 text-xs font-semibold uppercase tracking-[0.06em] text-au"
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
