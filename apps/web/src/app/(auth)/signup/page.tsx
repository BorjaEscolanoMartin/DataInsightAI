"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { AUTH_FIELD, ERROR_NOTE, FIELD_LABEL, PRIMARY_BUTTON } from "@/components/ui/styles"
import { createClient } from "@/lib/supabase"

export default function SignupPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const supabase = createClient()
    const { data, error } = await supabase.auth.signUp({ email, password })

    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }

    if (data.session) {
      router.push("/projects")
      return
    }

    setDone(true)
  }

  if (done) {
    return (
      <>
        <h2 id="auth-form-title" className="font-serif text-[30px] font-medium text-fg">
          Revisa tu email
        </h2>
        <p className="mt-2 text-sm text-f2 [overflow-wrap:anywhere]">
          Te hemos enviado un enlace de confirmación a <strong className="text-fg">{email}</strong>.
        </p>
        <p className="mt-5 border-t border-ln pt-[18px] text-sm">
          <Link href="/login" className="font-medium text-au underline underline-offset-4">
            Volver al login
          </Link>
        </p>
      </>
    )
  }

  return (
    <>
      <h2 id="auth-form-title" className="font-serif text-[30px] font-medium text-fg">
        Crear cuenta
      </h2>
      <p className="mt-1.5 text-sm text-f2">Con una cuenta puedes subir tus propios CSV.</p>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-[18px]">
        <div>
          <label htmlFor="signup-email" className={FIELD_LABEL}>
            Email
          </label>
          <input
            id="signup-email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={AUTH_FIELD}
            placeholder="tu@email.com"
          />
        </div>

        <div>
          <label htmlFor="signup-password" className={FIELD_LABEL}>
            Contraseña
          </label>
          <input
            id="signup-password"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            aria-describedby="signup-password-hint"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={AUTH_FIELD}
          />
          <p id="signup-password-hint" className="mt-1 text-xs text-f3">
            Mínimo 8 caracteres
          </p>
        </div>

        {error && (
          <p role="alert" className={ERROR_NOTE}>
            {error}
          </p>
        )}

        <button type="submit" disabled={loading} className={`${PRIMARY_BUTTON} mt-1.5 w-full`}>
          {loading ? "Registrando..." : "Crear cuenta"}
        </button>
      </form>

      <p className="mt-5 border-t border-ln pt-[18px] text-sm text-f2">
        ¿Ya tienes cuenta?{" "}
        <Link href="/login" className="font-medium text-au underline underline-offset-4">
          Inicia sesión
        </Link>
      </p>
    </>
  )
}
