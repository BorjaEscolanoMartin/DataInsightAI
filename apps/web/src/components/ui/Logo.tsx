import Link from "next/link"

/** Brand link (S17, S26): «DataInsight» and an italic «AI» in the accent, a 44 px target. It goes
 *  to `/` on every page, where the middleware sends a visitor to the demo and a signed-in user to
 *  their projects. */
export function Logo() {
  return (
    <Link
      href="/"
      aria-label="DataInsight AI, ir al inicio"
      className="inline-flex min-h-11 items-center gap-1.5 font-serif text-[26px] font-semibold tracking-[-0.015em] text-fg"
    >
      <span>DataInsight</span>
      <span className="italic tracking-normal text-au">AI</span>
    </Link>
  )
}
