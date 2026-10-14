import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { SECONDARY_BUTTON } from "@/components/ui/styles"
import DashboardLayout from "./layout"

vi.mock("next/headers", () => ({ cookies: async () => ({ getAll: () => [] }) }))
vi.mock("@supabase/ssr", () => ({
  createServerClient: () => ({
    auth: { getUser: async () => ({ data: { user: { email: "ana@example.com" } } }) },
  }),
}))

describe("dashboard layout", () => {
  it("shows the brand, the user, the theme toggle and the logout button", async () => {
    render(await DashboardLayout({ children: <p>Contenido</p> }))

    expect(screen.getByRole("link", { name: "DataInsight AI, ir al inicio" }).getAttribute("href")).toBe("/")
    expect(screen.getByText("ana@example.com")).toBeTruthy()
    expect(screen.getByRole("group", { name: "Tema" })).toBeTruthy()
    expect(screen.getByRole("button", { name: "Cerrar sesión" })).toBeTruthy()
    expect(screen.getByText("Contenido")).toBeTruthy()
  })

  it("draws the logout button like «Iniciar sesión» on /demo and posts to the logout route", async () => {
    render(await DashboardLayout({ children: <p>Contenido</p> }))

    const logout = screen.getByRole("button", { name: "Cerrar sesión" })
    expect(logout.className).toBe(SECONDARY_BUTTON)
    expect(logout.closest("form")?.getAttribute("action")).toBe("/auth/logout")
    expect(logout.closest("form")?.getAttribute("method")).toBe("post")
  })
})
