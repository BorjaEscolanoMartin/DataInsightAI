import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { InsightCard } from "./InsightCard"

describe("InsightCard", () => {
  it("lists the related columns as one line of text", () => {
    render(
      <InsightCard
        item={{ title: "Crecimiento", description: "Las ventas suben.", columns: ["Ventas", "Fecha"] }}
      />,
    )

    expect(screen.getByRole("heading", { name: "Crecimiento" })).toBeTruthy()
    expect(screen.getByText("Ventas · Fecha")).toBeTruthy()
  })
})
