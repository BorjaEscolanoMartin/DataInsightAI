import type { InsightItem } from "@/types/api"

interface Props {
  item: InsightItem
}

export function InsightCard({ item }: Props) {
  return (
    <article className="border-b border-ln py-4">
      <h4 className="font-serif text-xl leading-snug text-fg">{item.title}</h4>
      <p className="mt-1 text-[15px] leading-relaxed text-f2">{item.description}</p>
      {item.columns.length > 0 && (
        <p className="mt-2 text-xs text-f3">{item.columns.join(" · ")}</p>
      )}
    </article>
  )
}
