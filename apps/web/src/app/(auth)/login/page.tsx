"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ERROR_NOTE, FIELD_INPUT, FIELD_LABEL, PRIMARY_BUTTON } from "@/components/ui/styles"
import { createClient } from "@/lib/supabase"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const supabase = createClient()
    const { error } = await supabase.auth.signInWithPassword({ email, password })

    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }

    router.push("/projects")
    router.refresh()
  }

  return (
    <div className="border-t-2 border-fg pt-6">
      <h1 className="font-serif text-3xl text-fg">Inicia sesión en tu cuenta</h1>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        <div>
          <label htmlFor="login-email" className={FIELD_LABEL}>
            Email
          </label>
          <input
            id="login-email"
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
          <label htmlFor="login-password" className={FIELD_LABEL}>
            Contraseña
          </label>
          <input
            id="login-password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={FIELD_INPUT}
          />
        </div>

        {error && (
          <p role="alert" className={ERROR_NOTE}>
            {error}
          </p>
        )}

        <button type="submit" disabled={loading} className={`${PRIMARY_BUTTON} w-full`}>
          {loading ? "Entrando..." : "Iniciar sesión"}
        </button>
      </form>

      <p className="mt-8 text-sm text-f2">
        ¿No tienes cuenta?{" "}
        <Link href="/signup" className="text-au underline underline-offset-4">
          Regístrate
        </Link>
      </p>

      <p className="mt-2 text-sm text-f2">
        <Link href="/demo" className="text-au underline underline-offset-4">
          Ver demo
        </Link>{" "}
        sin registrarte
      </p>
    </div>
  )
}
