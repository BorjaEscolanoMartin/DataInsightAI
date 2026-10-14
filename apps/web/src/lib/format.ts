/** Spanish number format for the UI: thousands dot (also for four digits), decimal comma and a
 *  real minus sign. */
export function formatNumber(n: number, maximumFractionDigits = 2, minimumFractionDigits = 0): string {
  return n
    .toLocaleString("es-ES", { maximumFractionDigits, minimumFractionDigits, useGrouping: "always" })
    .replace("-", "−")
}

const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

/** Spanish short date from an ISO 8601 date or timestamp («2026-09-30» → «30 sep 2026»). It reads
 *  the calendar date from the string itself, with no Date object, so no time zone can shift the
 *  day; null when the value does not start with a valid YYYY-MM-DD. */
export function formatIsoDate(iso: string, options: { year?: boolean } = {}): string | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  if (!match) return null
  const [, year, month, day] = match
  const monthIndex = Number(month) - 1
  if (monthIndex < 0 || monthIndex > 11 || Number(day) < 1 || Number(day) > 31) return null
  const date = `${Number(day)} ${MONTHS[monthIndex]}`
  return options.year === false ? date : `${date} ${year}`
}

/** «1 oct 2024 – 30 sep 2026», or null when either end is missing or not an ISO date. */
export function formatDateRange(min?: string, max?: string): string | null {
  const from = min ? formatIsoDate(min) : null
  const to = max ? formatIsoDate(max) : null
  return from && to ? `${from} – ${to}` : null
}
