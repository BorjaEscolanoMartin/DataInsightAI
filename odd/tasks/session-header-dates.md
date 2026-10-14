# Session header button and list dates

Objective: W7 and W8 of the charts web brief, split into their own small PR (charts-fit-web L7). Branch `fix/session-header-dates` from `main` 6897fb3; PR against `main`. Runner: Vitest, `tsc`, `eslint`, build in `apps/web`.

## Specs

- S1 (W7): "En la cabecera con sesión, botón secundario con relieve, el mismo componente que «Iniciar sesión» en /demo, sin estilos duplicados." «Iniciar sesión» uses the shared `SECONDARY_BUTTON` style; «Cerrar sesión» uses the same constant (no copied classes) and keeps its form (`POST /auth/logout`).
- S2 (W8, changed by L3): "«12 oct 2026» con el formateador compartido, en lugar de «12/10/2026»." `created_at` is a UTC instant, so the list uses `formatInstantDate`: "junto a formatIsoDate, compartiendo la lista de meses. La zona horaria como parámetro opcional (por defecto, la del navegador), usando Intl.DateTimeFormat con formatToParts para obtener día, mes y año en esa zona." Tests: "timeZone “Europe/Madrid” explícito para 2026-10-01T23:30:00Z (debe dar «2 oct 2026») y un caso de horario de invierno, sin depender de la variable TZ del proceso."

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S1 | inline | done: RED (text link class), GREEN | bb010dd |
| T3 | S2 (L3) | inline | done: RED (`formatInstantDate` missing, 7 cases), GREEN; Madrid summer (23:30Z → «2 oct 2026», 22:30Z → next day) and winter (22:30Z → same day; 31 Dec 23:30Z → «1 ene 2027»), UTC, browser default, invalid → null; `shortDate` is the one composition of both formatters; web 124/124, tsc, eslint | (this commit) |
| T2 | S2 | inline | done: RED («1/10/2026»), GREEN; web 117/117, tsc, eslint | f6b0723 |

## Log

- L1 (2026-10-14, Borja): "Dos PRs. Primero W7 y W8 en su propia rama y PR (fix/session-header-dates, desde main), pequeña. Después los gráficos en feat/charts-fit-web, una sola PR con size:exception y un commit por decisión (W1, W2, W3…) para que se pueda revisar por partes. Método de siempre en las dos. Enséñame el resumen de cada una antes de su push."
- L2 (2026-10-14): Checks of bb010dd..f6b0723. Verifier S1, S2 PASS; no other date formatting left in apps/web/src; no security findings. Judgment Day: no CRITICAL; both judges WARNING: `formatIsoDate` shows the UTC day of the `created_at` instant, so projects created 00:00–01:59 in Madrid showed the previous day (2026-10-01T23:30:00Z: before «2/10/2026», now «1 oct 2026»).
- L3 (2026-10-14, Borja): "Sí, añade formatInstantDate junto a formatIsoDate, compartiendo la lista de meses. La zona horaria como parámetro opcional (por defecto, la del navegador), usando Intl.DateTimeFormat con formatToParts para obtener día, mes y año en esa zona. Test-first con timeZone “Europe/Madrid” explícito para 2026-10-01T23:30:00Z (debe dar «2 oct 2026») y un caso de horario de invierno, sin depender de la variable TZ del proceso. Confirma que la lista de proyectos se pinta en el cliente; si se pinta en el servidor, dímelo antes de seguir. Después, push y PR contra main, sin fusionar." The list is a client component (`"use client"`, projects from `useProjects()` in the browser), so the default zone is the viewer's. The page test (09:00Z) cannot tell `formatInstantDate` from `formatIsoDate`: the wiring is covered by review, not by a test, because a page test at 23:30Z would depend on the process time zone.
- L4 (2026-10-14, Borja): "Antes de fusionar #39, un test más: en el test de la página de proyectos, simula el módulo de formateo con vi.mock y comprueba que la lista llama a formatInstantDate con el created_at de cada proyecto (y no a formatIsoDate), con su mutación. Push a la misma PR. Después empieza feat/charts-fit-web desde main." Done: `vi.mock("@/lib/format")` wraps the real formatters in spies; the test lists two projects and checks `formatInstantDate` got each `created_at` in order and `formatIsoDate` was not called. It passed first (the wiring was already right) and fails against the mutant that renders `formatIsoDate(project.created_at)`. Web 125/125, tsc, eslint.
