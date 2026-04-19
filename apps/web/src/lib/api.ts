import { createClient } from "./supabase"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function authFetch(path: string, init?: RequestInit): Promise<Response> {
  const supabase = createClient()
  const {
    data: { session },
  } = await supabase.auth.getSession()

  return fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
      ...init?.headers,
    },
  })
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? `API error ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  get: <T>(path: string) => authFetch(path).then(handleResponse<T>),
  post: <T>(path: string, body: unknown) =>
    authFetch(path, { method: "POST", body: JSON.stringify(body) }).then(handleResponse<T>),
  patch: <T>(path: string, body: unknown) =>
    authFetch(path, { method: "PATCH", body: JSON.stringify(body) }).then(handleResponse<T>),
  delete: (path: string) => authFetch(path, { method: "DELETE" }).then(handleResponse<void>),

  downloadPdf: async (path: string): Promise<Blob> => {
    const res = await authFetch(path)
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(body.detail ?? `API error ${res.status}`)
    }
    return res.blob()
  },
}
