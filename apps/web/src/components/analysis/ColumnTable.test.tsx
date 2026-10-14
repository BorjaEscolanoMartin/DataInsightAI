import { fireEvent, render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it } from "vitest"
import type { ColumnProfile } from "@/types/api"
import { ColumnTable } from "./ColumnTable"

const COLUMNS: ColumnProfile[] = [
  {
    name: "Ventas",
    type: "numeric",
    null_count: 0,
    null_pct: 0,
    unique_count: 729,
    mean: 2307.5,
    std: 459.4,
    min_val: 1502.77,
    p25: 2021.16,
    p50: 2243.5,
    p75: 2530.58,
    max_val: 8734.6,
    outlier_count: 8,
  },
  {
    name: "Visitas web",
    type: "numeric",
    null_count: 6,
    null_pct: 0.82,
    unique_count: 595,
    mean: 2232,
    std: 495.3,
    min_val: 1221,
    p25: 1900,
    p50: 2200,
    p75: 2550,
    max_val: 7624,
    outlier_count: 0,
  },
  {
    name: "Promoción",
    type: "categorical",
    null_count: 0,
    null_pct: 0,
    unique_count: 2,
    top_categories: [
      { value: "No", count: 680 },
      { value: "Sí", count: 50 },
    ],
  },
]

function row(name: string): HTMLElement {
  return screen.getByText(name).closest("tr")!
}

describe("ColumnTable", () => {
  it("expands a numeric column from a button in its first cell", () => {
    render(<ColumnTable columns={COLUMNS} />)
    const button = screen.getByRole("button", { name: "Ventas" })
    expect(within(row("Ventas")).getAllByRole("cell")[0].contains(button)).toBe(true)
    expect(button.getAttribute("aria-expanded")).toBe("false")
    expect(screen.queryByText("Mediana")).toBeNull()

    fireEvent.click(button)

    expect(button.getAttribute("aria-expanded")).toBe("true")
    const strip = screen.getByText("Mediana").closest("tr")!
    expect(strip.textContent).toBe("Mín.1.502,77P252.021,16Mediana2.243,5P752.530,58Máx.8.734,6")

    fireEvent.click(button)

    expect(button.getAttribute("aria-expanded")).toBe("false")
    expect(screen.queryByText("Mediana")).toBeNull()
  })

  it("expands and collapses a numeric column from the keyboard", async () => {
    const user = userEvent.setup()
    render(<ColumnTable columns={COLUMNS} />)
    const button = screen.getByRole("button", { name: "Ventas" })

    await user.tab()
    expect(document.activeElement).toBe(button)

    await user.keyboard("{Enter}")
    expect(button.getAttribute("aria-expanded")).toBe("true")
    expect(screen.getByText("Mediana")).toBeTruthy()

    await user.keyboard(" ")
    expect(button.getAttribute("aria-expanded")).toBe("false")
    expect(screen.queryByText("Mediana")).toBeNull()
  })

  it("keeps non-numeric columns as plain rows with their top values inline", () => {
    render(<ColumnTable columns={COLUMNS} />)
    const promo = row("Promoción")

    expect(within(promo).queryByRole("button")).toBeNull()
    expect(promo.textContent).toContain("No 680 · Sí 50")
    const rows = screen.getAllByRole("row").length
    fireEvent.click(promo)
    expect(screen.getAllByRole("row")).toHaveLength(rows)
  })

  it("summarises nulls and numeric columns in Spanish", () => {
    render(<ColumnTable columns={COLUMNS} />)

    expect(row("Visitas web").textContent).toContain("6 (0,8 %)")
    const ventas = row("Ventas")
    expect(ventas.textContent).toContain("numérica")
    expect(ventas.textContent).toContain("media 2.307,5 · desviación 459,4 · 8 atípicos")
    expect(row("Visitas web").textContent).not.toContain("atípicos")
  })
})
