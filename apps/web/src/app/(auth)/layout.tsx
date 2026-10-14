import Link from "next/link"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { ArrowRightIcon } from "@/components/ui/icons"
import { Logo } from "@/components/ui/Logo"
import { PRIMARY_BUTTON } from "@/components/ui/styles"

/** Login and signup (S27): the app's pitch with a way into the demo on the left, the page's form
 *  in a raised panel on the right; stacked on mobile. Each page titles its panel with an `h2`
 *  whose id is `auth-form-title`. */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-ln">
        <div className="mx-auto flex max-w-[1180px] flex-wrap items-center justify-between gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
          <Logo asLink={false} />
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto flex max-w-[1180px] flex-wrap items-start gap-x-[72px] gap-y-12 px-4 pb-20 pt-16 sm:px-6">
        <section aria-labelledby="auth-pitch" className="min-w-0 flex-[999_1_460px]">
          <p className="mb-3.5 text-[13px] font-semibold uppercase tracking-[0.08em] text-au">
            Análisis de datos con IA
          </p>
          <h1
            id="auth-pitch"
            className="max-w-[560px] font-serif text-[40px] font-medium leading-[1.08] tracking-[-0.015em] text-fg sm:text-5xl"
          >
            De un CSV a un informe con hallazgos y previsiones
          </h1>
          <p className="mt-4 max-w-[520px] text-[17px] leading-relaxed text-f2">
            Perfil de cada columna, gráficos automáticos, hallazgos redactados por Claude y una
            previsión cuando hay una columna de fecha.
          </p>
          <div aria-hidden="true" className="gold-rule mt-8 max-w-[520px]" />
          <div className="mt-7 max-w-[520px]">
            <h2 className="font-serif text-2xl font-medium text-fg">¿Estás revisando el proyecto?</h2>
            <p className="mt-2 text-[15px] leading-relaxed text-f2">
              Mira dos análisis completos, de ventas diarias y de viviendas, sin crear una cuenta.
            </p>
            <Link href="/demo" className={`${PRIMARY_BUTTON} mt-4 gap-2`}>
              Ver la demo sin registrarte
              <ArrowRightIcon />
            </Link>
            <p className="mt-3 text-[13px] text-f3">Datos sintéticos · sin registro</p>
          </div>
        </section>
        <section
          aria-labelledby="auth-form-title"
          className="auth-card w-full max-w-[440px] flex-[1_1_360px] p-6 sm:p-8"
        >
          {children}
        </section>
      </main>
    </div>
  )
}
