import { createServerClient } from "@supabase/ssr"
import { NextResponse, type NextRequest } from "next/server"

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet: { name: string; value: string; options?: object }[]) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const {
    data: { user },
  } = await supabase.auth.getUser()

  const { pathname } = request.nextUrl

  // Every redirect goes to a fixed internal path on our own origin: nothing from the request URL
  // (query, parameters) is carried over (S25). It keeps the cookies getUser() may have refreshed,
  // otherwise the browser would lose the rotated session.
  const redirectTo = (path: "/demo" | "/projects" | "/login") => {
    const response = NextResponse.redirect(new URL(path, request.url))
    supabaseResponse.cookies.getAll().forEach((cookie) => response.cookies.set(cookie))
    return response
  }

  // The home page decides by session: visitors see the demo, signed-in users their projects.
  if (pathname === "/") {
    return redirectTo(user ? "/projects" : "/demo")
  }

  const isAuthPage = pathname.startsWith("/login") || pathname.startsWith("/signup")
  const isDashboard = pathname.startsWith("/projects")

  if (isDashboard && !user) {
    return redirectTo("/login")
  }

  if (isAuthPage && user) {
    return redirectTo("/projects")
  }

  return supabaseResponse
}

export const config = {
  // /demo is public and static: skipping it means a visit never calls Supabase. The whole
  // /demo subtree is skipped, so nothing under /demo may rely on this middleware's session
  // refresh or redirects.
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|demo(?:/|$)|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
}
