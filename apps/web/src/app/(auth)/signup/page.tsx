"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ERROR_NOTE, FIELD_INPUT, FIELD_LABEL, PRIMARY_BUTTON } from "@/components/ui/styles"
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
      <div className="border-t-2 border-fg pt-6">
        <h1 className="font-serif text-3xl text-fg">Revisa tu email</h1>
        <p className="mt-2 text-sm text-f2 [overflow-wrap:anywhere]">
          Te hemos enviado un enlace de confirmación a <strong className="text-fg">{email}</strong>.
        </p>
        <Link href="/login" className="mt-6 inline-flex min-h-11 items-center text-sm text-au underline underline-offset-4">
          Volver al login
        </Link>
      </div>
    )
  }

  return (
    <div className="border-t-2 border-fg pt-6">
      <h1 className="font-serif text-3xl text-fg">Crea tu cuenta</h1>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
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
            className={FIELD_INPUT}
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
            className={FIELD_INPUT}
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

        <button type="submit" disabled={loading} className={`${PRIMARY_BUTTON} w-full`}>
          {loading ? "Registrando..." : "Crear cuenta"}
        </button>
      </form>

      <p className="mt-8 text-sm text-f2">
        ¿Ya tienes cuenta?{" "}
        <Link href="/login" className="text-au underline underline-offset-4">
          Inicia sesión
        </Link>
      </p>
    </div>
  )
}
