"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
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
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-8 text-center shadow-xl">
        <p className="text-lg font-semibold text-gray-100">Revisa tu email</p>
        <p className="mt-2 text-sm text-gray-400">
          Te hemos enviado un enlace de confirmación a <strong>{email}</strong>.
        </p>
        <Link href="/login" className="mt-6 block text-sm text-indigo-400 hover:underline">
          Volver al login
        </Link>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-8 shadow-xl">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold">
          DataInsight <span className="text-indigo-400">AI</span>
        </h1>
        <p className="mt-1 text-sm text-gray-400">Crea tu cuenta</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-300">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="tu@email.com"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-300">Contraseña</label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="Mínimo 8 caracteres"
          />
        </div>

        {error && (
          <p className="rounded-lg bg-red-900/30 px-3 py-2 text-sm text-red-400">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
        >
          {loading ? "Registrando..." : "Crear cuenta"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        ¿Ya tienes cuenta?{" "}
        <Link href="/login" className="text-indigo-400 hover:underline">
          Inicia sesión
        </Link>
      </p>
    </div>
  )
}
