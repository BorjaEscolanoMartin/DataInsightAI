"use client"

interface Props {
  title: string
  children: React.ReactNode
}

export function ChartCard({ title, children }: Props) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <h3 className="mb-4 text-sm font-medium text-gray-300">{title}</h3>
      {children}
    </div>
  )
}
