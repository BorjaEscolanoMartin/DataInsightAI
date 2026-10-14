"use client"

import { nextHorizonText } from "@/lib/forecast"
import type { PredictionsOut } from "@/types/api"
import { ForecastChart } from "./ForecastChart"
import { FeatureImportance } from "./FeatureImportance"

interface Props {
  predictions: PredictionsOut
}

function hasForecast(predictions: PredictionsOut): boolean {
  return !!predictions.forecast && predictions.forecast.points.length > 0
}

function hasRegression(predictions: PredictionsOut): boolean {
  return !!predictions.regression && predictions.regression.feature_importance.length > 0
}

export function hasPredictions(predictions: PredictionsOut | null | undefined): predictions is PredictionsOut {
  return !!predictions && (hasForecast(predictions) || hasRegression(predictions))
}

export function PredictionsPanel({ predictions }: Props) {
  if (!hasPredictions(predictions)) return null
  const { forecast, regression } = predictions

  return (
    <div className="space-y-10">

      {hasForecast(predictions) && (
        <div>
          <h3 className="mb-2 font-serif text-xl text-fg">
            Previsión de {forecast!.target_column}: {nextHorizonText(forecast!)}
          </h3>
          <ForecastChart forecast={forecast!} />
        </div>
      )}

      {hasRegression(predictions) && (
        <div>
          <h3 className="mb-2 font-serif text-xl text-fg">
            Regresión (RandomForest): importancia de variables
          </h3>
          <FeatureImportance regression={regression!} />
        </div>
      )}
    </div>
  )
}
