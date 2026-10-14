/** Classes for the last of `count` small charts so that it reaches the end of its row (W6): the
 *  grid has 2 columns on tablets (md) and 3 on desktops (xl), so an incomplete last row leaves
 *  no gap. Empty when the last row is already full at both widths. */
export function lastSpanClass(count: number): string {
  if (count === 0) return ""
  const classes: string[] = []
  if (count % 2 === 1) classes.push("md:col-span-2")
  const onDesktop = 3 - ((count - 1) % 3)
  // xl must also undo the tablet span when the desktop row is already full.
  if (onDesktop > 1 || classes.length) classes.push(`xl:col-span-${onDesktop}`)
  return classes.join(" ")
}
