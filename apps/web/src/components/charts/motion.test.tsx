import { render } from "@testing-library/react"
import { cloneElement, type ReactElement } from "react"
import { afterEach, describe, expect, it, vi } from "vitest"
import { ValueColumnChart } from "./BarChartComp"

// jsdom has no layout, so the container gets a fixed size and Recharts draws its SVG.
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
