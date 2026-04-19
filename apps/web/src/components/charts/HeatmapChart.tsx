"use client"

interface HeatmapDatum {
  x: string
  y: string
  value: number
}

interface Props {
  columns: string[]
  data: HeatmapDatum[]
}

function corrColor(value: number): string {
  const abs = Math.abs(value)
  if (value >= 0) {
    return `rgba(99,102,241,${(0.15 + abs * 0.85).toFixed(2)})`
  }
  return `rgba(239,68,68,${(0.15 + abs * 0.85).toFixed(2)})`
}

function textColor(value: number): string {
  return Math.abs(value) > 0.5 ? "#f9fafb" : "#9ca3af"
}

export function HeatmapChart({ columns, data }: Props) {
  const lookup = new Map(data.map((d) => [`${d.x}||${d.y}`, d.value]))
  const cellSize = Math.max(32, Math.min(56, Math.floor(480 / columns.length)))
  const labelWidth = 80

  return (
    <div className="overflow-x-auto">
      <div style={{ minWidth: labelWidth + columns.length * cellSize }}>
        {/* Column headers */}
        <div className="flex" style={{ marginLeft: labelWidth }}>
          {columns.map((col) => (
            <div
              key={col}
              className="truncate text-center text-xs text-gray-500"
              style={{ width: cellSize, fontSize: 9 }}
              title={col}
            >
              {col.length > 8 ? col.slice(0, 7) + "…" : col}
            </div>
          ))}
        </div>

        {/* Rows */}
        {columns.map((rowCol) => (
          <div key={rowCol} className="flex items-center">
            <div
              className="truncate text-right text-xs text-gray-400 pr-2"
              style={{ width: labelWidth, fontSize: 10 }}
              title={rowCol}
            >
              {rowCol.length > 10 ? rowCol.slice(0, 9) + "…" : rowCol}
            </div>
            {columns.map((colCol) => {
              const val = lookup.get(`${rowCol}||${colCol}`) ?? 0
              return (
                <div
                  key={colCol}
                  className="flex items-center justify-center rounded-sm text-xs font-medium"
                  style={{
                    width: cellSize,
                    height: cellSize,
                    backgroundColor: corrColor(val),
                    color: textColor(val),
                    fontSize: cellSize < 40 ? 8 : 10,
                  }}
                  title={`${rowCol} × ${colCol}: ${val.toFixed(2)}`}
                >
                  {val.toFixed(2)}
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
