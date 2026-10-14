import { formatNumber } from "@/lib/format"

/** Top of a count axis: the largest value rounded up to the next multiple of its leading power
 *  of ten (346 → 400, 950 → 1.000), not to the next big step (W3). */
export function niceAxisMax(max: number): number {
  if (!(max > 0)) return 1
  const unit = 10 ** Math.floor(Math.log10(max))
  return Math.ceil(max / unit) * unit
}

/** Axis tick numbers in Spanish («1.000», «0,5»). */
export function numberTick(value: number): string {
  return formatNumber(value)
}

const MARGIN = 0.05
const TARGET_TICKS = 5

/** The smallest of 1, 2, 2,5 and 5 times a power of ten that is at least `raw`. */
function niceStep(raw: number): number {
  const unit = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].find((m) => m * unit >= raw - 1e-12) ?? 10
  return step * unit
}

/** Drops the float noise of multiples of a decimal step (0.6000000000000001 → 0.6). */
const tidy = (v: number) => Number(v.toPrecision(12))

/** A scatter axis fitted to its data (W4): a 5 % margin on each side, never below 0 when every
 *  value is 0 or more, and round ticks at a 1, 2, 2,5 or 5 step that cover the margin. Null
 *  without values. */
export function scatterAxis(values: number[]): { domain: [number, number]; ticks: number[] } | null {
  if (!values.length) return null
  const min = Math.min(...values)
  const max = Math.max(...values)
  const pad = (max - min) * MARGIN || Math.abs(max) * MARGIN || 1
  const low = min >= 0 ? Math.max(0, min - pad) : min - pad
  const high = max + pad
  const step = niceStep((high - low) / TARGET_TICKS)
  const first = Math.floor(tidy(low / step))
  const last = Math.ceil(tidy(high / step))
  const ticks = Array.from({ length: last - first + 1 }, (_, i) => tidy((first + i) * step))
  return { domain: [ticks[0], ticks[ticks.length - 1]], ticks }
}
