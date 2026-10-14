import { describe, expect, it } from "vitest"
import type { ForecastOut } from "@/types/api"
import { forecastBandLabel, formatForecastValue } from "./ForecastChart"

const POINTS = [{ ds: "2025-01-01", yhat: 160, yhat_lower: 140, yhat_upper: 180 }]

describe("forecastBandLabel", () => {
  it("names the 95 % level for an analysis with the new fields", () => {
    const forecast: ForecastOut = { target_column: "Ventas", date_column: "Fecha", wape: 9.67, points: POINTS }

    expect(forecastBandLabel(forecast)).toBe("Intervalo del 95 %")
  })

  it("names no level for an old analysis, whose band was not calibrated", () => {
    const forecast: ForecastOut = {
      target_column: "Ventas",
      date_column: "Fecha",
      mape: 8.96,
      horizon_days: 14,
      points: POINTS,
    }

    expect(forecastBandLabel(forecast)).toBe("Intervalo")
  })
})

describe("formatForecastValue", () => {
  it("writes the band as lower – upper with the shared formatter", () => {
    expect(formatForecastValue([1402.5, 1810])).toBe("1.402,5 – 1.810")
  })

  it("writes a single value with the shared formatter", () => {
    expect(formatForecastValue(2307.456)).toBe("2.307,46")
  })
})
