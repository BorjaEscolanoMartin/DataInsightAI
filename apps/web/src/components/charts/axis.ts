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
