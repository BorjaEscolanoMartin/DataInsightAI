import Link from "next/link"

const BRAND_CLASS =
  "inline-flex min-h-11 items-center gap-1.5 font-serif text-[26px] font-semibold tracking-[-0.015em] text-fg"

function Brand() {
  return (
    <>
      <span>DataInsight</span> <span className="italic tracking-normal text-au">AI</span>
    </>
  )
}

/** Brand (S17, S31): «DataInsight» and an italic «AI» in the accent, 44 px tall. By default a link
 *  to `/`, where the middleware sends a visitor to the login and a signed-in user to their
 *  projects. On login and signup (`asLink={false}`) it is plain text with the same look: nothing to
 *  focus and no pointer, since `/` would lead back to the login. */
export function Logo({ asLink = true }: { asLink?: boolean }) {
  if (!asLink) {
    return (
      <span className={`${BRAND_CLASS} cursor-default`}>
        <Brand />
      </span>
    )
  }
  return (
    <Link href="/" aria-label="DataInsight AI, ir al inicio" className={BRAND_CLASS}>
      <Brand />
    </Link>
  )
}
