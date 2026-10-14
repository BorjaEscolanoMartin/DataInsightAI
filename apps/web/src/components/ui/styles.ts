// Shared control styles (docs: odd/tasks/redesign.md, S2 and S6): primary button in ink with
// inverse text, and text links in the accent; both at least 44 px tall.
export const PRIMARY_BUTTON =
  "inline-flex min-h-11 items-center justify-center bg-fg px-5 text-sm font-semibold text-inv hover:opacity-90 disabled:opacity-50"

export const TEXT_LINK =
  "inline-flex min-h-11 items-center text-sm font-medium text-fg underline underline-offset-4 hover:text-au"

export const FIELD_LABEL = "mb-1 block text-sm font-medium text-fg"

export const FIELD_INPUT =
  "min-h-11 w-full border border-f3 bg-s1 px-3 text-sm text-fg placeholder:text-f3 focus:border-fg focus:outline-2 focus:outline-offset-2 focus:outline-au"

export const ERROR_NOTE = "border-l-2 border-fg pl-3 text-sm text-fg"
