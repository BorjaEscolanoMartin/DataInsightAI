import type { ForecastFrequency, ForecastOut } from "@/types/api"

const FREQUENCIES: Record<ForecastFrequency, { next: string; unit: string; adjective: string }> = {
  D: { next: "próximos", unit: "días", adjective: "diaria" },
  W: { next: "próximas", unit: "semanas", adjective: "semanal" },
  M: { next: "próximos", unit: "meses", adjective: "mensual" },
  Q: { next: "próximos", unit: "trimestres", adjective: "trimestral" },
  Y: { next: "próximos", unit: "años", adjective: "anual" },
}

// Analyses stored before the forecast had a frequency were daily, with horizon_days.
function frequencyOf(forecast: ForecastOut) {
  return FREQUENCIES[forecast.frequency ?? "D"]
}

/** "12 meses" */
export function horizonText(forecast: ForecastOut): string {
  return `${forecast.horizon ?? forecast.horizon_days ?? 30} ${frequencyOf(forecast).unit}`
}

/** "próximos 12 meses" */
export function nextHorizonText(forecast: ForecastOut): string {
  return `${frequencyOf(forecast).next} ${horizonText(forecast)}`
}

/** "Suma mensual de Ventas" when repeated dates were summed, otherwise the column name. */
export function targetText(forecast: ForecastOut): string {
  if (forecast.aggregation !== "sum") return forecast.target_column
  return `Suma ${frequencyOf(forecast).adjective} de ${forecast.target_column}`
}
