# forecast-quality

Objective: make the forecast trustworthy on real data (brief P3 / PR 4, H2 + H3) and fix two defects reported by Borja: the confidence interval and the histogram's empty bins.
Branch: `fix/forecast-quality` from `main` (03493fb). Delivery: ask-on-risk (forecast about 550 authored lines, so the chain question comes before the commit that crosses 400). Runners: `pytest` and `ruff` in `apps/api`; `npm test`, `typecheck`, `lint` and `build` in `apps/web`.

## Specs

Status: draft. No test is written until Borja answers D1-D5 (L2: "No escribas tests hasta que te conteste").

- S1 H2 (brief): "El objetivo del forecast es la primera columna numérica, aunque sea un identificador." "`workers/tasks.py` → `_run_predictions` usa `numeric_cols[0]`. Con el `Supertienda` original, el objetivo es `Id. de la fila`." Fix: exclude ID-like columns from the target. Detection: D2.
- S2 H3 aggregation (brief): "`run_forecast` agrega por día con la **media**, no con la suma". Brief PR 4: "agregación (suma o media según la columna)". L2: "suma o media por día (sumar no sirve para métricas de nivel como precios o stock)". Rule: D1.
- S3 H3 gaps and frequency (brief): "rellena con `asfreq("D").interpolate()` los días que faltan". "Serie trimestral de Appol: MAPE del 0,0 %, porque el backtest compara contra valores interpolados en línea recta, no contra datos reales." Brief P3: "no interpolar huecos largos o detectar la frecuencia". Rule: D3.
- S4 H3 metric (brief): "Serie diaria de Supertienda: MAPE del 427,9 %. La serie va de 296 a 98.567 en los últimos 30 días, y el MAPE se dispara en los días bajos." Brief P3: "cambiar a una métrica robusta (MAE o sMAPE)". L2: "MAE o sMAPE (y dónde cambia la etiqueta: front, PDF y fixtures)". Choice: D4.
- S5 Confidence interval (Borja, Engram plan/next-prs-after-demo): the interval is the raw series std × √i (`last_std * 1.96 * sqrt(i+1)`), so it leaves the plausible range (negative, and above 7,000 in ventas). Proposal: compute it by simulating the fitted model. Parameters: D5. Verified with a RED first.
- S6 Histogram (Borja, same record): the profiling histogram drops empty bins and merges bins that are not contiguous; it must also return bins with count 0. Verified with a RED first. Code evidence: `profiling.py:76`, `if counts[i] > 0`.
- S7 Closure: independent verifier (the stored `predictions_json` format changes, high-risk item 1), RDD per work-unit commit; Judgment Day and /security-review if Borja asks for them.

Test data (brief): "Para los tests automáticos de la PR 4, mejor fixtures pequeñas creadas en el propio test que estos ficheros." The demo fixtures are not regenerated here: that happens once, at the end of the insights prompt PR.

## Open decisions

Each one has a recommendation; nothing is applied until Borja answers.

### D1 Sum or mean per date

Today every series is averaged per date. Sum is right for flows (sales, orders), wrong for levels (price, stock, balance). No statistical test tells a flow from a level, and keyword lists by column name are fragile across languages.

Recommendation:
- Dates never repeat (one row per date, the common case for levels and for the demo): no aggregation, so sum and mean do not matter.
- Dates repeat (transaction-level data such as Supertienda): sum.
- The result carries `aggregation: "none" | "sum"`, and the chart and the PDF say it ("Suma diaria de Ventas"), so a sum applied to a level metric is visible instead of silent.
- Known limitation, to the backlog: a level metric with repeated dates (one price per product per day) is summed. Letting the user pick the aggregation needs UI and an API parameter, out of this PR.

Alternative: mean for names that look like levels (precio, price, stock, saldo, tasa, rate, %). Cheaper to explain, but it fails silently on any name outside the list.

### D2 ID-like columns

The profile already stores `type`, `unique_count` and `null_count` per column.

Recommendation: a column is an identifier when it is numeric, every non-null value is an integer and distinct, and either
- the values are a consecutive range in any order (`max - min + 1 == count`), or
- its name has the token `id` as a whole word, case-insensitive ("Id. de la fila", "ID", "row_id", "customer id"; not "Pedidos" or "Rapidez").

`profile_csv` computes it once and stores `is_identifier: bool` in each column entry (an optional new field; the web app ignores it). `_run_predictions` takes the first numeric column that is not an identifier; with none left, there is no forecast.

Sub-question: the regression has the same flaw (target `numeric_cols[-1]`, IDs as features). Recommendation: leave it for the backlog, because it changes the regression results the demo shows.

### D3 Frequency, long gaps and what to do with them

Detecting the frequency is what fixes Appol: a quarterly series is resampled per day today, so 90 interpolated days sit between real points.

