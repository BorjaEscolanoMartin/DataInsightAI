# Charts fit the data (web)

Objective: the web draws the charts of the API PR #37 (numeric histogram bounds with outlier bins, value bars, tidy axes, full-width heatmap, gap-free grid) and honours reduced motion. Branch `feat/charts-fit-web` from `main` 6897fb3; one PR against `main` with `size:exception`, one commit per decision (L7). W7 and W8 went to their own PR, #39 (`fix/session-header-dates`). Brief: `.claude/rediseno/graficos-web/graficos-web.md` (git-ignored) with its mockups. Runner: Vitest (`npm test`), `tsc`, `eslint`, build in `apps/web`; screenshots of /demo at 1280 and 390 px, both themes.

## Specs

Quoted from the brief (W1–W10); decisions in the Log.

- S1 (W1): "Las etiquetas salen de `start` y `end`, formateadas con el formateador español compartido: «22.000», «450.500», «0,1», «9,0». Nunca «1.01e+04»." "Las barras de extremo («< X» y «> Y», con `start` o `end` a `null`) van en `--au`, separadas unos píxeles del resto. Su etiqueta va en `--au` bajo la barra." "Bajo el título, en `--f3`: «N por encima de Y» (o «por debajo de X»), o nada si no hay extremos." "Los análisis antiguos, que solo tienen `bin`, se pintan como ahora."
- S2 (W2): "La web las pinta como columnas verticales en `--fg`, una por valor, porque son una distribución y no un ranking." Decision (L4): the web tells them apart by a numeric `value` in the data, in one helper with its test and a comment saying the API only sends `value` in whole-number column bars.
- S3 (W3): "El tope del eje es el máximo redondeado hacia arriba a un número «bonito», no el siguiente salto grande: con un máximo de 346, el eje llega a 400, no a 600." "La última etiqueta del eje no se corta."
- S4 (W4): "Los ejes van según los datos, con un 5 % de margen. Si todos los valores son ≥ 0, el eje no baja de 0. Nunca hay eje en negativo para datos positivos." "Los puntos, como ahora: relleno `--au` al 0,45 y borde opaco de 1 px."
- S5 (W5, corrected by L6): "con más de 4 variables ocupa todo el ancho de la rejilla y muestra los nombres completos. Con 4 o menos, una celda." "el mapa va en una caja con desplazamiento horizontal y un ancho mínimo de unos 620 px. La página no tiene desplazamiento horizontal." The cell colours stay as they are (no contrast failure, L5–L6).
- S6 (W6): "3 columnas en escritorio, 2 en tableta y 1 en móvil." "Si la última fila de gráficos pequeños queda incompleta, el último gráfico se estira hasta el final de la fila." "Cada gráfico separado por una línea fina `--ln`, sin tarjetas, como ahora."
- S7, S8 (W7, W8): moved to PR #39 (`odd/tasks/session-header-dates.md`), L7.
- S9 (W9): "Si el sistema pide reducir movimiento (`prefers-reduced-motion: reduce`), los gráficos se dibujan sin animación. Una sola utilidad compartida, no una comprobación en cada gráfico."
- S10 (W10, backlog): "Cuando esta PR esté en main, la API deja de generar `bin` en los análisis nuevos. Va en una PR propia." Same API PR (L4): «Top valores de X» → «Valores de X» and «X vs Y» → «X frente a Y». Titles stay as the API sends them in this PR.
- Checks (brief «Pruebas»): jsdom tests for the histogram labels in Spanish, the `bin` fallback, vertical columns for S2 and horizontal for categories, animation off with `matchMedia` mocked to reduce, screenshots of /demo (sales and housing) at 1280 and 390 px in both themes; "First Load JS de /demo: avisar si sube más de 5 kB" (baseline 242 kB, /demo 20,9 kB).

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S1 | inline | done: RED (`histogram` helper missing; no note under the title), GREEN; `histogramView` (pure, tested) gives the Spanish ranges, the outlier side, the axis ends with shared decimals and the note; the chart draws outlier bars in `--au` 4 px apart with their label in `--au` under them; old `bin`-only data keeps its labels and axis; checked in Chromium (housing, dark, 1280) | 13ecb73 |
| T2 | S2 | inline | done: RED (`bars` helper missing; no orientation), GREEN; `isValueBars` (one helper, commented: the API only sends `value` in whole-number column bars) picks `ValueColumnChart` (vertical `--fg` columns, every value labelled) or `CategoricalBarChart`; each root marks `data-orientation` for the jsdom test | 5ecabf2 |
| T3 | S3 | inline | done: RED (`axis` helper missing), GREEN; `niceAxisMax` (346 → 400, 950 → 1.000; next multiple of the leading power of ten) sets the category bars' domain with 5 ticks; `numberTick` writes axis numbers in Spanish; right margin 24 px keeps the last label whole | f35ca9b |
| T4 | S4 | inline | done: RED (`scatterAxis` missing), GREEN; 5 % margin, clamped at 0 when every value is ≥ 0, round ticks (1, 2, 2,5, 5 × 10ⁿ) covering the margin, Spanish tick numbers; points unchanged (`--au` at 0,45 with a 1 px opaque stroke) | (this commit) |
| T5 | S5 | inline | pending | |
| T6 | S6 | inline | pending | |
| T7 | S9 | inline | pending | |
| T8 | checks, screenshots | inline | pending | |

