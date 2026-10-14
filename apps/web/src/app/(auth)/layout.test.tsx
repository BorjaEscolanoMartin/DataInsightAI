import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import AuthLayout from "./layout"

describe("auth layout", () => {
  it("links the brand to the home page and offers the theme toggle", () => {
    render(
      <AuthLayout>
        <p>Formulario</p>
      </AuthLayout>,
    )

    expect(screen.getByRole("link", { name: "DataInsight AI, ir al inicio" }).getAttribute("href")).toBe("/")
    expect(screen.getByRole("group", { name: "Tema" })).toBeTruthy()
    expect(screen.getByText("Formulario")).toBeTruthy()
  })
})
