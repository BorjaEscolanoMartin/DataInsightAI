import type { ReactNode } from "react"

export interface SectionProps {
  number: string
  title: string
  context?: string
  children: ReactNode
}

/** A numbered report section: 2 px ink rule, number in the accent and serif title on the left,
 *  content on the right; stacked on mobile (docs: odd/tasks/redesign.md, S1). */
export function Section({ number, title, context, children }: SectionProps) {
  return (
    <section className="grid grid-cols-1 gap-6 border-t-2 border-fg pt-5 md:grid-cols-[200px_minmax(0,1fr)] md:gap-10">
      <div>
        <h2 className="font-serif leading-tight text-fg">
          <span className="block text-lg tabular-nums text-au">{number}</span>{" "}
          <span className="block text-2xl">{title}</span>
        </h2>
        {context && <p className="mt-2 text-sm text-f2">{context}</p>}
      </div>
      <div className="min-w-0">{children}</div>
    </section>
  )
}
