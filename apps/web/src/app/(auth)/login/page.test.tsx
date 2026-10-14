import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import LoginPage from "./page"

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }))
vi.mock("@/lib/supabase", () => ({
  createClient: () => ({
    auth: {
      signInWithPassword: async () => ({ error: { message: "Invalid login credentials" } }),
    },
  }),
}))

describe("/login", () => {
  it("titles its form", () => {
    render(<LoginPage />)

    expect(screen.getByRole("heading", { level: 2, name: "Iniciar sesión" })).toBeTruthy()
    expect(screen.getByText("Entra para ver tus proyectos y subir datos.")).toBeTruthy()
  })

  it("links to the signup page", () => {
    render(<LoginPage />)

    expect(screen.getByRole("link", { name: "Regístrate" }).getAttribute("href")).toBe("/signup")
  })

  it("labels its fields", () => {
    render(<LoginPage />)

    expect(screen.getByLabelText("Email").getAttribute("type")).toBe("email")
    expect(screen.getByLabelText("Contraseña").getAttribute("type")).toBe("password")
    expect(screen.getByLabelText("Email").getAttribute("autocomplete")).toBe("email")
    expect(screen.getByLabelText("Contraseña").getAttribute("autocomplete")).toBe("current-password")
  })

  it("announces a failed login as an alert", async () => {
    render(<LoginPage />)
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "ana@example.com" } })
    fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "secreta123" } })

    fireEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }))

    expect((await screen.findByRole("alert")).textContent).toBe("Invalid login credentials")
  })
})
