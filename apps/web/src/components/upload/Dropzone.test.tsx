import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { Dropzone } from "./Dropzone"

function choose(container: HTMLElement, file: File) {
  const input = container.querySelector('input[type="file"]') as HTMLInputElement
  fireEvent.change(input, { target: { files: [file] } })
}

describe("Dropzone", () => {
  it("opens the file picker from a real button", () => {
    render(<Dropzone onFile={vi.fn()} />)

    const button = screen.getByRole("button", { name: "Seleccionar archivo" })
    expect(button.getAttribute("type")).toBe("button")
  })

  it("passes a CSV to onFile", async () => {
    const onFile = vi.fn()
    const { container } = render(<Dropzone onFile={onFile} />)
    const file = new File(["a,b\n1,2"], "datos.csv", { type: "text/csv" })

    choose(container, file)

    await waitFor(() => expect(onFile).toHaveBeenCalledWith(file))
  })

  it("rejects a file that is not a CSV", async () => {
    const onFile = vi.fn()
    const { container } = render(<Dropzone onFile={onFile} />)

    choose(container, new File(["hola"], "notas.txt", { type: "text/plain" }))

    expect(await screen.findByText("Solo se aceptan archivos .csv")).toBeTruthy()
    expect(onFile).not.toHaveBeenCalled()
  })

  it("rejects a CSV over 50 MB", async () => {
    const onFile = vi.fn()
    const { container } = render(<Dropzone onFile={onFile} />)
    const file = new File(["a"], "grande.csv", { type: "text/csv" })
    Object.defineProperty(file, "size", { value: 50 * 1024 * 1024 + 1 })

    choose(container, file)

    expect(await screen.findByText("El archivo supera los 50 MB")).toBeTruthy()
    expect(onFile).not.toHaveBeenCalled()
  })
})
