import { act, renderHook } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"
import { useReducedMotion } from "./motion"

/** A matchMedia stand-in whose «prefers-reduced-motion: reduce» answer can change later. */
function mockMotionPreference(reduce: boolean) {
  const listeners = new Set<() => void>()
  const query = {
    get matches() {
      return reduce
    },
    addEventListener: (_: string, listener: () => void) => listeners.add(listener),
    removeEventListener: (_: string, listener: () => void) => listeners.delete(listener),
  }
  const matchMedia = vi.fn((media: string) => {
    expect(media).toBe("(prefers-reduced-motion: reduce)")
    return query
  })
  vi.stubGlobal("matchMedia", matchMedia)
  return {
    change(next: boolean) {
      reduce = next
      listeners.forEach((listener) => listener())
    },
  }
}

describe("useReducedMotion", () => {
  afterEach(() => vi.unstubAllGlobals())

  it("is true when the system asks to reduce motion", () => {
    mockMotionPreference(true)

    expect(renderHook(() => useReducedMotion()).result.current).toBe(true)
  })

  it("is false otherwise and follows a later change of the setting", () => {
    const preference = mockMotionPreference(false)
    const { result } = renderHook(() => useReducedMotion())
    expect(result.current).toBe(false)

    act(() => preference.change(true))

    expect(result.current).toBe(true)
  })
})
