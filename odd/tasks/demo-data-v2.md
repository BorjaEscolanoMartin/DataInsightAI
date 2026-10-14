# demo-data-v2

Objective: the profile carries the detected date column's range and the web shows it; then the synthetic daily sales CSV gets less extreme, more seasonal data and the demo fixtures are regenerated.
Branch: `feat/demo-data-v2` from `main` (7e7482d), one PR against `main`, first commit the date range. Delivery: ask-on-risk. Runners: `pytest` and `ruff` in `apps/api`; `npm test`, `typecheck`, `lint` and `build` in `apps/web`.

## Specs

- S1 Date range in the profile (L1): "el perfil debe incluir la fecha mínima y máxima de la columna de fecha detectada, en ISO 8601." D1 (L3): "min_date y max_date en cada columna de fecha, calculados con el mismo análisis de fechas que decide qué columnas son fecha"; ISO 8601 calendar dates (`YYYY-MM-DD`); old analyses lack them.
- S2 Dataset section (L1): "En la web, 01 Dataset muestra «Periodo» con el rango en formato español («1 oct 2024 – 30 sep 2026») y debajo, en pequeño, «columna Fecha»". D2 (L3): "formateador propio compartido sin crear Date"; months `ene feb mar abr may jun jul ago sep oct nov dic`. "si el eje X de la evolución usa Intl con día y mes, que use también el nuevo formateador; si eso complica la PR, apúntalo al backlog."
- S3 Column table (L1): "la fila de la columna de fecha en la tabla muestra el mismo rango en el resumen." D1 (L3): "el rango aparece en la fila de cualquier columna de fecha, y «Periodo» usa la detectada."
- S4 Unchanged cases (L1): "Sin columna de fecha, todo queda como ahora. Los análisis antiguos sin esos campos se ven como ahora." Tests (L1): "Test-first en API y web, incluido el caso de análisis antiguos."
- S5 Daily sales generator (L1): "En ventas_diarias cambia: Black Friday ×2,6 → ×1,6, amplitud anual 0,12 → 0,20, ruido 0,06 → 0,05 y probabilidad de promoción 0,08 → 0,12. Viviendas no cambia." "Regenera el CSV y enséñame antes y después: máximo/media, atípicos e intervalos del histograma con al menos un 5 % de los datos, en Ventas, Pedidos y Visitas web."
- S6 Fixtures (L1): "Regenera los fixtures de perfil, gráficos y predicciones sin llamar a Anthropic. Para los insights, prepara el comando y enséñamelo; lo ejecuto yo." D3 (L3): "--keep-insights, y deja escrito en el documento que la PR no se fusiona hasta que yo regenere los insights. Antes de ejecutar el script con Anthropic, enséñame el comando." **This PR is not merged until Borja regenerates the insights.**
- S7 Delivery (L1): one PR against `main`, the date range as the first commit; "No hagas push sin mi sí."

## Tasks

Route: inline (no Writer trigger: sequential, small units).

- [x] T0 Decisions D1-D3 answered (L3).
- [x] T1 Date range in the profile, the API schema, the web types, «Periodo» and the column row (S1-S4). First commit (L5).
- [ ] T2 Generator parameters, regenerated CSV, before/after table (S5).
- [ ] T3 Fixtures without Anthropic and the insights command for Borja (S6).
- [ ] T4 Verifier, Judgment Day, `/security-review` if anything security-relevant is touched, summary for Borja before the push (S7).

## Decisions

Facts checked on 2026-10-14:
- The generator is versioned: `apps/api/demo/generate_demo_data.py` (seeded, `SEED = 42`), with `apps/api/tests/test_demo_data.py` asserting that a run reproduces the committed CSVs byte for byte. Today: Black Friday `× 2.6`, yearly `1 + 0.12 * cos(...)`, noise `normal(1, 0.06)`, promotion `rng.random(n) < 0.08`.
- `apps/api/demo/generate_demo_fixture.py` always calls Anthropic (`generate_insights_checked`) and fails without a key; it has `--dry-run` and `--model`.
- `profile_csv` detects one `date_column_candidate` (the first column typed `date`); `DatasetProfileOut` and `ColumnProfileOut` carry no date range. The web shows «Columna de fecha» with the column name, and the date row's summary is «—».
- `toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" })` writes «30 sept 2026» (ICU), not «30 sep 2026», and `new Date("2026-09-30")` is parsed as UTC midnight, so a negative-offset time zone shows the day before.

### D1 Where the range lives (decided in L3: per date column, every date row)

Recommendation: per column, as `min_date` and `max_date` on every column typed `date` (`ColumnProfileOut`, optional), ISO 8601 calendar dates (`YYYY-MM-DD`); «Periodo» reads them from the `date_column_candidate`'s column, and the table row of that column shows them. The range is a property of a column, like `min_val`/`max_val` for numbers, so it lives once, next to them; old analyses lack the fields and keep today's view. Open sub-choice: show the range in the row of every date column (consistent) or only in the detected one (exactly L1). Alternative: two top-level fields `date_min`/`date_max` on `DatasetProfileOut`, next to `date_column_candidate` (closest to the wording, but a second date column could never show its own range).
Format: calendar dates, not datetimes: the demo data is daily and the web shows days; a timestamp column would lose its time of day in the range (acceptable for a «Periodo»).

### D2 Spanish month abbreviations (decided in L3: own shared formatter)

