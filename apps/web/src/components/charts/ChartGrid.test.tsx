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

  it("notes the outlier bins under a histogram's title, and nothing for old histograms", () => {
    render(
      <ChartGrid
        charts={[
          {
            id: "hist_Metros",
            type: "histogram",
            title: "Distribución de Metros",
            data: [
              { bin: "25–162", start: 25, end: 162, count: 1438 },
              { bin: "> 162", start: 162, end: null, count: 62 },
            ],
          },
          CHARTS[0],
        ]}
      />,
    )

    const [metros, old] = screen.getAllByRole("figure")
    expect(metros.querySelector("figcaption")?.textContent).toBe(
      "Distribución de Metros62 por encima de 162",
    )
    expect(old.querySelector("figcaption")?.textContent).toBe("Distribución de Ventas")
  })

  it("draws the values of a whole-number column as columns and categories as rows", () => {
    render(
      <ChartGrid
        charts={[
          {
            id: "bar_Baños",
            type: "bar",
            title: "Distribución de Baños",
            data: [
              { name: "1", value: 1, count: 775 },
              { name: "2", value: 2, count: 592 },
            ],
          },
          CHARTS[2],
        ]}
      />,
    )

    const [banos, zona] = screen.getAllByRole("figure")
    expect(banos.querySelector("[data-orientation]")?.getAttribute("data-orientation")).toBe("vertical")
    expect(zona.querySelector("[data-orientation]")?.getAttribute("data-orientation")).toBe("horizontal")
  })
})
