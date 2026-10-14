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
    name: "Día de la semana",
    type: "categorical",
    null_count: 0,
    null_pct: 0,
    unique_count: 7,
    top_categories: [
      { value: "Martes", count: 105 },
      { value: "Miércoles", count: 105 },
      { value: "Jueves", count: 104 },
      { value: "Viernes", count: 104 },
      { value: "Sábado", count: 104 },
      { value: "Domingo", count: 104 },
      { value: "Lunes", count: 104 },
    ],
  },
  {
    name: "Activo",
    type: "boolean",
    null_count: 0,
    null_pct: 0,
    unique_count: 2,
    top_categories: [
      { value: "true", count: 3 },
      { value: "false", count: 1 },
    ],
  },
  { name: "Fecha", type: "date", null_count: 0, null_pct: 0, unique_count: 730 },
  {
    name: "Entrega",
    type: "date",
    null_count: 0,
    null_pct: 0,
    unique_count: 700,
    min_date: "2024-10-01",
    max_date: "2026-09-30",
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

  it.each([
    [
      "Día de la semana",
      "Martes 105 · Miércoles 105 · Jueves 104…",
      "Martes105Miércoles105Jueves104Viernes104Sábado104Domingo104Lunes104",
    ],
    ["Activo", "true 3 · false 1", "true3false1"],
  ])("expands the %s column to every category and its count", (name, inline, strip) => {
    render(<ColumnTable columns={COLUMNS} />)
    const button = screen.getByRole("button", { name })
    expect(row(name).textContent).toContain(inline)

    fireEvent.click(button)

    expect(button.getAttribute("aria-expanded")).toBe("true")
    const detail = row(name).nextElementSibling as HTMLElement
    expect(detail.textContent).toBe(strip)
  })

  it("keeps a date column as a plain row", () => {
    render(<ColumnTable columns={COLUMNS} />)

    expect(within(row("Fecha")).queryByRole("button")).toBeNull()
  })

  it("summarises a date column with its range, or as before without one", () => {
    render(<ColumnTable columns={COLUMNS} />)

    expect(row("Entrega").textContent).toContain("1 oct 2024 – 30 sep 2026")
    expect(within(row("Fecha")).getAllByRole("cell").at(-1)?.textContent).toBe("—")
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
