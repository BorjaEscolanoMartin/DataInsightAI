"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { AUTH_FIELD, ERROR_NOTE, FIELD_LABEL, PRIMARY_BUTTON } from "@/components/ui/styles"
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
    <>
      <h2 id="auth-form-title" className="font-serif text-[30px] font-medium text-fg">
        Iniciar sesión
      </h2>
      <p className="mt-1.5 text-sm text-f2">Entra para ver tus proyectos y subir datos.</p>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-[18px]">
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
            className={AUTH_FIELD}
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
            className={AUTH_FIELD}
          />
        </div>

        {error && (
          <p role="alert" className={ERROR_NOTE}>
            {error}
          </p>
        )}

        <button type="submit" disabled={loading} className={`${PRIMARY_BUTTON} mt-1.5 w-full`}>
          {loading ? "Entrando..." : "Iniciar sesión"}
        </button>
      </form>

      <p className="mt-5 border-t border-ln pt-[18px] text-sm text-f2">
        ¿No tienes cuenta?{" "}
        <Link href="/signup" className="font-medium text-au underline underline-offset-4">
          Regístrate
        </Link>
      </p>
    </>
  )
}
