"use client"

import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts"
import { AXIS_LINE, AXIS_TICK, GRID_STROKE, TOOLTIP_PROPS } from "@/components/charts/chartTheme"
import { horizonText, targetText } from "@/lib/forecast"
import type { ForecastOut } from "@/types/api"

interface Props {
  forecast: ForecastOut
}

export function ForecastChart({ forecast }: Props) {
  const data = forecast.points.map((p) => ({
    ds: p.ds,
    yhat: +p.yhat.toFixed(2),
    band: [+p.yhat_lower.toFixed(2), +p.yhat_upper.toFixed(2)] as [number, number],
  }))

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-baseline gap-x-5 gap-y-1 text-sm text-f2">
        {forecast.wape != null && (
          <span>
            WAPE backtest:{" "}
            <strong className="font-serif text-2xl font-medium tabular-nums text-fg">
              {forecast.wape.toFixed(1)}%
            </strong>
          </span>
        )}
        {forecast.mape != null && (
          <span>
            MAPE backtest:{" "}
            <strong className="font-serif text-2xl font-medium tabular-nums text-fg">
              {forecast.mape.toFixed(1)}%
            </strong>
          </span>
        )}
        {forecast.mae != null && (
          <span>
            MAE: <strong className="font-medium tabular-nums text-fg">{forecast.mae.toFixed(1)}</strong>
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-f3">
        <span>
          Objetivo: <strong className="font-medium text-f2">{targetText(forecast)}</strong>
        </span>
        <span>
          Fecha: <strong className="font-medium text-f2">{forecast.date_column}</strong>
        </span>
        <span>
          Horizonte: <strong className="font-medium text-f2">{horizonText(forecast)}</strong>
        </span>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={GRID_STROKE} vertical={false} />
          <XAxis
            dataKey="ds"
            tick={AXIS_TICK}
            axisLine={AXIS_LINE}
            tickLine={false}
            interval="preserveStartEnd"
            minTickGap={32}
          />
          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={60} />
          <Tooltip {...TOOLTIP_PROPS} />
          <Legend wrapperStyle={{ fontSize: 12, color: "var(--f2)" }} />
          <Area
            type="monotone"
            dataKey="band"
            fill="var(--au)"
            fillOpacity={0.14}
            stroke="none"
            name="Intervalo del 95 %"
          />
          <Line
            type="monotone"
            dataKey="yhat"
            stroke="var(--au)"
            strokeWidth={1.5}
            dot={false}
            name="Previsión"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
