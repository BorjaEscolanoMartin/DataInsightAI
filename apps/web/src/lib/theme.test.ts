import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { THEME_SCRIPT, THEME_STORAGE_KEY } from "./theme"

// The script is shipped as a string and inlined in <head>, so the tests run that same string.
function runScript() {
  new Function(THEME_SCRIPT)()
}

const root = document.documentElement

describe("THEME_SCRIPT", () => {
  beforeEach(() => {
    localStorage.clear()
    root.removeAttribute("data-theme")
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it.each(["light", "dark"])("applies a stored %s choice to the root", (choice) => {
    localStorage.setItem(THEME_STORAGE_KEY, choice)

    runScript()

    expect(root.getAttribute("data-theme")).toBe(choice)
  })

  it("leaves the root alone without a stored choice, so the CSS default (dark) applies", () => {
    runScript()

    expect(root.hasAttribute("data-theme")).toBe(false)
  })

  it.each(["system", "sepia"])("ignores the invalid stored value %s", (value) => {
    localStorage.setItem(THEME_STORAGE_KEY, value)

    runScript()

    expect(root.hasAttribute("data-theme")).toBe(false)
  })

  it("falls back to the CSS default when storage cannot be read", () => {
    vi.spyOn(window, "localStorage", "get").mockImplementation(() => {
      throw new DOMException("Storage is disabled", "SecurityError")
    })

    expect(runScript).not.toThrow()
    expect(root.hasAttribute("data-theme")).toBe(false)
  })
})
