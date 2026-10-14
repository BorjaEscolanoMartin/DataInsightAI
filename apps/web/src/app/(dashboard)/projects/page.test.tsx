import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import ProjectsPage from "./page"

const state = vi.hoisted(() => ({
  projects: [] as unknown[],
  create: vi.fn(async () => ({})),
}))

vi.mock("@/lib/queries", () => ({
  useProjects: () => ({ data: state.projects, isLoading: false, error: null }),
  useCreateProject: () => ({ mutateAsync: state.create, isPending: false }),
  useDeleteProject: () => ({ mutate: vi.fn() }),
  useUpdateProject: () => ({ mutateAsync: vi.fn() }),
}))

const PROJECT = {
  id: "p1",
  name: "Tienda online",
  description: "Ventas de 2026",
  created_at: "2026-10-01T09:00:00Z",
}

describe("/projects", () => {
  beforeEach(() => {
    state.projects = []
    state.create.mockClear()
  })

  it("creates a project from a labelled field with the trimmed name", async () => {
    render(<ProjectsPage />)
    expect(screen.getByText("No tienes proyectos todavía")).toBeTruthy()

    fireEvent.click(screen.getByRole("button", { name: "Nuevo proyecto" }))
    fireEvent.change(screen.getByLabelText("Nombre del proyecto"), {
      target: { value: "  Tienda online  " },
    })
    fireEvent.click(screen.getByRole("button", { name: "Crear" }))

    await waitFor(() => expect(state.create).toHaveBeenCalledWith({ name: "Tienda online" }))
  })

  it("links each project to its page and keeps its actions visible", () => {
    state.projects = [PROJECT]

    render(<ProjectsPage />)

    expect(screen.getByRole("link", { name: "Tienda online" }).getAttribute("href")).toBe(
      "/projects/p1",
    )
    expect(screen.getByText("Ventas de 2026")).toBeTruthy()
    expect(screen.getByRole("button", { name: "Renombrar Tienda online" })).toBeTruthy()
    expect(screen.getByRole("button", { name: "Borrar Tienda online" })).toBeTruthy()
  })

  it("writes each project's creation date as a short Spanish date", () => {
    state.projects = [PROJECT]

    render(<ProjectsPage />)

    expect(screen.getByText("1 oct 2026")).toBeTruthy()
    expect(screen.queryByText("1/10/2026")).toBeNull()
  })
})
