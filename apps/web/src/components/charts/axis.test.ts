import { describe, expect, it } from "vitest"
import { niceAxisMax, numberTick, scatterAxis } from "./axis"

describe("niceAxisMax", () => {
  it.each([
    [346, 400],
    [950, 1000],
    [1000, 1000],
    [7, 7],
    [12, 20],
    [0.34, 0.4],
  ])("rounds %s up to %s, the next multiple of its leading power of ten", (max, top) => {
    expect(niceAxisMax(max)).toBeCloseTo(top, 10)
  })

  it("gives an empty or all-zero chart an axis up to 1", () => {
    expect(niceAxisMax(0)).toBe(1)
  })
})

describe("numberTick", () => {
  it("writes axis numbers in Spanish", () => {
    expect([numberTick(1000), numberTick(450500), numberTick(0.5)]).toEqual(["1.000", "450.500", "0,5"])
  })
})

describe("scatterAxis", () => {
  it("leaves a 5 % margin and never goes below 0 for non-negative data", () => {
    // Precio: 22.000–721.000; the 5 % margin would reach −12.950, so the axis starts at 0.
    expect(scatterAxis([721000, 22000, 300000])).toEqual({
      domain: [0, 800000],
      ticks: [0, 200000, 400000, 600000, 800000],
    })
    // Metros: 25–239, with room on both sides.
    expect(scatterAxis([25, 239])).toEqual({ domain: [0, 250], ticks: [0, 50, 100, 150, 200, 250] })
  })

  it("starts above 0 when the data does, keeping the margin", () => {
    expect(scatterAxis([0.5, 1])).toEqual({ domain: [0.4, 1.2], ticks: [0.4, 0.6, 0.8, 1, 1.2] })
  })

  it("goes below 0 only for negative data", () => {
    expect(scatterAxis([-10, 10])).toEqual({ domain: [-15, 15], ticks: [-15, -10, -5, 0, 5, 10, 15] })
  })

  it("gives a single value some room around it", () => {
    expect(scatterAxis([5, 5])?.domain).toEqual([4.7, 5.3])
  })

  it("has no axis to fit without values", () => {
    expect(scatterAxis([])).toBeNull()
  })
})
