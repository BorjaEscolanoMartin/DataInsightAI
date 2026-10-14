import Link from "next/link"

const NAMES = {
  "/projects": "DataInsight AI, ir a Proyectos",
  "/demo": "DataInsight AI, ir a la demo",
} as const

/** Brand link (S17): «DataInsight» and an italic «AI» in the accent, a 44 px target whose name
 *  says where it goes. Signed-in pages link to `/projects`; `/demo`, login and signup link to
 *  `/demo` (D7). */
export function Logo({ href }: { href: keyof typeof NAMES }) {
  return (
    <Link
      href={href}
      aria-label={NAMES[href]}
      className="inline-flex min-h-11 items-center gap-1.5 font-serif text-[26px] font-semibold tracking-[-0.015em] text-fg"
    >
      <span>DataInsight</span>
      <span className="italic tracking-normal text-au">AI</span>
    </Link>
  )
}
