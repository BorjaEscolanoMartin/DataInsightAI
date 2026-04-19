"use client"

import { useState } from "react"
import Link from "next/link"
import { useProjects, useCreateProject, useDeleteProject, useUpdateProject } from "@/lib/queries"
import type { Project } from "@/types/api"

export default function ProjectsPage() {
  const { data: projects, isLoading, error } = useProjects()
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()
  const updateProject = useUpdateProject()

  const [newName, setNewName] = useState("")
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingName, setEditingName] = useState("")

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!newName.trim()) return
    await createProject.mutateAsync({ name: newName.trim() })
    setNewName("")
    setShowForm(false)
  }

  async function handleRename(project: Project) {
    if (!editingName.trim() || editingName === project.name) {
      setEditingId(null)
      return
    }
    await updateProject.mutateAsync({ id: project.id, name: editingName.trim() })
    setEditingId(null)
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-gray-500">Cargando proyectos...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-900/20 p-4 text-red-400">
        Error al cargar proyectos: {error.message}
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-100">Mis proyectos</h1>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500"
        >
          + Nuevo proyecto
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="mb-6 flex gap-3 rounded-xl border border-gray-700 bg-gray-900 p-4"
        >
          <input
            autoFocus
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Nombre del proyecto"
            className="flex-1 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={createProject.isPending}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {createProject.isPending ? "Creando..." : "Crear"}
          </button>
          <button
            type="button"
            onClick={() => setShowForm(false)}
            className="rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-400 hover:text-gray-200"
          >
            Cancelar
          </button>
        </form>
      )}

      {!projects?.length ? (
        <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-gray-700">
          <p className="text-gray-500">No tienes proyectos todavía</p>
          <button
            onClick={() => setShowForm(true)}
            className="text-sm text-indigo-400 hover:underline"
          >
            Crea tu primer proyecto
          </button>
        </div>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <li
              key={project.id}
              className="group rounded-xl border border-gray-800 bg-gray-900 p-5 transition hover:border-gray-600"
            >
              {editingId === project.id ? (
                <input
                  autoFocus
                  type="text"
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  onBlur={() => handleRename(project)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleRename(project)
                    if (e.key === "Escape") setEditingId(null)
                  }}
                  className="w-full rounded border border-indigo-500 bg-gray-800 px-2 py-1 text-sm font-semibold text-gray-100 focus:outline-none"
                />
              ) : (
                <Link href={`/projects/${project.id}`}>
                  <h2 className="truncate font-semibold text-gray-100 hover:text-indigo-400 transition-colors">{project.name}</h2>
                </Link>
              )}

              {project.description && (
                <p className="mt-1 truncate text-sm text-gray-500">{project.description}</p>
              )}

              <p className="mt-3 text-xs text-gray-600">
                {new Date(project.created_at).toLocaleDateString("es-ES")}
              </p>

              <div className="mt-4 flex gap-2 opacity-0 transition group-hover:opacity-100">
                <button
                  onClick={() => {
                    setEditingId(project.id)
                    setEditingName(project.name)
                  }}
                  className="rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-800 hover:text-gray-200"
                >
                  Renombrar
                </button>
                <button
                  onClick={() => {
                    if (confirm(`¿Borrar "${project.name}"?`)) {
                      deleteProject.mutate(project.id)
                    }
                  }}
                  className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-900/20"
                >
                  Borrar
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
