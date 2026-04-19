import type { InsightItem } from "@/types/api"

interface Props {
  item: InsightItem
  category: "trends" | "anomalies" | "correlations" | "recommendations"
}

const STYLES = {
  trends:         "border-blue-800/50   bg-blue-900/10   text-blue-300",
  anomalies:      "border-amber-800/50  bg-amber-900/10  text-amber-300",
  correlations:   "border-purple-800/50 bg-purple-900/10 text-purple-300",
  recommendations:"border-green-800/50  bg-green-900/10  text-green-300",
}

const ICONS = {
  trends:         "↗",
  anomalies:      "⚡",
  correlations:   "⟷",
  recommendations:"→",
}

export function InsightCard({ item, category }: Props) {
  return (
    <div className={`rounded-lg border p-4 ${STYLES[category]}`}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5 text-lg leading-none">{ICONS[category]}</span>
        <div className="min-w-0">
          <p className="font-semibold">{item.title}</p>
          <p className="mt-1 text-sm opacity-80">{item.description}</p>
          {item.columns.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {item.columns.map((col) => (
                <span
                  key={col}
                  className="rounded bg-black/20 px-1.5 py-0.5 font-mono text-xs"
                >
                  {col}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
