"use client"

import type { ChartSpec } from "@/types/api"
import { ChartCard } from "./ChartCard"
import { HistogramChart } from "./HistogramChart"
import { histogramView, type HistogramDatum } from "./histogram"
import { CategoricalBarChart, ValueColumnChart } from "./BarChartComp"
import { isValueBars } from "./bars"
import { TimeSeriesChart } from "./LineChartComp"
import { HeatmapChart } from "./HeatmapChart"
import { ScatterChartComp } from "./ScatterChartComp"

interface Props {
  charts: ChartSpec[]
}

export function ChartGrid({ charts }: Props) {
  if (!charts.length) return null

  // The time series go first, at full width; the rest share the grid below.
  const ordered = [
    ...charts.filter((c) => c.type === "line"),
    ...charts.filter((c) => c.type !== "line"),
  ]

  return (
    <div>
      {/* grid-cols-1 is not a no-op: it gives the mobile column a minmax(0, 1fr) track, so a wide
          chart (the correlation heatmap) scrolls inside its block instead of widening the page. */}
      <div className="grid grid-cols-1 gap-x-8 gap-y-8 md:grid-cols-2 xl:grid-cols-3">
        {ordered.map((chart) => {
          switch (chart.type) {
            case "histogram": {
              const view = histogramView(chart.data as unknown as HistogramDatum[])
              return (
                <ChartCard key={chart.id} title={chart.title} note={view.note}>
                  <HistogramChart view={view} />
                </ChartCard>
              )
            }
            case "bar":
              return (
                <ChartCard key={chart.id} title={chart.title}>
                  {isValueBars(chart) ? (
                    <ValueColumnChart data={chart.data as { name: string; count: number }[]} />
                  ) : (
                    <CategoricalBarChart data={chart.data as { name: string; count: number }[]} />
                  )}
                </ChartCard>
              )
            case "line":
              return (
                <div key={chart.id} className="col-span-full">
                  <ChartCard title={chart.title}>
                    <TimeSeriesChart
                      data={chart.data as { date: string; value: number | null }[]}
                      yColumn={chart.y_column ?? ""}
                    />
                  </ChartCard>
                </div>
              )
            case "heatmap":
              return (
                <ChartCard key={chart.id} title={chart.title}>
                  <HeatmapChart
                    columns={chart.columns ?? []}
                    data={chart.data as { x: string; y: string; value: number }[]}
                  />
                </ChartCard>
              )
            case "scatter":
              return (
                <ChartCard key={chart.id} title={chart.title}>
                  <ScatterChartComp
                    data={chart.data as { x: number | null; y: number | null }[]}
                    xCol={chart.x_column ?? "x"}
                    yCol={chart.y_column ?? "y"}
                  />
                </ChartCard>
              )
            default:
              return null
          }
        })}
      </div>
    </div>
  )
}
