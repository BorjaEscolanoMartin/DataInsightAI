import { describe, expect, it } from "vitest"
import type { ChartSpec } from "@/types/api"
import { isValueBars } from "./bars"

const bar = (data: Record<string, unknown>[]): ChartSpec => ({
  id: "bar_x",
  type: "bar",
  title: "Distribución de x",
  data,
})

describe("isValueBars", () => {
  it("is true for the count of each value of a whole-number column", () => {
    expect(isValueBars(bar([{ name: "1", value: 1, count: 155 }, { name: "2", value: 2, count: 338 }]))).toBe(true)
  })

  it("is false for category counts and for an empty chart", () => {
    expect(isValueBars(bar([{ name: "Centro", count: 346 }]))).toBe(false)
    expect(isValueBars(bar([]))).toBe(false)
  })
})