Recommendation:
- Frequency: median spacing between consecutive distinct dates, mapped to D (1 day), W (7), M (28-31), Q (89-92) or Y (365-366). Any other spacing: no forecast, with a logged reason.
- Seasonality and horizon per frequency: D 7 and 30, W 52 and 12, M 12 and 12, Q 4 and 8, Y none and 3.
- A gap is a missing step at the detected frequency. Short gap: up to 3 consecutive missing steps. Filled with 0 when D1 summed (no transaction means no sales), interpolated otherwise.
- Long gap: more than 3 consecutive missing steps. The series is cut to the segment after the last long gap; if that segment has fewer than 10 points (today's minimum), no forecast.
- The backtest metric uses only observed steps, never filled ones. That is what removes the false 0.0 %.
- Result contract: new `frequency` and `horizon` (steps) fields. `horizon_days` stops being written; the chart and the PDF fall back to it for analyses stored before this PR.

### D4 MAE or sMAPE

- sMAPE is a percentage, easy to read, but it is 200 % on any step where the actual value is 0 and the forecast is not. With D1/D3, a summed daily series with days without sales has exactly those zeros, so Supertienda would still look broken.
- MAE is in the target's units, never explodes on zeros or low days, and is what the interval in S5 is measured in. Its cost: it is not comparable across columns, so it needs the unit context ("Error medio en backtest: 123,4 Ventas").

Recommendation: MAE. The field becomes `mae`; `mape` stays optional in the schema and the types, is no longer written, and old analyses keep showing it with its own label.

Where the label and the field change:
- Front: `apps/web/src/components/predictions/ForecastChart.tsx:45-47` ("MAPE backtest") and `apps/web/src/types/api.ts:105` (`mape: number | null`).
- PDF: `apps/api/app/services/report.py:288-289` (`("MAPE backtest", ...)`).
- API schema: `apps/api/app/schemas/predictions.py:14`.
- Fixtures: `apps/web/src/data/demo/ventas.json` holds `"mape": 8.961710139785902` (`viviendas.json` has no forecast). Not touched here: with `mape` optional it keeps typechecking and renders the old label until the insights prompt PR regenerates it.

### D5 Simulation of the interval

statsmodels 0.15.0: `HoltWintersResults.simulate(nsimulations, anchor=None, repetitions=1, error='add', random_errors=None, *, rng=None)`.

Recommendation:
- `repetitions=1000`, interval from the 2.5 and 97.5 percentiles per step. 1000 × 30 steps runs in milliseconds and the percentiles stay stable from run to run.
- Seed: module constant `FORECAST_SEED = 42` (the same value as the demo generator's SEED), passed as `rng=np.random.default_rng(FORECAST_SEED)`. The same CSV always gets the same band, so the tests and the regenerated fixtures are deterministic.
- `random_errors=None` (normal errors with the residual variance). `"bootstrap"` avoids the normality assumption but resamples from very few residuals on short series (10 points minimum).
- Proposal beyond the report: when every observed value is ≥ 0, clip `yhat_lower` at 0.

## Tasks

Provisional until D1-D5 are answered. Route: inline (no Writer trigger).

- [x] T1 inline: `docs: add feature document for forecast quality` (this file)
- [ ] T2 S6 inline: RED histogram with an empty bin, then return every bin
- [ ] T3 S1 inline: identifier detection in profiling, forecast target skips identifiers
- [ ] T4 S2, S3 inline: aggregation, frequency, gaps, observed-only backtest
- [ ] T5 S4 inline: MAE in the service, schema, types, chart and PDF, with fallback for old analyses
- [ ] T6 S5 inline: simulated interval
- [ ] T7 S7: verifier, RDD

## Log

- L1 Borja (2026-10-13, earlier session; the verbatim prompt was not kept, scope from Engram `plan/next-prs-after-demo`): forecast quality PR first and insights prompt PR after it, so the demo fixtures are regenerated once, at the end of the prompt PR. P3 scope extended with the confidence interval (S5) and the histogram's empty bins (S6), each verified with a RED at the start of the PR.
- L2 Borja (2026-10-13): "El resumen está bien, con dos correcciones. Primera: antes de los RED, crea la rama, haz el commit de cierre de la demo y escribe el documento odd/tasks de la PR con las decisiones abiertas y tu recomendación para cada una: suma o media por día (sumar no sirve para métricas de nivel como precios o stock), cómo detectar una columna tipo ID, qué es un hueco largo y qué hacer con él, MAE o sMAPE (y dónde cambia la etiqueta: front, PDF y fixtures), y el número de repeticiones y la semilla de la simulación. No escribas tests hasta que te conteste. Segunda: en el orden, entre el rediseño y el portfolio va la PR de mejoras pequeñas del backlog. Guárdalo en Engram"
- L3 Branch created from main 03493fb; da7e602 closes `odd/tasks/demo.md` (L22, L23, T8). Code read for the decisions: `forecasting.py` (mean per date, `asfreq("D").interpolate()`, interval from `series.tail(...).std()`), `tasks.py:23` (`numeric_cols[0]`), `profiling.py:76` (empty bins dropped), `report.py:288`, `ForecastChart.tsx:43-47`. Waiting for Borja on D1-D5.
