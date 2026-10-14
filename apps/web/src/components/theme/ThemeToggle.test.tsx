import { fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { THEME_STORAGE_KEY } from "@/lib/theme"
import { ThemeToggle } from "./ThemeToggle"

const root = document.documentElement

function pressed() {
  return ["Oscuro", "Claro"].map(
    (name) => screen.getByRole("button", { name }).getAttribute("aria-pressed"),
  )
}

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear()
    root.removeAttribute("data-theme")
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("offers two labelled buttons, dark first, and starts on dark", () => {
    render(<ThemeToggle />)

    const group = screen.getByRole("group", { name: "Tema" })
    expect(within(group).getAllByRole("button").map((b) => b.textContent)).toEqual(["Oscuro", "Claro"])
    expect(pressed()).toEqual(["true", "false"])
  })

  it("shows a stored light choice as pressed", () => {
    localStorage.setItem(THEME_STORAGE_KEY, "light")

    render(<ThemeToggle />)

    expect(pressed()).toEqual(["false", "true"])
  })

  it.each(["system", "sepia"])("treats the stored value %s as dark", (value) => {
    localStorage.setItem(THEME_STORAGE_KEY, value)

    render(<ThemeToggle />)

    expect(pressed()).toEqual(["true", "false"])
  })

  it("applies and remembers the chosen theme", () => {
    render(<ThemeToggle />)

    fireEvent.click(screen.getByRole("button", { name: "Claro" }))
    expect(pressed()).toEqual(["false", "true"])
    expect(root.getAttribute("data-theme")).toBe("light")
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("light")

    fireEvent.click(screen.getByRole("button", { name: "Oscuro" }))
    expect(pressed()).toEqual(["true", "false"])
    expect(root.getAttribute("data-theme")).toBe("dark")
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark")
  })

  it("still applies the choice to the page when storage fails", () => {
    vi.spyOn(window, "localStorage", "get").mockImplementation(() => {
      throw new DOMException("Storage is disabled", "SecurityError")
    })

    render(<ThemeToggle />)
    expect(pressed()).toEqual(["true", "false"])

    fireEvent.click(screen.getByRole("button", { name: "Claro" }))

    expect(pressed()).toEqual(["false", "true"])
    expect(root.getAttribute("data-theme")).toBe("light")
  })

  it("gives each option an icon hidden from assistive technology and keeps its text", () => {
    render(<ThemeToggle />)

    for (const name of ["Oscuro", "Claro"]) {
      const button = screen.getByRole("button", { name })
      const icon = button.querySelector("svg")
      expect(icon?.getAttribute("aria-hidden")).toBe("true")
      expect(button.textContent).toBe(name)
    }
  })
})
