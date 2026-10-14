import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { salesFixture as sales } from "@/data/demo"
import type { DatasetWithAnalysis } from "@/types/api"
import ProjectPage from "./page"

const state = vi.hoisted(() => ({ datasets: [] as unknown[] }))

vi.mock("next/navigation", () => ({ useParams: () => ({ id: "p1" }) }))
vi.mock("@/lib/api", () => ({ api: { downloadPdf: vi.fn() } }))
vi.mock("@/lib/queries", () => ({
  useProject: () => ({ data: { id: "p1", name: "Tienda online" } }),
  useProjectDatasets: () => ({ data: state.datasets, isLoading: false }),
  useUploadDataset: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useAnalysisPoll: () => ({ data: undefined }),
}))

function dataset(status: string): DatasetWithAnalysis {
  return {
    dataset: {
      id: "d1",
      project_id: "p1",
      filename: sales.filename,
      size_bytes: sales.size_bytes,
      row_count: sales.row_count,
      column_count: sales.column_count,
      uploaded_at: "2026-10-14T10:00:00Z",
    },
    analysis: {
      id: "a1",
      dataset_id: "d1",
      status,
      ...(status === "completed"
        ? sales.analysis
        : { profile: null, insights: null, predictions: null }),
      started_at: null,
      finished_at: null,
    },
  }
}

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <ProjectPage />
    </QueryClientProvider>,
  )
}

function breadcrumb() {
  return screen.getByRole("link", { name: "Proyectos" }).getAttribute("href")
}

describe("/projects/[id]", () => {
  beforeEach(() => {
    state.datasets = []
  })

  it("offers the upload section and the demo when the project has no dataset", () => {
    renderPage()

    expect(breadcrumb()).toBe("/projects")
    expect(screen.getByRole("link", { name: "Proyectos" }).parentElement?.textContent).toBe(
      "Proyectos / Tienda online",
    )
    expect(screen.getByRole("heading", { level: 2, name: "01 Subir datos" })).toBeTruthy()
    expect(screen.getByRole("button", { name: "Seleccionar archivo" })).toBeTruthy()
    expect(screen.getByRole("link", { name: "Mira el análisis de ejemplo" }).getAttribute("href")).toBe(
      "/demo",
    )
  })

  it("shows the status of an analysis in progress", () => {
    state.datasets = [dataset("running")]

    renderPage()

    const status = screen.getByRole("status")
    expect(status.textContent).toContain(sales.filename)
    expect(status.textContent).toContain("Analizando datos...")
    expect(screen.queryByRole("table")).toBeNull()
  })

  it("shows a failed analysis and lets the user upload a new CSV", () => {
    state.datasets = [dataset("failed")]

    renderPage()

    expect(screen.getByRole("status").textContent).toContain("Error en el análisis")
    expect(screen.getByLabelText("Subir nuevo CSV")).toBeTruthy()
  })

  it("shows a completed analysis with the new upload and the PDF after the columns", () => {
    state.datasets = [dataset("completed")]

    renderPage()

    expect(breadcrumb()).toBe("/projects")
    expect(screen.getByRole("heading", { level: 1, name: sales.filename })).toBeTruthy()
    const table = screen.getByRole("table")
    for (const action of [
      screen.getByLabelText("Subir nuevo CSV"),
      screen.getByRole("button", { name: "Descargar el informe en PDF" }),
    ]) {
      expect(table.compareDocumentPosition(action) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    }
  })
})
