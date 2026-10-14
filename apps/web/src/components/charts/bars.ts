import type { ChartSpec } from "@/types/api"

/** Whether a bar chart counts the values of a whole-number column (one column per value, in
 *  value order) rather than categories (a ranking). The API (#37) only sends a numeric `value`
 *  in the bars of whole-number columns with few distinct values; category bars carry just
 *  `name` and `count`. */
export function isValueBars(chart: ChartSpec): boolean {
  return chart.data.length > 0 && chart.data.every((d) => typeof d.value === "number")
}
