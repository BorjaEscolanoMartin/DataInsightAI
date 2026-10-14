import { formatNumber } from "@/lib/format"

/** A histogram bin from the API. Since #37 each bin carries its numeric bounds; an outlier bin
 *  has no `start` («< X», values below the IQR bounds) or no `end` («> Y», values above them).
 *  Older analyses only have the `bin` label. */
export interface HistogramDatum {
  bin: string
  count: number
  start?: number | null
  end?: number | null
}

export type OutlierSide = "below" | "above"

export interface HistogramBar {
  /** «25–31,85», «> 162»; the old `bin` label when the bounds are missing. */
  range: string
  count: number
  side: OutlierSide | null
}

export interface HistogramView {
  bars: HistogramBar[]
  /** First and last bound of the bins inside the IQR range, for the axis ends; null for old
   *  analyses, whose axis keeps the labels as they are. */
  axis: { first: string; last: string } | null
  /** «62 por encima de 162», «6 por debajo de 72 · 3 por encima de 128»; null without outliers. */
  note: string | null
}

const MAX_DECIMALS = 2

/** Decimals that write every value exactly, up to two, so the labels of one chart match
 *  («0,1» and «9,0», not «0,1» and «9»). */
function sharedDecimals(values: number[]): number {
  for (let decimals = 0; decimals < MAX_DECIMALS; decimals++) {
    const factor = 10 ** decimals
    if (values.every((v) => Math.abs(Math.round(v * factor) / factor - v) < 1e-9)) return decimals
  }
  return MAX_DECIMALS
}

export function histogramView(data: HistogramDatum[]): HistogramView {
  const hasBounds = data.length > 0 && data.every((d) => d.start !== undefined && d.end !== undefined)
  if (!hasBounds) {
    return {
      bars: data.map((d) => ({ range: d.bin, count: d.count, side: null })),
      axis: null,
      note: null,
    }
  }

  const sideOf = (d: HistogramDatum): OutlierSide | null =>
    d.start === null ? "below" : d.end === null ? "above" : null
  const inner = data.filter((d) => sideOf(d) === null)
  const below = data.find((d) => sideOf(d) === "below")
  const above = data.find((d) => sideOf(d) === "above")

  // The labels a reader compares (axis ends and outlier bounds) share their decimals.
  const first = inner[0]?.start ?? below?.end ?? 0
  const last = inner.at(-1)?.end ?? above?.start ?? first
  const decimals = sharedDecimals([first, last])
  const bound = (v: number) => formatNumber(v, decimals, decimals)

  const bars = data.map((d): HistogramBar => {
    const side = sideOf(d)
    const range =
      side === "below"
        ? `< ${bound(d.end as number)}`
        : side === "above"
          ? `> ${bound(d.start as number)}`
          : `${formatNumber(d.start as number)}–${formatNumber(d.end as number)}`
    return { range, count: d.count, side }
  })

  const parts = [
    below && `${formatNumber(below.count)} por debajo de ${bound(below.end as number)}`,
    above && `${formatNumber(above.count)} por encima de ${bound(above.start as number)}`,
  ].filter(Boolean)

  return {
    bars,
    axis: { first: bound(first), last: bound(last) },
    note: parts.length ? parts.join(" · ") : null,
  }
}
