import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { correlationCellColor, HeatmapChart } from "./HeatmapChart"

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
