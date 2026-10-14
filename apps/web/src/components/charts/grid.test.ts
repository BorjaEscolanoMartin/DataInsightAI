import { describe, expect, it } from "vitest"
import { lastSpanClass } from "./grid"

describe("lastSpanClass", () => {
  it.each([
    // Count of small charts → classes for the last one (2 columns on tablets, 3 on desktops).
    [9, "md:col-span-2 xl:col-span-1"],
    [8, "xl:col-span-2"],
    [7, "md:col-span-2 xl:col-span-3"],
    [6, ""],
    [5, "md:col-span-2 xl:col-span-2"],
    [4, "xl:col-span-3"],
    [1, "md:col-span-2 xl:col-span-3"],
    [0, ""],
  ])("stretches the last of %s small charts to the end of its row: «%s»", (count, classes) => {
    expect(lastSpanClass(count)).toBe(classes)
  })
})
