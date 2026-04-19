"use client"

import type { PredictionsOut } from "@/types/api"
import { ForecastChart } from "./ForecastChart"
import { FeatureImportance } from "./FeatureImportance"

interface Props {
  predictions: PredictionsOut
}

export function PredictionsPanel({ predictions }: Props) {
  const { forecast, regression } = predictions
  const hasForecast = forecast && forecast.points.length > 0
  const hasRegression = regression && regression.feature_importance.length > 0
  if (!hasForecast && !hasRegression) return null

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-gray-400">
        Predicciones automáticas
        <span className="ml-2 rounded-full bg-violet-900/40 px-2 py-0.5 text-xs text-violet-300">
          ML
        </span>
      </h2>

      {hasForecast && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <h3 className="mb-3 text-sm font-semibold text-violet-300">
            Forecasting — serie temporal
          </h3>
          <ForecastChart forecast={forecast!} />
        </div>
      )}

      {hasRegression && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <h3 className="mb-3 text-sm font-semibold text-violet-300">
            Regresión baseline (RandomForest) — importancia de variables
          </h3>
          <FeatureImportance regression={regression!} />
        </div>
      )}
    </div>
  )
}
