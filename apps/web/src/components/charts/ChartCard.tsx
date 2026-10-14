"use client"

interface Props {
  title: string
  children: React.ReactNode
}

export function ChartCard({ title, children }: Props) {
  return (
    <figure className="min-w-0 border-t border-ln pt-4">
      <figcaption className="mb-3 text-sm font-semibold text-fg">{title}</figcaption>
      {children}
    </figure>
  )
}
