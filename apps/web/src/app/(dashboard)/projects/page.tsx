"use client"

import { useState } from "react"
import Link from "next/link"
import { useProjects, useCreateProject, useDeleteProject, useUpdateProject } from "@/lib/queries"
import { ERROR_NOTE, FIELD_INPUT, FIELD_LABEL, PRIMARY_BUTTON, SECONDARY_BUTTON } from "@/components/ui/styles"
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
    return <p className="text-f2">Cargando proyectos...</p>
  }

  if (error) {
    return (
      <p role="alert" className={ERROR_NOTE}>
        Error al cargar proyectos: {error.message}
      </p>
    )
  }

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="font-serif text-4xl text-fg md:text-5xl">Mis proyectos</h1>
        <button type="button" onClick={() => setShowForm(true)} className={PRIMARY_BUTTON}>
          Nuevo proyecto
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="flex flex-wrap items-end gap-3 border-t-2 border-fg pt-5"
        >
          <div className="min-w-0 flex-1 basis-64">
            <label htmlFor="new-project-name" className={FIELD_LABEL}>
              Nombre del proyecto
            </label>
            <input
              id="new-project-name"
              autoFocus
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className={FIELD_INPUT}
            />
          </div>
          <button type="submit" disabled={createProject.isPending} className={PRIMARY_BUTTON}>
            {createProject.isPending ? "Creando..." : "Crear"}
          </button>
          <button type="button" onClick={() => setShowForm(false)} className={SECONDARY_BUTTON}>
            Cancelar
          </button>
        </form>
      )}

      {!projects?.length ? (
        <div className="border-t-2 border-fg pt-5">
          <p className="text-f2">No tienes proyectos todavía</p>
          <button type="button" onClick={() => setShowForm(true)} className={SECONDARY_BUTTON}>
            Crea tu primer proyecto
          </button>
        </div>
      ) : (
        <ul className="border-t-2 border-fg">
          {projects.map((project) => (
            <li
              key={project.id}
              className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-b border-ln py-4"
            >
              <div className="min-w-0 flex-1 basis-64">
                {editingId === project.id ? (
                  <input
                    autoFocus
                    type="text"
                    aria-label={`Nuevo nombre de ${project.name}`}
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    onBlur={() => handleRename(project)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleRename(project)
                      if (e.key === "Escape") setEditingId(null)
                    }}
                    className={FIELD_INPUT}
                  />
                ) : (
                  <h2 className="font-serif text-2xl leading-snug [overflow-wrap:anywhere]">
                    <Link href={`/projects/${project.id}`} className="text-fg hover:text-au">
                      {project.name}
                    </Link>
                  </h2>
                )}
                {project.description && (
                  <p className="mt-1 text-sm text-f2 [overflow-wrap:anywhere]">{project.description}</p>
                )}
                <p className="mt-1 text-xs tabular-nums text-f3">
                  {new Date(project.created_at).toLocaleDateString("es-ES")}
                </p>
              </div>

              <div className="flex gap-4">
                <button
                  type="button"
                  aria-label={`Renombrar ${project.name}`}
                  onClick={() => {
                    setEditingId(project.id)
                    setEditingName(project.name)
                  }}
                  className={SECONDARY_BUTTON}
                >
                  Renombrar
                </button>
                <button
                  type="button"
                  aria-label={`Borrar ${project.name}`}
                  onClick={() => {
                    if (confirm(`¿Borrar "${project.name}"?`)) {
                      deleteProject.mutate(project.id)
                    }
                  }}
                  className={SECONDARY_BUTTON}
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
