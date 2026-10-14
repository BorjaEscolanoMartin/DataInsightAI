import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import AuthLayout from "./layout"

describe("auth layout", () => {
  it("shows the brand as text, not a link, and offers the theme toggle", () => {
    render(
      <AuthLayout>
        <p>Formulario</p>
      </AuthLayout>,
    )

    // On login and signup the brand is plain text: no link, nothing to focus.
    expect(screen.queryByRole("link", { name: /DataInsight/ })).toBeNull()
    const brand = screen.getByText("DataInsight").parentElement!
    expect(brand.textContent).toBe("DataInsight AI")
    expect(brand.closest("a")).toBeNull()
    expect(brand.hasAttribute("tabindex")).toBe(false)
    expect(screen.getByRole("group", { name: "Tema" })).toBeTruthy()
    expect(screen.getByText("Formulario")).toBeTruthy()
  })

  it("presents the app and sends reviewers to the demo without an account", () => {
    render(
      <AuthLayout>
        <p>Formulario</p>
      </AuthLayout>,
    )

    expect(
      screen.getByRole("heading", { level: 1, name: "De un CSV a un informe con hallazgos y previsiones" }),
    ).toBeTruthy()
    expect(screen.getByRole("heading", { level: 2, name: "¿Estás revisando el proyecto?" })).toBeTruthy()
    expect(screen.getByRole("link", { name: "Ver la demo sin registrarte" }).getAttribute("href")).toBe("/demo")
    expect(screen.getByText("Datos sintéticos · sin registro")).toBeTruthy()
  })
})
