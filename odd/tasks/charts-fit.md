# Charts fit the data (API)

Objective: charts that adapt to the data: histograms not flattened by extremes, discrete columns as bars, numeric bin bounds, scatter on continuous pairs, no flat category charts. Branch `feat/charts-fit-api` from `main` 44c7eab; PR 1 of 2 against `main` (the web PR comes later, with a mockup; not started). Delivery: single PR. Runner: `pytest` + `ruff check .` in `apps/api` (web checks after the fixture regeneration).

## Specs

- S1 (A1): "Los valores extremos aplastan los histogramas: calcula los intervalos sobre el rango central (por ejemplo, percentiles 1–99) y agrupa lo que quede fuera en intervalos de extremo «< X» y «≥ Y»." Decision D1 (L2): the central range is the IQR bounds of `iqr_bounds` (the same rule the column table counts outliers with), clipped to the data's min and max; the 20 bins cover that range; values below go to «< X», values above to «> Y» (outliers are strictly outside the bound), each extreme bin only when it has values. "con un test para cuando el IQR sea 0, que debe usar el rango completo."
- S2 (A2): "Las columnas enteras con pocos valores distintos (baños, habitaciones) salen como histograma con intervalos tipo «1–1.1»: deben ser barras con el recuento de cada valor." Decision D2: every value an integer and at most 10 distinct values, the same constant the insights breakdowns use (one shared constant). "las columnas enteras se titulan «Distribución de X», no «Top valores»".
- S3 (A3): "Las etiquetas salen como «884.8» y «1.01e+04»: propongo que la API devuelva los límites como números y que la web los formatee con el formateador español compartido." Decision D3: each histogram bin is `{"bin", "start", "end", "count"}`, `start: null` on «< X» and `end: null` on «> Y»; `bin` stays for the current web and old analyses until the web PR. Discrete columns are `bar` charts with `{"name": "3", "value": 3, "count"}`, ordered by value. Backlog: "dejar de generar bin cuando la web use start/end".
- S4 (A4): "Las dispersiones eligen parejas con variables discretas (superficie vs habitaciones): deben preferir variables continuas." Decision D4: the discrete columns of S2 are excluded from the scatter pairs.
- S5 (A5): "Las categóricas casi uniformes, como el día de la semana con unos 104 por día, dan un gráfico plano" Decision D5: the bar chart is omitted when the largest category count divided by the smallest is at most 1,1, "y usa todas" (all the column's categories, not the profile's top 10).
- S6: "Los análisis antiguos guardados deben seguir viéndose."
- S7: "Para la demo, regenera los fixtures con --keep-insights."

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S1, S3 (histogram bins) | inline | done: RED (missing start/end; 20 bins over the whole range), GREEN; zero-IQR test mutation-checked | 2328cb6 |
| T2 | S2, S3 (discrete bars) | inline | done: RED (whole numbers drawn as a histogram), GREEN; boundary tests (11 values, decimals) mutation-checked; shared `MAX_DISCRETE_VALUES` replaces the breakdowns constant; the shared test CSV gets one decimal sale (300.5) so its 10 distinct whole numbers stay a histogram | d28a4e9 |
| T3 | S4 | inline | done: RED (metros–habitaciones chosen), GREEN; the discrete set is computed once and shared by the histograms and the scatter; when a continuous column lies beyond the 15 heatmap columns the correlations are recomputed (test, mutation-checked) | (this commit) |
| T4 | S5 | inline | pending | |
| T5 | S6, S7 | inline | pending | |

Route: inline; no writer trigger (one understood change in `profiling.py`, sequential).

## Log

- L1 (2026-10-14, Borja): "Nueva tarea en dos PRs seguidas contra main; empieza por la API (rama feat/charts-fit-api desde main). Crea odd/tasks/charts-fit.md con esto. Los gráficos no se adaptan a los datos:
API:
(A1) Los valores extremos aplastan los histogramas: calcula los intervalos sobre el rango central (por ejemplo, percentiles 1–99) y agrupa lo que quede fuera en intervalos de extremo «< X» y «≥ Y».
(A2) Las columnas enteras con pocos valores distintos (baños, habitaciones) salen como histograma con intervalos tipo «1–1.1»: deben ser barras con el recuento de cada valor.
(A3) Las etiquetas salen como «884.8» y «1.01e+04»: propongo que la API devuelva los límites como números y que la web los formatee con el formateador español compartido.
(A4) Las dispersiones eligen parejas con variables discretas (superficie vs habitaciones): deben preferir variables continuas.
(A5, a decidir) Las categóricas casi uniformes, como el día de la semana con unos 104 por día, dan un gráfico plano: ¿se omiten o se dejan?
Los análisis antiguos guardados deben seguir viéndose. Para la demo, regenera los fixtures con --keep-insights. La PR de la web vendrá después, con maqueta; no la empieces.
Antes del primer test, lee el código que genera los gráficos y plantéame las decisiones con tu recomendación y alternativas: el criterio de los percentiles, el umbral de «pocos valores enteros», el formato de los datos de los intervalos, cómo eligen ahora las parejas de dispersión y A5. Método de siempre."
- L2 (2026-10-14, Borja): "Sí, la tarea es mía. D1: sí, límites IQR, con un test para cuando el IQR sea 0, que debe usar el rango completo. D2: sí. D3: sí; las columnas enteras se titulan «Distribución de X», no «Top valores»; apunta al backlog dejar de generar bin cuando la web use start/end. D4: sí. D5: sí; dime si el cociente se calcula sobre todas las categorías o solo sobre el top 10, y usa todas. Arranca con el método de siempre y enséñame el resumen antes del push."
- L3: Current code (`_compute_charts`, `profiling.py`): 20-bin `np.histogram` over the full range of the first 6 numeric columns, label `f"{a:.4g}–{b:.4g}"`; bar charts from the profile's `top_categories` (top 10) of the first 4 categorical columns; scatter: top 2 pairs with |r| > 0,5 among the first 10 numeric columns, any type. Demo measures: IQR extreme bins Ventas 9, Pedidos 6, Visitas web 9, Metros 62, Precio 49 (P1–P99 would cut ~2 % of every column, 22 rows of Distancia al mar with no outliers); discrete: Habitaciones (6 values), Baños (4); continuous pairs in viviendas: only Metros–Precio passes 0,5; uniform: Día de la semana 105/104, Terraza 773/727 (1,06), Zona 1,35 stays. D5 answer: `top_categories` holds the top 10 only, so the ratio is computed from all the column's values.
- Backlog (L2): stop generating `bin` in histogram data once the web uses `start`/`end` (Engram `backlog/histogram-bin-label`).
