// @vitest-environment node
import { NextRequest } from "next/server"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { middleware } from "./middleware"

// The real middleware runs on a real request; only Supabase is replaced, so getUser says
// whether there is a session.
const session = vi.hoisted(() => ({ user: null as null | { id: string } }))

vi.mock("@supabase/ssr", () => ({
  createServerClient: () => ({
    auth: { getUser: async () => ({ data: { user: session.user } }) },
  }),
}))

const ORIGIN = "http://localhost:3000"

async function visit(path: string, signedIn: boolean) {
  session.user = signedIn ? { id: "user-1" } : null
  return middleware(new NextRequest(new URL(path, ORIGIN)))
}

describe("middleware redirects", () => {
  beforeEach(() => {
    session.user = null
  })

  it.each([
    ["/", false, "/demo"],
    ["/", true, "/projects"],
    ["/projects", false, "/login"],
    ["/login", true, "/projects"],
  ])("sends %s (signed in: %s) to exactly our origin and %s", async (path, signedIn, target) => {
    const response = await visit(path, signedIn)

    expect(response.status).toBe(307)
    expect(response.headers.get("location")).toBe(`${ORIGIN}${target}`)
  })

  it.each([
    [false, "/demo"],
    [true, "/projects"],
  ])("ignores a next parameter on / (signed in: %s)", async (signedIn, target) => {
    const response = await visit("/?next=https://otra-web.com", signedIn)

    expect(response.status).toBe(307)
    expect(response.headers.get("location")).toBe(`${ORIGIN}${target}`)
  })
})
