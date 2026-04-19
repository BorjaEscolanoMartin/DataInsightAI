import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "./api"
import { createClient } from "./supabase"
import type { Project, ProjectCreate, ProjectUpdate, DatasetWithAnalysis, Analysis } from "@/types/api"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => api.get<Project[]>("/api/projects"),
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ["projects", id],
    queryFn: () => api.get<Project>(`/api/projects/${id}`),
    enabled: !!id,
  })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ProjectCreate) => api.post<Project>("/api/projects", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  })
}

export function useUpdateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string } & ProjectUpdate) =>
      api.patch<Project>(`/api/projects/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  })
}

export function useDeleteProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/projects/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  })
}

export function useAnalysisPoll(analysisId: string | undefined) {
  return useQuery({
    queryKey: ["analyses", analysisId],
    queryFn: () => api.get<Analysis>(`/api/analyses/${analysisId}`),
    enabled: !!analysisId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === "completed" || status === "failed") return false
      return 2000
    },
  })
}

export function useProjectDatasets(projectId: string) {
  return useQuery({
    queryKey: ["projects", projectId, "datasets"],
    queryFn: () => api.get<DatasetWithAnalysis[]>(`/api/projects/${projectId}/datasets`),
    enabled: !!projectId,
  })
}

export function useUploadDataset(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File): Promise<DatasetWithAnalysis> => {
      const supabase = createClient()
      const {
        data: { session },
      } = await supabase.auth.getSession()

      const formData = new FormData()
      formData.append("file", file)

      const res = await fetch(`${API_URL}/api/projects/${projectId}/datasets`, {
        method: "POST",
        headers: session?.access_token
          ? { Authorization: `Bearer ${session.access_token}` }
          : {},
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail ?? `Error ${res.status}`)
      }
      return res.json()
    },
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["projects", projectId, "datasets"] }),
  })
}
