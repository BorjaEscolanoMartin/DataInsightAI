export type ThemeChoice = "system" | "light" | "dark"

export const THEME_STORAGE_KEY = "theme"

// Only an explicit choice is stored; "system" means no stored value and no data-theme attribute,
// so the CSS follows prefers-color-scheme.
const STORED_CHOICES: readonly ThemeChoice[] = ["light", "dark"]

// Inlined in <head> so the stored theme applies before the first paint. Storage access is wrapped
// because reading window.localStorage itself throws when site data is blocked.
export const THEME_SCRIPT = `try {
  var choice = window.localStorage.getItem(${JSON.stringify(THEME_STORAGE_KEY)});
  if (${JSON.stringify(STORED_CHOICES)}.indexOf(choice) !== -1) {
    document.documentElement.setAttribute("data-theme", choice);
  }
} catch (e) {}`

export function readThemeChoice(): ThemeChoice {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY)
    return STORED_CHOICES.find((choice) => choice === stored) ?? "system"
  } catch {
    return "system"
  }
}

export function applyThemeChoice(choice: ThemeChoice): void {
  const root = document.documentElement
  if (choice === "system") {
    root.removeAttribute("data-theme")
  } else {
    root.setAttribute("data-theme", choice)
  }
  try {
    if (choice === "system") {
      window.localStorage.removeItem(THEME_STORAGE_KEY)
    } else {
      window.localStorage.setItem(THEME_STORAGE_KEY, choice)
    }
  } catch {
    // The choice still applies to this page; it just is not remembered.
  }
}
