import { formatNumber } from "@/lib/format"

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

const MIN_INTERVALS = 3
const MAX_INTERVALS = 5
const ROUND_STEPS = [1, 2, 2.5, 5]

/** A count axis from 0 (W3, insights-yearly S6): among the steps 1, 2, 2,5 and 5 × 10ⁿ (whole,
 *  since rows are counted) that cover the maximum in 3 to 5 intervals, the one with the lowest
 *  top, and of those the fewest intervals (640 → 0–750 by 250, 346 → 0–400 by 100,
 *  950 → 0–1.000 by 250). */
export function countAxis(max: number): { domain: [number, number]; ticks: number[] } {
  if (!(max > 0)) return { domain: [0, 1], ticks: [0, 1] }
  let best: { step: number; intervals: number } | null = null
  for (let power = 0; 10 ** power <= max; power++) {
    for (const multiple of ROUND_STEPS) {
      const step = multiple * 10 ** power
      if (!Number.isInteger(step)) continue
      const intervals = Math.max(MIN_INTERVALS, Math.ceil(tidy(max / step)))
      if (intervals > MAX_INTERVALS) continue
      const top = step * intervals
      if (!best || top < best.step * best.intervals ||
          (top === best.step * best.intervals && intervals < best.intervals)) {
        best = { step, intervals }
      }
    }
  }
  // A maximum below 1 still counts in whole rows: 0–3 by 1.
  const { step, intervals } = best ?? { step: 1, intervals: MIN_INTERVALS }
  const ticks = Array.from({ length: intervals + 1 }, (_, i) => i * step)
  return { domain: [0, ticks[ticks.length - 1]], ticks }
}

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
