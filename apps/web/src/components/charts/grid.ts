// Whole class names, one per span: Tailwind only generates the classes it finds written in the
// source, never ones built at runtime.
const TABLET_SPAN: Record<number, string> = { 2: "md:col-span-2" }
const DESKTOP_SPAN: Record<number, string> = {
  1: "xl:col-span-1",
  2: "xl:col-span-2",
  3: "xl:col-span-3",
}

/** Classes for the last of `count` small charts so that it reaches the end of its row (W6): the
 *  grid has 2 columns on tablets (md) and 3 on desktops (xl), so an incomplete last row leaves
 *  no gap. Empty when the last row is already full at both widths. */
export function lastSpanClass(count: number): string {
  if (count === 0) return ""
  const onTablet = count % 2 === 1 ? 2 : 1
  const onDesktop = 3 - ((count - 1) % 3)
  const classes: string[] = []
  if (onTablet > 1) classes.push(TABLET_SPAN[onTablet])
  // xl must also undo the tablet span when the desktop row is already full.
  if (onDesktop > 1 || onTablet > 1) classes.push(DESKTOP_SPAN[onDesktop])
  return classes.join(" ")
}
