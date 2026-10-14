import { render } from "@testing-library/react"
import { cloneElement, type ReactElement } from "react"
import { afterEach, describe, expect, it, vi } from "vitest"
import { ValueColumnChart } from "./BarChartComp"
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

  it("animates the bars from nothing otherwise", () => {
    preferReducedMotion(false)
    const { container } = render(
      <ValueColumnChart data={[{ name: "1", count: 10 }, { name: "2", count: 20 }]} />,
    )

    expect(barHeights(container).every((h) => !(h > 0))).toBe(true)
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

