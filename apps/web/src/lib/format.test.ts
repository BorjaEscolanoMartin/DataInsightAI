import { describe, expect, it } from "vitest"
import { formatDateRange, formatInstantDate, formatIsoDate, formatNumber } from "./format"

describe("formatNumber", () => {
  it.each([
    [2307.5, 1, 0, "2.307,5"],
    [1502.77, 2, 0, "1.502,77"],
    [730, 2, 0, "730"],
    [-1234.5, 1, 0, "−1.234,5"],
    [0.8196, 1, 1, "0,8"],
    [2, 1, 1, "2,0"],
  ])("writes %s like the backend's format_es", (n, max, min, text) => {
    expect(formatNumber(n, max, min)).toBe(text)
  })
})

describe("formatIsoDate", () => {
  it.each([
    ["2024-01-15", "15 ene 2024"],
    ["2024-02-01", "1 feb 2024"],
    ["2024-03-31", "31 mar 2024"],
    ["2024-04-02", "2 abr 2024"],
    ["2024-05-09", "9 may 2024"],
    ["2024-06-10", "10 jun 2024"],
    ["2024-07-11", "11 jul 2024"],
    ["2024-08-12", "12 ago 2024"],
    ["2026-09-30", "30 sep 2026"],
    ["2024-10-01", "1 oct 2024"],
    ["2024-11-29", "29 nov 2024"],
    ["2024-12-31", "31 dic 2024"],
  ])("writes %s as %s", (iso, text) => {
    expect(formatIsoDate(iso)).toBe(text)
  })

  it("reads only the calendar date of a timestamp, whatever the time zone", () => {
    expect(formatIsoDate("2024-10-01T00:00:00")).toBe("1 oct 2024")
    expect(formatIsoDate("2024-10-01T23:30:00Z")).toBe("1 oct 2024")
  })

  it("can leave the year out", () => {
    expect(formatIsoDate("2024-10-01", { year: false })).toBe("1 oct")
  })

  it("returns null for a value that is not an ISO date", () => {
    expect(formatIsoDate("01/10/2024")).toBeNull()
    expect(formatIsoDate("2024-13-01")).toBeNull()
  })
})

describe("formatDateRange", () => {
  it("joins both ends with a spaced en dash", () => {
    expect(formatDateRange("2024-10-01", "2026-09-30")).toBe("1 oct 2024 – 30 sep 2026")
  })

  it("returns null when an end is missing", () => {
    expect(formatDateRange(undefined, "2026-09-30")).toBeNull()
    expect(formatDateRange("2024-10-01", undefined)).toBeNull()
  })
})

describe("formatInstantDate", () => {
  it.each([
    // Summer time (UTC+2): 23:30 UTC is already 1:30 on the next day in Madrid.
    ["2026-10-01T23:30:00Z", "Europe/Madrid", "2 oct 2026"],
    ["2026-07-10T22:30:00Z", "Europe/Madrid", "11 jul 2026"],
    // Winter time (UTC+1): 22:30 UTC is still 23:30 the same day; 23:30 UTC on 31 December is
    // already New Year.
    ["2026-01-10T22:30:00Z", "Europe/Madrid", "10 ene 2026"],
    ["2026-12-31T23:30:00Z", "Europe/Madrid", "1 ene 2027"],
    ["2026-10-01T23:30:00Z", "UTC", "1 oct 2026"],
  ])("writes %s as the calendar day in %s", (iso, timeZone, expected) => {
    expect(formatInstantDate(iso, { timeZone })).toBe(expected)
  })

  it("uses the browser's time zone by default", () => {
    const browserZone = Intl.DateTimeFormat().resolvedOptions().timeZone

    expect(formatInstantDate("2026-10-01T23:30:00Z")).toBe(
      formatInstantDate("2026-10-01T23:30:00Z", { timeZone: browserZone }),
    )
  })

  it("returns null for a value that is not an instant", () => {
    expect(formatInstantDate("no es una fecha")).toBeNull()
  })
})
