import { describe, expect, it } from "vitest"
import { histogramView } from "./histogram"

// Bins as the API sends them since #37: numeric bounds, and outlier bins with one open bound.
const METROS = [
  { bin: "25–31.85", start: 25, end: 31.85, count: 27 },
  { bin: "31.85–38.7", start: 31.85, end: 38.7, count: 35 },
  { bin: "155.2–162", start: 155.15, end: 162, count: 21 },
  { bin: "> 162", start: 162, end: null, count: 62 },
]

describe("histogramView", () => {
  it("labels the bins with Spanish numbers and marks the bin above the bounds", () => {
    const view = histogramView(METROS)

    expect(view.bars.map((b) => b.range)).toEqual(["25–31,85", "31,85–38,7", "155,15–162", "> 162"])
    expect(view.bars.map((b) => b.side)).toEqual([null, null, null, "above"])
    expect(view.bars.map((b) => b.count)).toEqual([27, 35, 21, 62])
    expect(view.axis).toEqual({ first: "25", last: "162" })
    expect(view.note).toBe("62 por encima de 162")
  })

  it("groups thousands and never writes exponents", () => {
    const view = histogramView([
      { bin: "2.2e+04–4.342e+04", start: 22000, end: 43425, count: 9 },
      { bin: "4.29e+05–4.505e+05", start: 429075, end: 450500, count: 8 },
      { bin: "> 4.505e+05", start: 450500, end: null, count: 49 },
    ])

    expect(view.bars.map((b) => b.range)).toEqual([
      "22.000–43.425",
      "429.075–450.500",
      "> 450.500",
    ])
    expect(view.axis).toEqual({ first: "22.000", last: "450.500" })
    expect(view.note).toBe("49 por encima de 450.500")
  })

  it("gives the axis ends the same decimals and has no note without outliers", () => {
    const view = histogramView([
      { bin: "0.1–0.545", start: 0.1, end: 0.545, count: 104 },
      { bin: "8.555–9", start: 8.555, end: 9, count: 60 },
    ])

    expect(view.axis).toEqual({ first: "0,1", last: "9,0" })
    expect(view.bars.every((b) => b.side === null)).toBe(true)
    expect(view.note).toBeNull()
  })

  it("names the outliers on both sides, below first", () => {
    const view = histogramView([
      { bin: "< 72", start: null, end: 72, count: 6 },
      { bin: "72–100", start: 72, end: 100, count: 300 },
      { bin: "100–128", start: 100, end: 128, count: 194 },
      { bin: "> 128", start: 128, end: null, count: 3 },
    ])

    expect(view.bars.map((b) => [b.range, b.side])).toEqual([
      ["< 72", "below"],
      ["72–100", null],
      ["100–128", null],
      ["> 128", "above"],
    ])
    expect(view.axis).toEqual({ first: "72", last: "128" })
    expect(view.note).toBe("6 por debajo de 72 · 3 por encima de 128")
  })

  it("keeps the label of old analyses, which only have bin", () => {
    const view = histogramView([
      { bin: "1–1.15", count: 775 },
      { bin: "3.85–4", count: 7 },
    ])

    expect(view.bars.map((b) => [b.range, b.side])).toEqual([
      ["1–1.15", null],
      ["3.85–4", null],
    ])
    expect(view.axis).toBeNull()
    expect(view.note).toBeNull()
  })
})
