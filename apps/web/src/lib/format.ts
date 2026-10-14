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
  return shortDate(Number(day), monthIndex, year, options.year !== false)
}

/** Spanish short date of an instant («2026-10-01T23:30:00Z» → «2 oct 2026» in Madrid): the
 *  calendar day in the given IANA time zone, by default the browser's. For instants (with a time),
 *  not for plain dates, which formatIsoDate reads as written; null when the value is not an
 *  instant. */
export function formatInstantDate(iso: string, options: { timeZone?: string } = {}): string | null {
  const instant = new Date(iso)
  if (Number.isNaN(instant.getTime())) return null
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: options.timeZone,
    year: "numeric",
    month: "numeric",
    day: "numeric",
  }).formatToParts(instant)
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    Number(parts.find((p) => p.type === type)?.value)
  return shortDate(part("day"), part("month") - 1, String(part("year")))
}

/** «2 oct 2026», or «2 oct» without the year: the one Spanish short date format. */
function shortDate(day: number, monthIndex: number, year: string, withYear = true): string {
  const date = `${day} ${MONTHS[monthIndex]}`
  return withYear ? `${date} ${year}` : date
}

/** «1 oct 2024 – 30 sep 2026», or null when either end is missing or not an ISO date. */
export function formatDateRange(min?: string, max?: string): string | null {
  const from = min ? formatIsoDate(min) : null
  const to = max ? formatIsoDate(max) : null
  return from && to ? `${from} – ${to}` : null
}

const MAX_DISTINCT_DECIMALS = 10

/** Fewest decimals that write each value differently from the one before it, unless the two
 *  are really equal (bounds 0,0012 and 0,0036 need three: «0,001» and «0,004»). */
export function distinctDecimals(values: number[]): number {
  for (let decimals = 0; decimals < MAX_DISTINCT_DECIMALS; decimals++) {
    const written = values.map((v) => formatNumber(v, decimals, decimals))
    if (values.every((v, i) => i === 0 || v === values[i - 1] || written[i] !== written[i - 1])) {
      return decimals
    }
  }
  return MAX_DISTINCT_DECIMALS
}
