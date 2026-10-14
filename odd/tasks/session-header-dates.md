# Session header button and list dates

Objective: W7 and W8 of the charts web brief, split into their own small PR (charts-fit-web L7). Branch `fix/session-header-dates` from `main` 6897fb3; PR against `main`. Runner: Vitest, `tsc`, `eslint`, build in `apps/web`.

## Specs

- S1 (W7): "En la cabecera con sesión, botón secundario con relieve, el mismo componente que «Iniciar sesión» en /demo, sin estilos duplicados." «Iniciar sesión» uses the shared `SECONDARY_BUTTON` style; «Cerrar sesión» uses the same constant (no copied classes) and keeps its form (`POST /auth/logout`).
- S2 (W8): "«12 oct 2026» con el formateador compartido, en lugar de «12/10/2026»." The project list uses `formatIsoDate`.

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S1 | inline | done: RED (text link class), GREEN | bb010dd |
| T2 | S2 | inline | done: RED («1/10/2026»), GREEN; web 117/117, tsc, eslint | (this commit) |

## Log

- L1 (2026-10-14, Borja): "Dos PRs. Primero W7 y W8 en su propia rama y PR (fix/session-header-dates, desde main), pequeña. Después los gráficos en feat/charts-fit-web, una sola PR con size:exception y un commit por decisión (W1, W2, W3…) para que se pueda revisar por partes. Método de siempre en las dos. Enséñame el resumen de cada una antes de su push."
