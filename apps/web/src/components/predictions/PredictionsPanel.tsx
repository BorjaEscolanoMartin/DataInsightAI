"use client"

import { nextHorizonText } from "@/lib/forecast"
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
    <div className="space-y-8">
      <h2 className="font-serif text-2xl text-fg">Predicciones automáticas</h2>

      {hasForecast && (
        <div>
          <h3 className="mb-2 font-serif text-xl text-fg">
            Forecasting — {nextHorizonText(forecast!)}
          </h3>
          <ForecastChart forecast={forecast!} />
        </div>
      )}

      {hasRegression && (
        <div>
          <h3 className="mb-2 font-serif text-xl text-fg">
            Regresión baseline (RandomForest) — importancia de variables
          </h3>
          <FeatureImportance regression={regression!} />
        </div>
      )}
    </div>
  )
}
