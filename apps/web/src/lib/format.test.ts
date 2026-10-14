import { describe, expect, it } from "vitest"
import { formatNumber } from "./format"

describe("formatNumber", () => {
  it.each([
    [2307.5, 1, 0, "2.307,5"],
    [1502.77, 2, 0, "1.502,77"],
    [730, 2, 0, "730"],
    [-1234.5, 1, 0, "−1.234,5"],
    [0.8196, 1, 1, "0,8"],
    [2, 1, 1, "2,0"],
  ])("writes %s like the backend's format_es", (n, max, min, text) => {
    expect(formatNumber(n, max, min)).toBe(text)
  })
})
