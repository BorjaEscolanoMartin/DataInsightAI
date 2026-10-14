"use client"

import type { ReactNode } from "react"

export interface SegmentedOption<T extends string> {
  value: T
  label: string
  icon?: ReactNode
}

interface Props<T extends string> {
  /** Accessible name of the group. */
  label: string
  options: SegmentedOption<T>[]
  value: T
  onChange: (value: T) => void
  /** Below `sm`, show only the icons; the text stays as visually hidden text (S18, D8). */
  compactBelowSm?: boolean
  /** Below `sm`, take the full width and share it between the options. */
  stretchBelowSm?: boolean
}

/** Segmented control (S18, S19): a group of buttons with `aria-pressed` on a recessed rail. */
export function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
  compactBelowSm,
  stretchBelowSm,
}: Props<T>) {
  return (
    <div
      role="group"
      aria-label={label}
      className={`ctl-track gap-0.5 ${stretchBelowSm ? "flex w-full sm:inline-flex sm:w-auto" : "inline-flex"}`}
    >
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={option.value === value}
          onClick={() => onChange(option.value)}
          className={`ctl-segment inline-flex min-h-11 min-w-11 items-center justify-center gap-1.5 px-3 text-center text-sm font-medium ${stretchBelowSm ? "flex-1 sm:flex-none" : ""}`}
        >
          {option.icon}
          <span className={compactBelowSm && option.icon ? "sr-only sm:not-sr-only" : undefined}>
            {option.label}
          </span>
        </button>
      ))}
    </div>
  )
}
