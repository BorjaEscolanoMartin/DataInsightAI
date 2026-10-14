import type { ReactNode } from "react"

interface Props {
  /** Short line above the title, in the accent. */
  eyebrow?: ReactNode
  title: string
  lead: string
  /** The gold rule under the header of the analysis view (S19). */
  rule?: boolean
}

export function ReportHeader({ eyebrow, title, lead, rule }: Props) {
  return (
    <header className="space-y-3">
      {eyebrow && (
        <p className="text-xs font-semibold uppercase tracking-[0.08em] text-au">{eyebrow}</p>
      )}
      <h1 className="font-serif text-4xl leading-tight text-fg [overflow-wrap:anywhere] md:text-5xl">
        {title}
      </h1>
      <p className="max-w-2xl text-f2">{lead}</p>
      {rule && <div aria-hidden="true" className="gold-rule !mt-6" />}
    </header>
  )
}
