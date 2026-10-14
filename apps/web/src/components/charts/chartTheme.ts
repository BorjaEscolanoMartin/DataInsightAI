// Shared Recharts styling. Colours are CSS variables, so the charts follow the theme without
// re-rendering (docs: odd/tasks/redesign.md, S5 and S12).
export const AXIS_TICK = { fontSize: 11, fill: "var(--f3)" }
export const AXIS_LINE = { stroke: "var(--ln)" }
export const GRID_STROKE = "var(--ln)"

export const TOOLTIP_PROPS = {
  contentStyle: {
    background: "var(--s1)",
    border: "1px solid var(--ln)",
    borderRadius: 0,
    color: "var(--fg)",
    fontSize: 12,
  },
  labelStyle: { color: "var(--f2)" },
  itemStyle: { color: "var(--fg)" },
  cursor: { fill: "var(--s2)", stroke: "var(--ln)" },
}
