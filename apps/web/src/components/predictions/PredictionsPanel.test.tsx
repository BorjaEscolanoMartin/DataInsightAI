import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import type { ForecastOut } from "@/types/api"
import { PredictionsPanel } from "./PredictionsPanel"

const POINTS = [{ ds: "2025-01-01", yhat: 160, yhat_lower: 140, yhat_upper: 180 }]

const NEW_FORECAST: ForecastOut = {
  target_column: "Ventas",
  date_column: "Fecha",
  aggregation: "sum",
  frequency: "M",
  horizon: 12,
  wape: 9.67,
  mae: 268.46,
  mape: null,
  horizon_days: null,
  points: POINTS,
}

// An analysis stored before the forecast quality PR: only mape and horizon_days.
const OLD_FORECAST: ForecastOut = {
  target_column: "Ventas",
  date_column: "Fecha",
  mape: 8.96,
  horizon_days: 14,
  points: POINTS,
}

function renderForecast(forecast: ForecastOut) {
  return render(<PredictionsPanel predictions={{ forecast, regression: null }} />)
}

describe("PredictionsPanel forecast", () => {
  it("shows WAPE first, MAE as detail, the aggregation and the horizon", () => {
    const { container } = renderForecast(NEW_FORECAST)

    expect(screen.getByRole("heading", { name: "Previsión de Ventas: próximos 12 meses" })).toBeTruthy()
    const text = container.textContent ?? ""
    expect(text).toContain("Objetivo: Suma mensual de Ventas")
    expect(text).toContain("Horizonte: 12 meses")
    expect(text).toContain("WAPE del backtest: 9,7 %")
    expect(text).toContain("MAE: 268,5")
    expect(text.indexOf("WAPE")).toBeLessThan(text.indexOf("MAE"))
    expect(text).not.toContain("MAPE")
  })

  it.each([
    ["D", 30, "próximos 30 días", "Suma diaria de Ventas"],
    ["W", 12, "próximas 12 semanas", "Suma semanal de Ventas"],
    ["M", 12, "próximos 12 meses", "Suma mensual de Ventas"],
    ["Q", 8, "próximos 8 trimestres", "Suma trimestral de Ventas"],
    ["Y", 3, "próximos 3 años", "Suma anual de Ventas"],
  ] as const)("names the %s horizon and sum in its own unit", (frequency, horizon, title, target) => {
    const { container } = renderForecast({ ...NEW_FORECAST, frequency, horizon })

    expect(screen.getByRole("heading", { name: `Previsión de Ventas: ${title}` })).toBeTruthy()
    expect(container.textContent).toContain(`Objetivo: ${target}`)
  })

  it("shows the target alone when nothing was summed", () => {
    const { container } = renderForecast({ ...NEW_FORECAST, aggregation: "none" })

    expect(container.textContent).toContain("Objetivo: Ventas")
    expect(container.textContent).not.toContain("Suma")
  })

  it("renders an old analysis with only mape and horizon_days", () => {
    const { container } = renderForecast(OLD_FORECAST)

    expect(screen.getByRole("heading", { name: "Previsión de Ventas: próximos 14 días" })).toBeTruthy()
    const text = container.textContent ?? ""
    expect(text).toContain("Objetivo: Ventas")
    expect(text).toContain("Horizonte: 14 días")
    expect(text).toContain("MAPE del backtest: 9,0 %")
    expect(text).not.toContain("WAPE")
    expect(text).not.toContain("MAE:")
    expect(text).not.toContain("Suma")
  })
})
