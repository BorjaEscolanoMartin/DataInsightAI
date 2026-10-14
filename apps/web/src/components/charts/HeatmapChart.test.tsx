import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { correlationCellColor, HeatmapChart, isWideHeatmap } from "./HeatmapChart"

describe("correlationCellColor", () => {
  it.each([
    [1, "color-mix(in srgb, var(--au) 50%, var(--bg))"],
    [0.92, "color-mix(in srgb, var(--au) 47%, var(--bg))"],
    [0, "color-mix(in srgb, var(--au) 10%, var(--bg))"],
    [-0.45, "color-mix(in srgb, var(--f3) 28%, var(--bg))"],
    [-1, "color-mix(in srgb, var(--f3) 50%, var(--bg))"],
  ])("tints r = %s with the accent for positives and a neutral for negatives", (r, colour) => {
    expect(correlationCellColor(r)).toBe(colour)
  })
})

describe("HeatmapChart", () => {
  it("prints every value with a real minus sign and lists the pairs for screen readers", () => {
    render(
      <HeatmapChart
        columns={["Ventas", "Coste"]}
        data={[
          { x: "Ventas", y: "Ventas", value: 1 },
          { x: "Ventas", y: "Coste", value: -0.45 },
          { x: "Coste", y: "Ventas", value: -0.45 },
          { x: "Coste", y: "Coste", value: 1 },
        ]}
      />,
    )

    expect(
      screen.getByRole("img", { name: "Coeficientes de correlación. Ventas y Coste: −0,45" }),
    ).toBeTruthy()
    expect(screen.getAllByText("−0,45")).toHaveLength(2)
    expect(screen.getAllByText("1,00")).toHaveLength(2)
  })
})

const SIX = ["Metros", "Habitaciones", "Baños", "Antigüedad (años)", "Distancia al mar (km)", "Precio"]
const matrix = (columns: string[]) =>
  columns.flatMap((x) => columns.map((y) => ({ x, y, value: x === y ? 1 : 0.5 })))

describe("isWideHeatmap", () => {
  it("is wide with more than four variables", () => {
    expect(isWideHeatmap(SIX.slice(0, 5))).toBe(true)
    expect(isWideHeatmap(SIX.slice(0, 4))).toBe(false)
  })
})

describe("HeatmapChart sizes", () => {
  it("writes the full names of a wide heatmap and keeps a 620 px minimum inside its scroll box", () => {
    render(<HeatmapChart columns={SIX} data={matrix(SIX)} />)

    const grid = screen.getByRole("img")
    expect(grid.style.minWidth).toBe("620px")
    expect(grid.parentElement?.className).toContain("overflow-x-auto")
    const label = screen.getAllByText("Distancia al mar (km)")[0]
    expect(label.className).not.toContain("truncate")
  })

  it("keeps a compact heatmap of four variables or fewer as it is", () => {
    const four = SIX.slice(0, 4)
    render(<HeatmapChart columns={four} data={matrix(four)} />)

    const grid = screen.getByRole("img")
    expect(grid.style.minWidth).toBe("")
    expect(screen.getAllByText("Antigüedad (años)")[0].className).toContain("truncate")
  })
})

describe("HeatmapChart scroll box", () => {
  it("lets the keyboard reach the scroll box of a wide heatmap", () => {
    render(<HeatmapChart columns={SIX} data={matrix(SIX)} />)

    const box = screen.getByRole("region", { name: "Mapa de correlaciones, desplazable en horizontal" })
    expect(box.tabIndex).toBe(0)
    expect(box.className).toContain("overflow-x-auto")
  })

  it("adds no tab stop to a compact heatmap, which fits its cell", () => {
    const four = SIX.slice(0, 4)
    render(<HeatmapChart columns={four} data={matrix(four)} />)

    expect(screen.queryByRole("region")).toBeNull()
  })
})