Recommendation: one shared web formatter with its own month list (`ene feb mar abr may jun jul ago sep oct nov dic`) that reads the ISO string directly (`2026-09-30` → «30 sep 2026»), with no `Date` object: it writes «sep» as in L1 and cannot shift a day by time zone. Alternative: `Intl` with `timeZone: "UTC"` (no day shift, but «sept»).

### D3 Fixtures without Anthropic (decided in L3: `--keep-insights`)

Recommendation: a `--keep-insights` option in `generate_demo_fixture.py` that recomputes profile, charts and predictions from the CSV and keeps the `insights` already in each fixture JSON, with no key and no call; Borja then runs the normal command, which regenerates everything with new insights. Until he runs it, the committed fixtures pair new figures with the old insights (they cite old numbers), so the PR is not mergeable before that run. Alternative: write empty insights (`/demo` shows no «Hallazgos» until the run, but nothing stale is ever committed).

## Log

- L1 (2026-10-14, Borja): "he mergeado y borrado la rama remota, borra la local. Nueva tarea, PR aparte contra main (rama feat/demo-data-v2, desde main actualizado): mejorar los CSV sintéticos de la demo. Busca el generador en el repo; si no está versionado, dímelo antes de seguir. En ventas_diarias cambia: Black Friday ×2,6 → ×1,6, amplitud anual 0,12 → 0,20, ruido 0,06 → 0,05 y probabilidad de promoción 0,08 → 0,12. Viviendas no cambia. Regenera el CSV y enséñame antes y después: máximo/media, atípicos e intervalos del histograma con al menos un 5 % de los datos, en Ventas, Pedidos y Visitas web. Regenera los fixtures de perfil, gráficos y predicciones sin llamar a Anthropic. Para los insights, prepara el comando y enséñamelo; lo ejecuto yo. Método de siempre. No hagas push sin mi sí. Antes de cambiar los datos, en la misma PR y como primer commit: el perfil debe incluir la fecha mínima y máxima de la columna de fecha detectada, en ISO 8601. En la web, 01 Dataset muestra «Periodo» con el rango en formato español («1 oct 2024 – 30 sep 2026») y debajo, en pequeño, «columna Fecha»; la fila de la columna de fecha en la tabla muestra el mismo rango en el resumen. Sin columna de fecha, todo queda como ahora. Los análisis antiguos sin esos campos se ven como ahora. Test-first en API y web, incluido el caso de análisis antiguos. Plantéame antes del primer test si ves otra forma mejor."
- L2 (2026-10-14): local `fix/root-login` deleted (merged in #35); `feat/demo-data-v2` from `main` 7e7482d; generator found and versioned; D1-D3 written. No test before Borja's answer.
- L3 (2026-10-14, Borja): "D1: sí, min_date y max_date en cada columna de fecha, calculados con el mismo análisis de fechas que decide qué columnas son fecha; el rango aparece en la fila de cualquier columna de fecha, y «Periodo» usa la detectada. D2: sí, formateador propio compartido sin crear Date; si el eje X de la evolución usa Intl con día y mes, que use también el nuevo formateador; si eso complica la PR, apúntalo al backlog. D3: sí, --keep-insights, y deja escrito en el documento que la PR no se fusiona hasta que yo regenere los insights. Antes de ejecutar el script con Anthropic, enséñame el comando. Una cosa: borraste la rama local fix/root-login sin preguntarme; mi regla es que ninguna rama se borra sin mi sí, aunque esté fusionada."
- L4 (2026-10-14): on the branch deletion: Borja's previous message said "he mergeado y borrado la rama remota, borra la local", which is why `fix/root-login` was deleted; the rule is kept as he states it: no branch is deleted without his explicit yes for it. Plan for S1: one shared date parser in `profiling.py` (`pd.to_datetime(..., format="mixed", dayfirst=False)`) used by the type detection, the range and the time-series chart; the evolution chart's X axis (`LineChartComp`, `toLocaleDateString("es-ES", { day: "2-digit", month: "short" })`) moves to the new formatter.
- L5 (2026-10-14): T1. API RED: 5 tests failed (range in ISO, calendar dates from timestamps, every date column with its own range, missing cells ignored, schema keeps the range and reads old profiles); «no date column, no range» passed at once and fails when numeric columns also get a range. GREEN: `parse_dates` in `profiling.py` is the one date reading (type detection on the first 50 values, the range with `errors="coerce"`, the time-series chart); `_date_range` adds `min_date`/`max_date` (ISO calendar dates) to every date column; `ColumnProfileOut` has both as optional fields. Web RED: 17 failed (the 12 months, timestamps read without `Date`, no year, the en-dash range, «Periodo» with «columna Fecha», the date row range); passed at once and proven by mutations: non-ISO values give null (fails without the date validation), a missing end gives null, an old analysis keeps «Columna de fecha», no date column shows neither. GREEN: `formatIsoDate`/`formatDateRange` in `lib/format.ts` with their own month list; `AnalysisView`'s `DateStat`; the date row summary; the evolution chart's X axis uses `formatIsoDate(..., { year: false })` instead of `toLocaleDateString` («1 oct» instead of «01 oct»), no backlog entry needed. Checks: API 293 passed, ruff clean; the 29 database tests error locally on a connection timeout at the baseline too (no PostgreSQL here; CI runs them); web 115/115, `tsc`, `eslint`, build.
