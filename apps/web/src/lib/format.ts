/** Spanish number format for the UI: thousands dot (also for four digits), decimal comma and a
 *  real minus sign. */
export function formatNumber(n: number, maximumFractionDigits = 2, minimumFractionDigits = 0): string {
  return n
    .toLocaleString("es-ES", { maximumFractionDigits, minimumFractionDigits, useGrouping: "always" })
    .replace("-", "−")
}
