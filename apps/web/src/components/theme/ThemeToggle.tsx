"use client"

import { useEffect, useState } from "react"
import { MoonIcon, SunIcon } from "@/components/ui/icons"
import { Segmented, type SegmentedOption } from "@/components/ui/Segmented"
import { applyThemeChoice, readThemeChoice, type ThemeChoice } from "@/lib/theme"

const OPTIONS: SegmentedOption<ThemeChoice>[] = [
  { value: "dark", label: "Oscuro", icon: <MoonIcon /> },
  { value: "light", label: "Claro", icon: <SunIcon /> },
]

export function ThemeToggle() {
  // The server cannot know the stored choice, so the first render shows the default (dark) and the
  // stored one is read after mounting; the page colours are already right thanks to the head script.
  const [choice, setChoice] = useState<ThemeChoice>("dark")

  useEffect(() => {
    setChoice(readThemeChoice())
  }, [])

  function choose(next: ThemeChoice) {
    applyThemeChoice(next)
    setChoice(next)
  }

  // data-theme-toggle: globals.css hides it where light-dark() is missing and the theme cannot change.
  return (
    <div data-theme-toggle>
      <Segmented label="Tema" options={OPTIONS} value={choice} onChange={choose} compactBelowSm />
    </div>
  )
}
