// @vitest-environment node
import { unstable_doesMiddlewareMatch } from "next/experimental/testing/server"
import { describe, expect, it } from "vitest"
import { config } from "./middleware"

describe("middleware matcher", () => {
  it.each(["/demo", "/demo/", "/demo/x"])(
    "does not run on the public demo (%s), so it never calls Supabase",
    (url) => {
      expect(unstable_doesMiddlewareMatch({ config, url })).toBe(false)
    },
  )

  it.each(["/", "/projects", "/projects/123", "/login", "/signup", "/demos"])(
    "still runs on %s",
    (url) => {
      expect(unstable_doesMiddlewareMatch({ config, url })).toBe(true)
    },
  )
})
