import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import type { ChartSpec } from "@/types/api"
import { ChartGrid } from "./ChartGrid"

const CHARTS: ChartSpec[] = [
  { id: "h", type: "histogram", title: "Distribución de Ventas", data: [{ bin: "1-2", count: 2 }] },
  {
    id: "l",
    type: "line",
    title: "Evolución de Ventas",
    y_column: "Ventas",
    data: [{ date: "2025-01-01", value: 1 }],
  },
  { id: "b", type: "bar", title: "Top valores de Zona", data: [{ name: "Playa", count: 1 }] },
]

describe("ChartGrid", () => {
  it("puts the time series first and keeps the order of the rest", () => {
    render(<ChartGrid charts={CHARTS} />)

    const titles = screen
      .getAllByRole("figure")
      .map((figure) => figure.querySelector("figcaption")?.textContent)
    expect(titles).toEqual(["Evolución de Ventas", "Distribución de Ventas", "Top valores de Zona"])
  })
})
