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
import { formatNumber } from "@/lib/format"
import type { ForecastOut } from "@/types/api"
import { useReducedMotion } from "@/lib/motion"

interface Props {
  forecast: ForecastOut
}

/** The band's level is only known for analyses with the new fields (wape): older ones used a
 *  band that was not calibrated (S16). */
export function forecastBandLabel(forecast: ForecastOut): string {
  return forecast.wape != null ? "Intervalo del 95 %" : "Intervalo"
}

/** Tooltip value: the band as «lower – upper», any other series as one number. */
export function formatForecastValue(value: number | [number, number]): string {
  return Array.isArray(value)
    ? `${formatNumber(value[0])} – ${formatNumber(value[1])}`
    : formatNumber(value)
}

export function ForecastChart({ forecast }: Props) {
  const reducedMotion = useReducedMotion()
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
            WAPE del backtest:{" "}
            <strong className="font-serif text-2xl font-medium tabular-nums text-fg">
              {formatNumber(forecast.wape, 1, 1)} %
            </strong>
          </span>
        )}
        {forecast.mape != null && (
          <span>
            MAPE del backtest:{" "}
            <strong className="font-serif text-2xl font-medium tabular-nums text-fg">
              {formatNumber(forecast.mape, 1, 1)} %
            </strong>
          </span>
        )}
        {forecast.mae != null && (
          <span>
            MAE: <strong className="font-medium tabular-nums text-fg">{formatNumber(forecast.mae, 1, 1)}</strong>
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
          <Tooltip
            {...TOOLTIP_PROPS}
            formatter={(value) => formatForecastValue(value as number | [number, number])}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: "var(--f2)" }} />
          <Area
            isAnimationActive={!reducedMotion}
            type="monotone"
            dataKey="band"
            fill="var(--au)"
            fillOpacity={0.14}
            stroke="none"
            name={forecastBandLabel(forecast)}
          />
          <Line
            isAnimationActive={!reducedMotion}
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