Route: inline; no writer trigger (sequential edits in the same chart components).

## Log

- L1 (2026-10-14, Borja): "Nueva tarea: PR de la web de los gráficos (rama feat/charts-fit-web desde main actualizado). Lee .claude/rediseno/graficos-web/graficos-web.md entero y mira las maquetas y capturas de esa carpeta. W1–W10 están cerradas salvo lo marcado «a decidir»: plantéamelo con tu recomendación antes del primer test. El contraste del mapa de correlaciones (W5) es un fallo actual de accesibilidad: compruébalo con los colores finales. Método de siempre. Enséñame el resumen y las capturas antes del push."
- L2: W2 «a decidir»: by a numeric `value` (no API change, works with analyses saved since #37) vs an explicit API field (needs an API PR first, and the web would still need the `value` fallback). Mockup titles («Valores de Zona», «Metros frente a Precio») differ from the API's («Top valores de Zona», «Metros vs Precio»).
- L3 (2026-10-14, Borja): "W2: sí, por la presencia de value, en un único helper con su test y un comentario que explique que la API solo envía value en las barras de columnas enteras. Títulos: sí, mantén los de la API en esta PR. Apunta en el backlog, para la PR de API de W10: «Top valores de X» → «Valores de X» y «X vs Y» → «X frente a Y». Crea la rama y sigue con el método de siempre; enséñame el resumen y las capturas antes del push."
- L4: Decisions from L3 recorded in S2 and S10. Backlog in Engram: `backlog/histogram-bin-label` (W10) now also carries the title changes.
- L5: W5 contrast measured on a `main` build in Chromium (/demo, housing): the cells mix `--au` (`--f3` for r < 0) at most 50 % over `--bg` with `--fg` text: r = 1,00 gives 5,56:1 (dark) and 9,59:1 (light); r = −0,27 gives 14,08:1 and 14,43:1. No current failure: the brief's 1,76 and 4,04 are text on pure gold, as drawn in the mockup. The proposed `--heat`/`--heat-neg` tokens would lower the worst case to 4,87:1 (dark) and 5,35:1 (light) (computed for every |r| in 0,01 steps; the brief's figures for them check out).
- L6 (2026-10-14, Borja): "Mantén los colores actuales del mapa: tu medición es correcta y el fallo del brief venía de la maqueta, no de la app. De W5 aplica solo el ancho completo con más de 4 variables y la caja con desplazamiento horizontal en móvil. Corrige W5 en graficos-web.md y en el documento de la tarea para que no quede como fallo de contraste. Sigue con el método de siempre." W5 corrected in the brief (local, git-ignored) and in S5.
- L7 (2026-10-14, Borja): "Dos PRs. Primero W7 y W8 en su propia rama y PR (fix/session-header-dates, desde main), pequeña. Después los gráficos en feat/charts-fit-web, una sola PR con size:exception y un commit por decisión (W1, W2, W3…) para que se pueda revisar por partes. Método de siempre en las dos. Enséñame el resumen de cada una antes de su push." Forecast for this PR: about 450–550 authored lines; one commit per W (T1 W1, T2 W2, T3 W3, T4 W4, T5 W5, T6 W6, T7 W9).
