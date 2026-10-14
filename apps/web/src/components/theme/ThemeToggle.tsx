"use client"

import { useEffect, useState } from "react"
import { applyThemeChoice, readThemeChoice, type ThemeChoice } from "@/lib/theme"

const OPTIONS: { choice: ThemeChoice; label: string }[] = [
  { choice: "system", label: "Sistema" },
  { choice: "light", label: "Claro" },
  { choice: "dark", label: "Oscuro" },
]

export function ThemeToggle() {
  // The server cannot know the stored choice, so the first render shows "system" and the stored
  // one is read after mounting; the page colours are already right thanks to the head script.
  const [choice, setChoice] = useState<ThemeChoice>("system")

  useEffect(() => {
    setChoice(readThemeChoice())
  }, [])

  function choose(next: ThemeChoice) {
    applyThemeChoice(next)
    setChoice(next)
  }

  // data-theme-toggle: globals.css hides it where light-dark() is missing and the theme cannot change.
  return (
    <div role="group" aria-label="Tema" data-theme-toggle className="flex border border-ln">
      {OPTIONS.map(({ choice: option, label }) => (
        <button
          key={option}
          type="button"
          aria-pressed={choice === option}
          onClick={() => choose(option)}
          className="min-h-11 min-w-11 px-3 text-sm text-f2 hover:text-fg aria-pressed:bg-fg aria-pressed:text-inv"
        >
          {label}
        </button>
      ))}
    </div>
  )
}
