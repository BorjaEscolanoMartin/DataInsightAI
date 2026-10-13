import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import LoginPage from "./page"

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }))

describe("/login", () => {
  it("links to the public demo", () => {
    render(<LoginPage />)

    const link = screen.getByRole("link", { name: "Ver demo" })
    expect(link.getAttribute("href")).toBe("/demo")
  })
})
