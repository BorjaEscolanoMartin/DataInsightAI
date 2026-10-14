import { Providers } from "@/components/providers"
import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { Logo } from "@/components/ui/Logo"
import { TEXT_LINK } from "@/components/ui/styles"

async function getUser() {
  const cookieStore = await cookies()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: () => {},
      },
    }
  )
  const {
    data: { user },
  } = await supabase.auth.getUser()
  return user
}

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = await getUser()

  return (
    <Providers>
      <div className="min-h-screen">
        <header className="border-b border-fg">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-2">
            <Logo />
            <div className="flex flex-wrap items-center gap-4">
              <span className="text-sm text-f2 [overflow-wrap:anywhere]">{user?.email}</span>
              <ThemeToggle />
              <LogoutButton />
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-10">{children}</main>
      </div>
    </Providers>
  )
}

function LogoutButton() {
  return (
    <form action="/auth/logout" method="post">
      <button type="submit" className={TEXT_LINK}>
        Cerrar sesión
      </button>
    </form>
  )
}
