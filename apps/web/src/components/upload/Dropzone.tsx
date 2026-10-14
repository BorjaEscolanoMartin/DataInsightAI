"use client"

import { useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { PRIMARY_BUTTON } from "@/components/ui/styles"

interface Props {
  onFile: (file: File) => void
  isLoading?: boolean
}

export function Dropzone({ onFile, isLoading }: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) onFile(accepted[0])
    },
    [onFile]
  )

  // The zone only takes drops; the file picker opens from a real button, which is focusable and
  // announced as a button (the zone itself has no role a screen reader can use).
  const { getRootProps, getInputProps, isDragActive, fileRejections, open } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    maxSize: 50 * 1024 * 1024,
    maxFiles: 1,
    disabled: isLoading,
    noClick: true,
    noKeyboard: true,
  })

  const rejection = fileRejections[0]?.errors[0]

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`flex flex-col items-center justify-center gap-4 border border-dashed bg-s1 px-6 py-12 text-center
          ${isDragActive ? "border-au" : "border-f3"} ${isLoading ? "opacity-60" : ""}`}
      >
        <input {...getInputProps()} />
        <p className="font-serif text-2xl text-fg">
          {isLoading
            ? "Subiendo y analizando..."
            : isDragActive
              ? "Suelta el archivo aquí"
              : "Arrastra aquí tu fichero"}
        </p>
        <button type="button" onClick={open} disabled={isLoading} className={PRIMARY_BUTTON}>
          Seleccionar archivo
        </button>
        <p className="text-xs text-f3">Solo .csv · máximo 50 MB</p>
      </div>
      {rejection && (
        <p role="alert" className="border-l-2 border-fg pl-3 text-sm text-fg">
          {rejection.code === "file-too-large"
            ? "El archivo supera los 50 MB"
            : rejection.code === "file-invalid-type"
              ? "Solo se aceptan archivos .csv"
              : rejection.message}
        </p>
      )}
    </div>
  )
}
