import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import SignupPage from "./page"

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }))
vi.mock("@/lib/supabase", () => ({
  createClient: () => ({
    auth: { signUp: async () => ({ data: null, error: { message: "User already registered" } }) },
  }),
}))

describe("/signup", () => {
  it("links to the login page", () => {
    render(<SignupPage />)

    expect(screen.getByRole("link", { name: "Inicia sesión" }).getAttribute("href")).toBe("/login")
  })

  it("labels its fields and asks for at least 8 characters", () => {
    render(<SignupPage />)

    expect(screen.getByLabelText("Email").getAttribute("type")).toBe("email")
    const password = screen.getByLabelText("Contraseña")
    expect(password.getAttribute("type")).toBe("password")
    expect(password.getAttribute("minlength")).toBe("8")
  })

  it("announces a failed signup as an alert", async () => {
    render(<SignupPage />)
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "ana@example.com" } })
    fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "secreta123" } })

    fireEvent.click(screen.getByRole("button", { name: "Crear cuenta" }))

    expect((await screen.findByRole("alert")).textContent).toBe("User already registered")
  })
})
