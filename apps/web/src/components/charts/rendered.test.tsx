import { act, render } from "@testing-library/react"
import { cloneElement, type ReactElement } from "react"
import { afterEach, describe, expect, it, vi } from "vitest"
import { CategoricalBarChart, categoryLabelWidth, ValueColumnChart } from "./BarChartComp"
import { HistogramChart } from "./HistogramChart"
import { histogramView } from "./histogram"

// Charts as Recharts draws them: jsdom has no layout, so the container gets a fixed size.
vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>()
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactElement }) =>
      cloneElement(children as ReactElement<{ width: number; height: number }>, { width: 400, height: 200 }),
  }
})

function preferReducedMotion(reduce: boolean) {
  vi.stubGlobal("matchMedia", () => ({
    matches: reduce,
    addEventListener: () => {},
    removeEventListener: () => {},
  }))
}

const barHeights = (container: HTMLElement) =>
  [...container.querySelectorAll(".recharts-bar-rectangle path")].map((p) =>
    Number(p.getAttribute("height")),
  )

describe("chart animation", () => {
  afterEach(() => vi.unstubAllGlobals())

  it("draws the bars at their final height at once when the system reduces motion", () => {
    preferReducedMotion(true)
    const { container } = render(
      <ValueColumnChart data={[{ name: "1", count: 10 }, { name: "2", count: 20 }]} />,
    )

    const heights = barHeights(container)
    expect(heights).toHaveLength(2)
    expect(heights.every((h) => h > 0)).toBe(true)
  })

  it("grows the two bars from nothing otherwise", async () => {
    preferReducedMotion(false)
    const { container } = render(
      <ValueColumnChart data={[{ name: "1", count: 10 }, { name: "2", count: 20 }]} />,
    )

    // Both bars are there from the start, with no shape yet: the animation draws them.
    expect(container.querySelectorAll(".recharts-bar-rectangle")).toHaveLength(2)
    expect(barHeights(container)).toEqual([])

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 1200))
    })

    const heights = barHeights(container)
    expect(heights).toHaveLength(2)
    expect(heights.every((h) => h > 0)).toBe(true)
  })
})

const yTicks = (container: HTMLElement) =>
  [...container.querySelectorAll(".recharts-yAxis .recharts-cartesian-axis-tick-value")].map(
    (t) => t.textContent,
  )

describe("count axes", () => {
  it("ends the value columns' axis at a round number, in Spanish", () => {
    const { container } = render(
      <ValueColumnChart
        data={[
          { name: "1", count: 775 },
          { name: "2", count: 592 },
          { name: "3", count: 1260 },
        ]}
      />,
    )

    expect(yTicks(container)).toEqual(["0", "500", "1.000", "1.500"])
  })

  it("ends a histogram's count axis at a round number, in Spanish", () => {
    const view = histogramView([
      { bin: "0–10", start: 0, end: 10, count: 1460 },
      { bin: "10–20", start: 10, end: 20, count: 820 },
    ])
    const { container } = render(<HistogramChart view={view} />)

    expect(yTicks(container)).toEqual(["0", "500", "1.000", "1.500"])
  })
})

describe("category bars", () => {
  const ZONAS = [
    { name: "Centro", count: 346 },
    { name: "Norte", count: 338 },
    { name: "Periferia", count: 256 },
  ]

  it("fits the label column to the longest name", () => {
    expect(categoryLabelWidth(["Centro", "Periferia"])).toBe(categoryLabelWidth(["Periferia"]))
    expect(categoryLabelWidth(["Periferia"])).toBeGreaterThan(categoryLabelWidth(["Sur"]))
    expect(categoryLabelWidth(["Una categoría con un nombre muy, muy largo"])).toBe(140)
  })

  it("draws each bar 60 % of its row, right after the label column", () => {
    preferReducedMotion(true)
    const { container } = render(<CategoricalBarChart data={ZONAS} />)

    const bars = [...container.querySelectorAll(".recharts-bar-rectangle path")]
    expect(bars).toHaveLength(3)
    const [first, second] = bars.map((b) => ({
      x: Number(b.getAttribute("x")),
      y: Number(b.getAttribute("y")),
      height: Number(b.getAttribute("height")),
    }))
    expect(first.height / (second.y - first.y)).toBeCloseTo(0.6, 1)
    expect(first.x).toBeCloseTo(8 + categoryLabelWidth(ZONAS.map((z) => z.name)), 0)
  })
})

