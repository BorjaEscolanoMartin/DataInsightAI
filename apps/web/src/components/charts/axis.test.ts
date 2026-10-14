import { describe, expect, it } from "vitest"
import { niceAxisMax, numberTick } from "./axis"

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
