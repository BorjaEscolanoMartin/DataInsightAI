import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { Logo } from "@/components/ui/Logo"

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-fg">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-2">
          <Logo href="/demo" />
          <ThemeToggle />
        </div>
      </header>
      <main className="flex flex-1 items-start justify-center px-4 py-16">
        <div className="w-full max-w-sm">{children}</div>
      </main>
    </div>
  )
}
