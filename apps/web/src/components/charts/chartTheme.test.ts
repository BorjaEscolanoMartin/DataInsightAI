import { describe, expect, it } from "vitest"
import { chartTooltip, TOOLTIP_PROPS } from "./chartTheme"

describe("chartTooltip", () => {
  it("keeps the tooltip still when the system reduces motion", () => {
    expect(chartTooltip(true)).toEqual({ ...TOOLTIP_PROPS, isAnimationActive: false })
  })

  it("lets it slide otherwise", () => {
    expect(chartTooltip(false)).toEqual({ ...TOOLTIP_PROPS, isAnimationActive: true })
  })
})
