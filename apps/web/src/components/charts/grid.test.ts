// @vitest-environment node
import { readFileSync } from "node:fs"
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

describe("grid classes", () => {
  it("are written whole in grid.ts, where Tailwind's scanner finds them", () => {
    // Next to this test, wherever the suite is launched from.
    const source = readFileSync(new URL("./grid.ts", import.meta.url), "utf8")
    const classes = new Set(
      Array.from({ length: 13 }, (_, count) => lastSpanClass(count).split(" ")).flat().filter(Boolean),
    )

    for (const name of classes) expect(source).toContain(`"${name}"`)
  })
})

