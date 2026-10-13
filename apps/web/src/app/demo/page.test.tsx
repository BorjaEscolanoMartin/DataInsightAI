import { act, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import DemoPage from "./page"

describe("/demo", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>
  let xhrSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    vi.useFakeTimers()
    fetchSpy = vi.spyOn(globalThis, "fetch")
    xhrSpy = vi.spyOn(XMLHttpRequest.prototype, "open")
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it("renders both fixtures without any network request", async () => {
    render(<DemoPage />)

    expect(screen.getByRole("note").textContent).toContain("Datos sintéticos")
    const sales = screen.getByRole("button", { name: "Ventas diarias · previsión" })
    const housing = screen.getByRole("button", { name: "Viviendas · regresión" })
    expect(sales.getAttribute("aria-pressed")).toBe("true")
    expect(housing.getAttribute("aria-pressed")).toBe("false")
    expect(screen.getByText("demo_ventas_diarias.csv")).toBeTruthy()

    fireEvent.click(housing)

    expect(housing.getAttribute("aria-pressed")).toBe("true")
    expect(sales.getAttribute("aria-pressed")).toBe("false")
    expect(screen.getByText("demo_viviendas.csv")).toBeTruthy()
    expect(screen.queryByText("demo_ventas_diarias.csv")).toBeNull()

    // Let pending timers and promises run, so a deferred request would be caught too.
    await act(async () => {
      await vi.runOnlyPendingTimersAsync()
    })

    expect(fetchSpy).not.toHaveBeenCalled()
    expect(xhrSpy).not.toHaveBeenCalled()
  })
})
