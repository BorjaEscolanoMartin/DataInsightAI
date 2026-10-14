import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { housingFixture as housing, salesFixture as sales } from "@/data/demo"
import { formatNumber } from "@/lib/format"
import { AnalysisView } from "./AnalysisView"

// The dataset section is a <dl>: each value is the element right after its label.
function stat(label: string): string | null {
  return screen.getByText(label, { selector: "dt" }).nextElementSibling?.textContent ?? null
}

function sectionTitles(): (string | null)[] {
  return screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent)
}

describe("AnalysisView", () => {
  it("falls back to the dataset counts and shows only the dataset section without a profile", () => {
    render(
      <AnalysisView
        filename="ventas.csv"
        sizeBytes={2048}
        rowCount={12}
        columnCount={3}
        analysis={{ profile: null, insights: null, predictions: null }}
      />,
    )

    expect(screen.getByRole("heading", { level: 1, name: "ventas.csv" })).toBeTruthy()
    expect(stat("Filas")).toBe("12")
    expect(stat("Columnas")).toBe("3")
    expect(stat("Tamaño")).toBe("2,0 KB")
    expect(screen.queryByText("Columna de fecha")).toBeNull()
    expect(sectionTitles()).toEqual(["01 Dataset"])
    expect(screen.queryByRole("table")).toBeNull()
  })

  it("numbers every section of a full analysis in order", () => {
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
    expect(stat("Filas")).toBe(formatNumber(profile.row_count))
    expect(stat("Columnas")).toBe(String(profile.column_count))
    expect(stat("Columna de fecha")).toBe(profile.date_column_candidate)
    expect(sectionTitles()).toEqual([
      "01 Dataset",
      "02 Hallazgos",
      "03 Predicciones",
      "04 Gráficos",
      "05 Columnas",
    ])
    // One header row plus one row per profiled column.
    expect(screen.getAllByRole("row")).toHaveLength(profile.columns.length + 1)
  })

  it("numbers only the sections it shows", () => {
    render(
      <AnalysisView
        filename={sales.filename}
        sizeBytes={sales.size_bytes}
        rowCount={null}
        columnCount={null}
        analysis={{ ...sales.analysis, insights: null, predictions: null }}
      />,
    )

    expect(sectionTitles()).toEqual(["01 Dataset", "02 Gráficos", "03 Columnas"])
  })

  it("shows the eyebrow above the file name and the actions after the columns", () => {
    render(
      <AnalysisView
        filename={sales.filename}
        sizeBytes={sales.size_bytes}
        rowCount={null}
        columnCount={null}
        analysis={sales.analysis}
        eyebrow="Demo · datos sintéticos"
        actions={<a href="/signup">Analiza tu propio CSV</a>}
      />,
    )

    const eyebrow = screen.getByText("Demo · datos sintéticos")
    const title = screen.getByRole("heading", { level: 1 })
    expect(eyebrow.compareDocumentPosition(title) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    const action = screen.getByRole("link", { name: "Analiza tu propio CSV" })
    expect(
      screen.getByRole("table").compareDocumentPosition(action) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
  })

  // The sales fixture predates the date range: it stands for an old analysis.
  const withRange = {
    ...sales.analysis,
    profile: {
      ...sales.analysis.profile!,
      columns: sales.analysis.profile!.columns.map((c) =>
        c.name === sales.analysis.profile!.date_column_candidate
          ? { ...c, min_date: "2024-10-01", max_date: "2026-09-30" }
          : c,
      ),
    },
  }

  it("shows the period of the detected date column and names the column below", () => {
    render(
      <AnalysisView
        filename={sales.filename}
        sizeBytes={sales.size_bytes}
        rowCount={null}
        columnCount={null}
        analysis={withRange}
      />,
    )

    expect(stat("Periodo")).toBe("1 oct 2024 – 30 sep 2026")
    expect(screen.getByText(`columna ${sales.analysis.profile!.date_column_candidate}`)).toBeTruthy()
    expect(screen.queryByText("Columna de fecha")).toBeNull()
  })

  it("shows an old analysis without the range as before", () => {
    render(
      <AnalysisView
        filename={sales.filename}
        sizeBytes={sales.size_bytes}
        rowCount={null}
        columnCount={null}
        analysis={sales.analysis}
      />,
    )

    expect(stat("Columna de fecha")).toBe(sales.analysis.profile!.date_column_candidate)
    expect(screen.queryByText("Periodo")).toBeNull()
  })

  it("shows neither the period nor the date column without a date column", () => {
    render(
      <AnalysisView
        filename={housing.filename}
        sizeBytes={housing.size_bytes}
        rowCount={null}
        columnCount={null}
        analysis={housing.analysis}
      />,
    )

    expect(housing.analysis.profile!.date_column_candidate).toBeNull()
    expect(screen.queryByText("Periodo")).toBeNull()
    expect(screen.queryByText("Columna de fecha")).toBeNull()
  })
})
