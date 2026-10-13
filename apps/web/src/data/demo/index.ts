import type { AnalysisViewProps } from "@/components/analysis/AnalysisView"
import ventas from "./ventas.json"
import viviendas from "./viviendas.json"

/** A precomputed demo analysis, written by apps/api/demo/generate_demo_fixture.py. */
export interface DemoFixture {
  filename: string
  size_bytes: number
  row_count: number | null
  column_count: number | null
  analysis: AnalysisViewProps["analysis"]
}

// TypeScript imports JSON with string literals widened to `string` (no `as const` for JSON),
// so a fixture can never satisfy unions such as ColumnProfile["type"] directly. Checking it
// against the widened type still makes typecheck fail when the generator renames, drops or
// retypes a field; only the literal values themselves are left unchecked.
type Widen<T> = T extends string
  ? string
  : T extends number
    ? number
    : T extends boolean
      ? boolean
      : T extends readonly (infer U)[]
        ? Widen<U>[]
        : T extends object
          ? { [K in keyof T]: Widen<T[K]> }
          : T

export const salesFixture = (ventas satisfies Widen<DemoFixture>) as DemoFixture
export const housingFixture = (viviendas satisfies Widen<DemoFixture>) as DemoFixture
