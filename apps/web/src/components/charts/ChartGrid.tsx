"use client"

import type { ChartSpec } from "@/types/api"
import { ChartCard } from "./ChartCard"
import { HistogramChart } from "./HistogramChart"
import { histogramView, type HistogramDatum } from "./histogram"
import { CategoricalBarChart, ValueColumnChart } from "./BarChartComp"
import { isValueBars } from "./bars"
import { TimeSeriesChart } from "./LineChartComp"
import { HeatmapChart, isWideHeatmap } from "./HeatmapChart"
import { ScatterChartComp } from "./ScatterChartComp"
import { lastSpanClass } from "./grid"

interface Props {
  charts: ChartSpec[]
}

/** Charts that take a whole row: the time series and a heatmap of many variables. */
function isFullWidth(chart: ChartSpec): boolean {
  return chart.type === "line" || (chart.type === "heatmap" && isWideHeatmap(chart.columns ?? []))
}

/** How each chart type is drawn. A type missing here is not drawn, nor counted in the grid. */
const RENDERERS: Record<ChartSpec["type"], (chart: ChartSpec) => React.ReactNode> = {
  histogram: (chart) => {
    const view = histogramView(chart.data as unknown as HistogramDatum[])
    return (
      <ChartCard title={chart.title} note={view.note}>
        <HistogramChart view={view} />
      </ChartCard>
    )
  },
  bar: (chart) => (
    <ChartCard title={chart.title}>
      {isValueBars(chart) ? (
        <ValueColumnChart data={chart.data as { name: string; count: number }[]} />
      ) : (
        <CategoricalBarChart data={chart.data as { name: string; count: number }[]} />
      )}
    </ChartCard>
  ),
  line: (chart) => (
    <ChartCard title={chart.title}>
      <TimeSeriesChart
        data={chart.data as { date: string; value: number | null }[]}
        yColumn={chart.y_column ?? ""}
      />
    </ChartCard>
  ),
  heatmap: (chart) => (
    <ChartCard title={chart.title}>
      <HeatmapChart
        columns={chart.columns ?? []}
        data={chart.data as { x: string; y: string; value: number }[]}
      />
    </ChartCard>
  ),
  scatter: (chart) => (
    <ChartCard title={chart.title}>
      <ScatterChartComp
        data={chart.data as { x: number | null; y: number | null }[]}
        xCol={chart.x_column ?? "x"}
        yCol={chart.y_column ?? "y"}
      />
    </ChartCard>
  ),
}

function isDrawn(chart: ChartSpec): boolean {
  return Object.hasOwn(RENDERERS, chart.type)
}

function ChartBlock({ chart }: { chart: ChartSpec }) {
  return RENDERERS[chart.type](chart)
}

export function ChartGrid({ charts }: Props) {
  // Only charts this page can draw take a place in the grid.
  const drawn = charts.filter(isDrawn)
  if (!drawn.length) return null

  // The time series first, then the small charts in the API's order, then the other wide charts,
  // so no wide chart breaks a row of small ones (W6).
  const lines = drawn.filter((c) => c.type === "line")
  const small = drawn.filter((c) => !isFullWidth(c))
  const wide = drawn.filter((c) => isFullWidth(c) && c.type !== "line")
  const lastSmall = lastSpanClass(small.length)

  return (
    <div>
      {/* grid-cols-1 is not a no-op: it gives the mobile column a minmax(0, 1fr) track, so a wide
          chart (the correlation heatmap) scrolls inside its block instead of widening the page. */}
      <div className="grid grid-cols-1 gap-x-8 gap-y-8 md:grid-cols-2 xl:grid-cols-3">
        {lines.map((chart) => (
          <div key={chart.id} className="col-span-full">
            <ChartBlock chart={chart} />
          </div>
        ))}
        {small.map((chart, i) =>
          i === small.length - 1 && lastSmall ? (
            <div key={chart.id} className={lastSmall}>
              <ChartBlock chart={chart} />
            </div>
          ) : (
            <ChartBlock key={chart.id} chart={chart} />
          ),
        )}
        {wide.map((chart) => (
          <div key={chart.id} className="col-span-full">
            <ChartBlock chart={chart} />
          </div>
        ))}
      </div>
    </div>
  )
}
