import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import AuthLayout from "./layout"

describe("auth layout", () => {
  it("shows the brand and offers the theme toggle", () => {
    render(
      <AuthLayout>
        <p>Formulario</p>
      </AuthLayout>,
    )

    expect(screen.getByText("DataInsight AI")).toBeTruthy()
    expect(screen.getByRole("group", { name: "Tema" })).toBeTruthy()
    expect(screen.getByText("Formulario")).toBeTruthy()
  })
})
