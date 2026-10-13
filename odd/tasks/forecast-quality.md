# forecast-quality

Objective: make the forecast trustworthy on real data (brief P3 / PR 4, H2 + H3) and fix two defects reported by Borja: the confidence interval and the histogram's empty bins.
Branch: `fix/forecast-quality` from `main` (03493fb). Delivery: ask-on-risk (forecast about 550 authored lines, so the chain question comes before the commit that crosses 400). Runners: `pytest` and `ruff` in `apps/api`; `npm test`, `typecheck`, `lint` and `build` in `apps/web`.

## Specs

Decided in L4. Open decisions D1-D5 are closed; their rationale is in L3/L4 and in commit 95255d0.

- S1 H2 (brief): "El objetivo del forecast es la primera columna numérica, aunque sea un identificador." Fix: the forecast target is the first numeric column that is not an identifier; with none left, there is no forecast. A column is an identifier when it is numeric, every non-null value is an integer and distinct, and either the values form a consecutive range in any order (`max - min + 1 == count`) or its name has the token `id`. L4: "parte el nombre por cualquier carácter que no sea letra o dígito, incluido el guion bajo: cliente_id e ID cliente deben coincidir; Pedidos y Paid no." Token match is case-insensitive. `profile_csv` stores `is_identifier` on every column entry. The regression keeps its current columns (backlog).
- S2 H3 aggregation (D1, L4 accepted): dates are reduced to the day; when no date repeats there is no aggregation (`aggregation: "none"`); when dates repeat, values are summed per date (`aggregation: "sum"`). The chart and the PDF say it ("Suma diaria de Ventas", with the period word of the frequency). A level metric with repeated dates is summed: known limitation, backlog.
- S3 H3 frequency and gaps (D3, L4 accepted):
  - Frequency from the median spacing between consecutive distinct dates: D (1 day), W (7), M (28-31), Q (89-92), Y (365-366). Any other spacing, or two dates in the same period: no forecast.
  - Seasonal period and horizon (steps) per frequency: D 7 and 30, W 52 and 12, M 12 and 12, Q 4 and 8, Y none and 3. Seasonality is used when the fitted series has at least three seasons (today's rule for D: 21 points).
  - Short gap, up to 3 consecutive missing steps: filled with 0 when summed, interpolated otherwise. Long gap, more than 3: the series is cut to the segment after the last long gap; fewer than 10 points left means no forecast.
  - The backtest metrics use only observed steps.
  - The result carries `frequency` and `horizon`; `horizon_days` is no longer written. L4: "El horizonte según la frecuencia, con el título del gráfico que lo refleje." Title: "Forecasting — próximos 30 días / próximas 12 semanas / próximos 12 meses / próximos 8 trimestres / próximos 3 años".
- S4 H3 metric (D4), L4: "MAE y además WAPE (la suma de errores absolutos entre la suma de valores reales); WAPE como cifra principal en la UI y el PDF, MAE como detalle." WAPE = Σ|actual − forecast| / Σ|actual| × 100 over the observed backtest steps (absolute actuals, so a series with negatives cannot divide by a sum near 0); `None` when Σ|actual| is 0. MAE = mean |actual − forecast| over the same steps. The result carries `wape` and `mae`; `mape` is no longer written but stays optional in the API schema, the web types, the chart and the PDF for stored analyses.
- S5 Confidence interval (D5 accepted): `simulate(horizon, repetitions=1000, error="add", random_errors=None, rng=np.random.default_rng(FORECAST_SEED))` with `FORECAST_SEED = 42`; bounds are the 2.5 and 97.5 percentiles per step. L4: "Recorta el intervalo a 0 solo si la serie histórica no tiene negativos."
- S6 Histogram: every bin is returned, including those with count 0 (`profiling.py:76`).
- S7 Compatibility, L4: "Añade un test que pinte un análisis antiguo, solo con mape, para demostrar la compatibilidad." The API schema keeps passing stored forecasts (`mape`, `horizon_days`) and passes the new fields through.
- S8 Closure: independent verifier (the stored `predictions_json` format changes, high-risk item 1), RDD per work-unit commit.

Test data (brief): "Para los tests automáticos de la PR 4, mejor fixtures pequeñas creadas en el propio test que estos ficheros." The demo fixtures are not regenerated here: that happens once, at the end of the insights prompt PR (`ventas.json` keeps `"mape"` until then, which S7 covers).

## Tasks

Route: inline (no Writer trigger). Each task: RED, GREEN, commit.

- [x] T1 inline: `docs: add feature document for forecast quality` (95255d0)
- [ ] T2 S6 inline: histogram returns empty bins
- [ ] T3 S1 inline: identifier detection in profiling; forecast target skips identifiers
- [ ] T4 S2, S3 inline: day aggregation, frequency, gaps, horizon per frequency, observed-only backtest
- [ ] T5 S4 inline: WAPE and MAE in the service
- [ ] T6 S5 inline: simulated interval, clipped at 0 for non-negative history
- [ ] T7 S2-S4, S7 inline: API schema, web types, chart (title, WAPE, MAE, aggregation), PDF; old analysis render test
- [ ] T8 S8: verifier, RDD

## Log

- L1 Borja (2026-10-13, earlier session; the verbatim prompt was not kept, scope from Engram `plan/next-prs-after-demo`): forecast quality PR first and insights prompt PR after it, so the demo fixtures are regenerated once, at the end of the prompt PR. P3 scope extended with the confidence interval (S5) and the histogram's empty bins (S6), each verified with a RED at the start of the PR.
- L2 Borja (2026-10-13): "El resumen está bien, con dos correcciones. Primera: antes de los RED, crea la rama, haz el commit de cierre de la demo y escribe el documento odd/tasks de la PR con las decisiones abiertas y tu recomendación para cada una: suma o media por día (sumar no sirve para métricas de nivel como precios o stock), cómo detectar una columna tipo ID, qué es un hueco largo y qué hacer con él, MAE o sMAPE (y dónde cambia la etiqueta: front, PDF y fixtures), y el número de repeticiones y la semilla de la simulación. No escribas tests hasta que te conteste. Segunda: en el orden, entre el rediseño y el portfolio va la PR de mejoras pequeñas del backlog. Guárdalo en Engram"
- L3 Branch created from main 03493fb; da7e602 closes `odd/tasks/demo.md` (L22, L23, T8). Code read for the decisions: `forecasting.py` (mean per date, `asfreq("D").interpolate()`, interval from `series.tail(...).std()`), `tasks.py:23` (`numeric_cols[0]`), `profiling.py:76` (empty bins dropped), `report.py:288`, `ForecastChart.tsx:43-47`. Waiting for Borja on D1-D5.
- L4 Borja (2026-10-13): "D1, D3 y D5 aceptadas. D2 aceptada, pero parte el nombre por cualquier carácter que no sea letra o dígito, incluido el guion bajo: cliente_id e ID cliente deben coincidir; Pedidos y Paid no. D4: MAE y además WAPE (la suma de errores absolutos entre la suma de valores reales); WAPE como cifra principal en la UI y el PDF, MAE como detalle. Recorta el intervalo a 0 solo si la serie histórica no tiene negativos. El horizonte según la frecuencia, con el título del gráfico que lo refleje. Añade un test que pinte un análisis antiguo, solo con mape, para demostrar la compatibilidad. Actualiza el documento con estas decisiones y empieza por los RED"
- L5 Specs rewritten from L4. Found while planning: the API validates stored predictions through `ForecastOut` (`routers/datasets.py:36`, `routers/analyses.py:51`), which drops unknown keys and defaults `horizon_days` to 30, so the new fields must be declared there (S7). Interpretations to confirm: WAPE divides by Σ|actual| (S4); dates are reduced to the day before aggregating (S2); `run_forecast` derives the horizon from the frequency, so its `horizon_days` parameter goes away.
