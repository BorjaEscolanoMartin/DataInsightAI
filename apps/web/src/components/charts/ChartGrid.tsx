"use client"

import type { ChartSpec } from "@/types/api"
import { ChartCard } from "./ChartCard"
import { HistogramChart } from "./HistogramChart"
import { CategoricalBarChart } from "./BarChartComp"
import { TimeSeriesChart } from "./LineChartComp"
import { HeatmapChart } from "./HeatmapChart"
import { ScatterChartComp } from "./ScatterChartComp"

interface Props {
  charts: ChartSpec[]
}

export function ChartGrid({ charts }: Props) {
  if (!charts.length) return null

  return (
    <div>
      <h2 className="mb-4 text-sm font-medium text-gray-400">Visualizaciones automáticas</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {charts.map((chart) => {
          switch (chart.type) {
            case "histogram":
              return (
                <ChartCard key={chart.id} title={chart.title}>
                  <HistogramChart data={chart.data as { bin: string; count: number }[]} />
                </ChartCard>
              )
            case "bar":
              return (
                <ChartCard key={chart.id} title={chart.title}>
                  <CategoricalBarChart data={chart.data as { name: string; count: number }[]} />
                </ChartCard>
              )
            case "line":
              return (
                <ChartCard key={chart.id} title={chart.title}>
                  <TimeSeriesChart
                    data={chart.data as { date: string; value: number | null }[]}
                    yColumn={chart.y_column ?? ""}
                  />
                </ChartCard>
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
