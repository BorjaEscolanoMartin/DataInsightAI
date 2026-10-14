"use client"

interface Props {
  title: string
  /** A short line under the title, in the faint text colour (e.g. the histogram's outliers). */
  note?: string | null
  children: React.ReactNode
}

export function ChartCard({ title, note, children }: Props) {
  return (
    <figure className="min-w-0 border-t border-ln pt-4">
      <figcaption className="mb-3 text-sm font-semibold text-fg">
        {title}
        {note && <span className="mt-0.5 block text-xs font-normal text-f3">{note}</span>}
      </figcaption>
      {children}
    </figure>
  )
}
