import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import ventas from "@/data/demo/ventas.json"
import { AnalysisView, type AnalysisViewProps } from "./AnalysisView"

const sales = ventas as unknown as {
  filename: string
  size_bytes: number
  row_count: number
  column_count: number
  analysis: AnalysisViewProps["analysis"]
}

function stat(label: string): string | null {
  return screen.getByText(label).nextElementSibling?.textContent ?? null
}

describe("AnalysisView", () => {
  it("falls back to the dataset counts and hides every section without a profile", () => {
    render(
      <AnalysisView
        filename="ventas.csv"
        sizeBytes={2048}
        rowCount={12}
        columnCount={3}
        analysis={{ profile: null, insights: null, predictions: null }}
      />,
    )

    expect(stat("Archivo")).toBe("ventas.csv")
    expect(stat("Filas")).toBe((12).toLocaleString())
    expect(stat("Columnas")).toBe("3")
    expect(stat("Tamaño")).toBe("2.0 KB")
    expect(screen.queryByText("Columna fecha")).toBeNull()
    expect(screen.queryByText("Insights generados por IA")).toBeNull()
    expect(screen.queryByText("Predicciones automáticas")).toBeNull()
    expect(screen.queryByRole("table")).toBeNull()
  })

  it("renders the profile counts and every section of a full analysis", () => {
    render(
      <AnalysisView
        filename={sales.filename}
        sizeBytes={sales.size_bytes}
        rowCount={null}
        columnCount={null}
        analysis={sales.analysis}
      />,
    )

    const profile = sales.analysis.profile!
    expect(stat("Filas")).toBe(profile.row_count.toLocaleString())
    expect(stat("Columnas")).toBe(String(profile.column_count))
    expect(stat("Columna fecha")).toBe(profile.date_column_candidate)
    expect(screen.getByText("Insights generados por IA")).toBeTruthy()
    expect(screen.getByText("Predicciones automáticas")).toBeTruthy()
    // One header row plus one row per profiled column.
    expect(screen.getAllByRole("row")).toHaveLength(profile.columns.length + 1)
  })
})
