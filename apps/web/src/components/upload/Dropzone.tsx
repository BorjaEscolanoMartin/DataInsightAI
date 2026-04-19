"use client"

import { useCallback } from "react"
import { useDropzone } from "react-dropzone"

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

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    maxSize: 50 * 1024 * 1024,
    maxFiles: 1,
    disabled: isLoading,
  })

  const rejection = fileRejections[0]?.errors[0]

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition
          ${isLoading ? "cursor-not-allowed opacity-50" : ""}
          ${isDragActive ? "border-indigo-400 bg-indigo-900/20" : "border-gray-700 hover:border-gray-500 hover:bg-gray-900/50"}`}
      >
        <input {...getInputProps()} />
        <svg
          className="mb-4 h-10 w-10 text-gray-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
          />
        </svg>
        {isLoading ? (
          <p className="text-sm text-gray-400">Subiendo y analizando...</p>
        ) : isDragActive ? (
          <p className="text-sm text-indigo-400">Suelta el archivo aquí</p>
        ) : (
          <>
            <p className="text-sm text-gray-300">
              Arrastra tu CSV aquí o{" "}
              <span className="text-indigo-400 underline">selecciona un archivo</span>
            </p>
            <p className="mt-1 text-xs text-gray-600">Solo .csv · máx. 50 MB</p>
          </>
        )}
      </div>
      {rejection && (
        <p className="text-sm text-red-400">
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
