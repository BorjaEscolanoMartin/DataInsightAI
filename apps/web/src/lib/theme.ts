export type ThemeChoice = "dark" | "light"

export const THEME_STORAGE_KEY = "theme"

// Dark is the CSS default (S24): with no valid stored choice there is no data-theme attribute and
// the page is dark from the first paint. Any other stored value (the old "system", a corrupt one)
// is ignored.
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
    return STORED_CHOICES.find((choice) => choice === stored) ?? "dark"
  } catch {
    return "dark"
  }
}

export function applyThemeChoice(choice: ThemeChoice): void {
  document.documentElement.setAttribute("data-theme", choice)
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, choice)
  } catch {
    // The choice still applies to this page; it just is not remembered.
  }
}
