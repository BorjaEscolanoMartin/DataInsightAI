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

  it("spans the whole grid with a heatmap of more than four variables", () => {
    const heatmap = (columns: string[]): ChartSpec => ({
      id: `heat_${columns.length}`,
      type: "heatmap",
      title: `Correlación ${columns.length}`,
      columns,
      data: columns.flatMap((x) => columns.map((y) => ({ x, y, value: 1 }))),
    })
    render(<ChartGrid charts={[heatmap(["a", "b", "c", "d", "e"]), heatmap(["a", "b", "c", "d"])]} />)

    const figure = (title: string) =>
      screen.getAllByRole("figure").find((f) => f.querySelector("figcaption")?.textContent === title)
    const wide = figure("Correlación 5")
    const compact = figure("Correlación 4")
    expect(wide?.parentElement?.className).toContain("col-span-full")
    expect(compact?.parentElement?.className ?? "").not.toContain("col-span-full")
  })

  it("puts wide charts after the small ones and stretches the last small chart to its row's end", () => {
    const columns = ["a", "b", "c", "d", "e"]
    render(
      <ChartGrid
        charts={[
          CHARTS[0],
          {
            id: "heat",
            type: "heatmap",
            title: "Correlación",
            columns,
            data: columns.flatMap((x) => columns.map((y) => ({ x, y, value: 1 }))),
          },
          CHARTS[2],
        ]}
      />,
    )

    const figures = screen.getAllByRole("figure")
    expect(figures.map((f) => f.querySelector("figcaption")?.firstChild?.textContent)).toEqual([
      "Distribución de Ventas",
      "Top valores de Zona",
      "Correlación",
    ])
    // Two small charts: the second ends the row on desktops (3 columns); tablets fit both.
    expect(figures[1].parentElement?.className).toContain("xl:col-span-2")
    expect(figures[0].parentElement?.className ?? "").not.toContain("col-span")
  })

  it("leaves charts of an unknown type out of the grid, so the last drawn chart ends its row", () => {
    const unknown = { id: "pie", type: "pie", title: "Tarta", data: [] } as unknown as ChartSpec
    render(<ChartGrid charts={[CHARTS[0], CHARTS[2], unknown]} />)

    const figures = screen.getAllByRole("figure")
    expect(figures).toHaveLength(2)
    // Two drawn small charts: the second ends the row on desktops.
    expect(figures[1].parentElement?.className).toContain("xl:col-span-2")
  })
})
