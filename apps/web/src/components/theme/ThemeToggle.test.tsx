import { fireEvent, render, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { THEME_STORAGE_KEY } from "@/lib/theme"
import { ThemeToggle } from "./ThemeToggle"

const root = document.documentElement

function pressed() {
  return ["Sistema", "Claro", "Oscuro"].map(
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

  it("offers three labelled buttons and starts on the system choice", () => {
    render(<ThemeToggle />)

    expect(screen.getByRole("group", { name: "Tema" })).toBeTruthy()
    expect(pressed()).toEqual(["true", "false", "false"])
  })

  it("shows the stored choice as pressed", () => {
    localStorage.setItem(THEME_STORAGE_KEY, "dark")

    render(<ThemeToggle />)

    expect(pressed()).toEqual(["false", "false", "true"])
  })

  it("applies, remembers and clears the chosen theme", () => {
    render(<ThemeToggle />)

    fireEvent.click(screen.getByRole("button", { name: "Oscuro" }))
    expect(pressed()).toEqual(["false", "false", "true"])
    expect(root.getAttribute("data-theme")).toBe("dark")
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark")

    fireEvent.click(screen.getByRole("button", { name: "Claro" }))
    expect(pressed()).toEqual(["false", "true", "false"])
    expect(root.getAttribute("data-theme")).toBe("light")
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("light")

    fireEvent.click(screen.getByRole("button", { name: "Sistema" }))
    expect(pressed()).toEqual(["true", "false", "false"])
    expect(root.hasAttribute("data-theme")).toBe(false)
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBeNull()
  })

  it("still applies the choice to the page when storage fails", () => {
    vi.spyOn(window, "localStorage", "get").mockImplementation(() => {
      throw new DOMException("Storage is disabled", "SecurityError")
    })

    render(<ThemeToggle />)
    expect(pressed()).toEqual(["true", "false", "false"])

    fireEvent.click(screen.getByRole("button", { name: "Oscuro" }))

    expect(pressed()).toEqual(["false", "false", "true"])
    expect(root.getAttribute("data-theme")).toBe("dark")
  })
})
