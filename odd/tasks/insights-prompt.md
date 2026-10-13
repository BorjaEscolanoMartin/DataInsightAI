# insights-prompt

Objective: insights that stick to the data: no causal claims, no figures or context the model did not receive, Spanish number format, with a temporal summary and cross-column breakdowns as input and a check of the figures in the output. Ends by regenerating the demo fixtures.
Branch: `fix/insights-prompt` from `main` (3485774). Delivery: ask-on-risk. Runners: `pytest` and `ruff` in `apps/api`; `npm test`, `typecheck`, `lint` and `build` in `apps/web` (only if the fixtures' shape changes).

## Specs

Status: draft. No test is written until Borja answers D1-D6 (L1: "No escribas tests hasta que te conteste").

- S1 Prompt rules (L1): "sin afirmaciones causales, solo cifras que estén en los datos recibidos, sin inventar contexto externo, y formato numérico español (coma decimal, punto de miles)". Rules: D1.
- S2 Temporal summary (L1): "Resumen temporal cuando hay columna de fecha: qué se le pasa al modelo (totales o medias por periodo, picos con su fecha, tendencia) y con qué límite de tamaño." Design: D2.
- S3 Cross-column breakdowns (L1): "Cruces entre columnas: si se le pasan medias del objetivo por categoría (por ejemplo, con y sin promoción), para qué columnas y con qué límite." Design: D3.
- S4 Output check (L1): "Validación de la salida: si se comprueba que las cifras de los insights aparecen en los datos de entrada, y qué se hace si no." Design: D4.
- S5 Model and temperature (L1): "Temperatura y modelo, pensando en que los resultados sean reproducibles." Choice: D5.
- S6 Testing (L1): "Qué se puede testear sin llamar a Anthropic y cómo hacemos la prueba real con mi clave." Plan: D6.
- S7 Fixtures (L1): "Al final de la PR regeneraremos los fixtures de la demo." Borja runs `python -m demo.generate_demo_fixture` from `apps/api`; the JSON is reviewed before the commit, as in the demo PR.

Evidence that motivates the PR (Engram `backlog/insights-prompt-review`): every figure in the current fixtures is right; the errors are interpretation. Sales: causation from correlations ("direct precursor", r = 0.36 for visits(t-1) → orders(t)); "the low frequency prevents evaluating promotions" (50 promotion days; 2.908 vs 2.263 on average); "tripling the mean" (3.8 times); "almost perfect" for r = 0.92. Housing: Metros outliers "between 25 and 239 m²" (all are high, 163-239); Baños = 4 "probably > 200 m²" (157-199); price outliers "áticos or Playa" (43 adosados and 6 áticos, 32 in Playa). Likely cause: the model only receives the profile.

## Current state

- `apps/api/app/services/insights_llm.py`: `generate_insights(profile)` sends a Spanish system prompt and a user prompt built from the profile only (`_build_prompt`): per column type, nulls, uniques, mean/std/min/max with `:.3g` (so "91.4", "r=0.920"), outlier count, top 4 categories, the date column's name, and up to 6 pairs with |r| > 0.6. Model `claude-sonnet-4-6`, `max_tokens=4096`, no `temperature` (default 1.0), no structured output: the reply is parsed with `json.loads` after stripping code fences, then `InsightsOut.model_validate`.
- `generate_insights` receives no CSV: the worker calls it with the profile (`tasks.py:82`), and so does the fixture script. A temporal summary or a breakdown needs the CSV bytes.
- Tests (`tests/test_insights_llm.py`): the prompt contains column names and the row count; empty insights without a key; JSON parsing with a mocked client; code fences stripped.
- Installed SDK: `anthropic` 1.13.0 (uv.lock), which has `messages.parse` and `output_config`.
- Measured on the demo CSVs: sales covers 24 months (daily mean 1.979 in the first, 2.776 in the last); the top days are 2025-11-28 (8.734,60), 2024-11-22 (5.439,69) and 2026-09-26 (3.698,49); promotion Sí 2.908 (50 days) vs No 2.263 (680); weekday means from 2.056 (lunes) to 2.634 (sábado). Housing has no date; its 49 price outliers are 43 Adosado and 6 Ático, 32 in Playa; Baños has 4 distinct values and Habitaciones 6.

## Open decisions

Each one has a recommendation; nothing is applied until Borja answers.

### D1 Prompt rules

Recommendation, in the system prompt, as short rules with the reason for each (the newer models follow reasons better than capitals):
- Describe associations only: "se asocia con", "coincide con", "es mayor cuando". Forbidden: "causa", "provoca", "impulsa", "precursor", "motor", "indicador adelantado". A correlation is described with its r and the qualifier from a fixed scale given in the prompt (|r| < 0,3 débil, < 0,6 moderada, < 0,8 fuerte, otherwise muy fuerte), so "casi perfecta" never appears.
- Every figure in a description must appear in the data block, written as it appears there. Ratios, differences and percentages are allowed only if the data block already carries them (D2 and D3 precompute the useful ones).
- No external context: no seasons, holidays, markets or events unless their name is in the data (a "Black Friday" column would count; the date 2025-11-28 does not make it Black Friday).
- If the data cannot answer something, leave it out instead of saying it cannot be evaluated.
- Number format: the prompt itself writes every number in Spanish format (coma decimal, punto de miles, "8.734,60", "0,92", "28,5 %"), from one helper `format_es`, so the model copies figures that already have the right format and D4 can find them. Dates stay ISO (2025-11-28).

### D2 Temporal summary

Only when the profile has a date column and a forecast target (the same target the predictions use: the first numeric column that is not an identifier; the rule is moved from `tasks._run_predictions` to one shared helper, never copied). It reuses the forecast's reading of dates (reduced to the day, repeated dates summed), so the summary and the forecast describe the same series.

Recommendation:
- Per period, the mean of the daily (or per-step) values, not the total: a mean is comparable between months of different length and still makes sense for levels (prices, stock). Period: month for daily or weekly data, the data's own period for monthly, quarterly and yearly data. At most 24 periods (the last 24); an incomplete first or last period is marked as such.
- Peaks: the 3 highest and the 3 lowest values, with their date.
- Trend: the change between the first and the last complete period, as a value and a percentage, plus, if there are at least two years, the change of the last 12 months against the 12 before. These are the only trend figures the model may quote.
- Size limit: about 40 lines (24 periods, 6 peaks, 2-3 trend lines), roughly 1.500 tokens. On the demo: 24 months, which show the growth from 1.979 to 2.776 and the 8.734,60 peak.

### D3 Cross-column breakdowns

Recommendation:
- Target: the forecast target when there is a date column, otherwise the regression target (the last numeric non-identifier column). Same shared helper as D2.
- Columns: categorical and boolean columns, plus numeric columns with at most 10 distinct values (Baños, Habitaciones). At most 4 columns, the ones with the largest spread of group means. Identifiers and the target itself are excluded.
- Per group: n, the target's mean and its difference from the overall mean as a percentage. At most 10 groups per column (by n), the rest as "otros".
- Outliers: per numeric column with outliers, how many are low and how many are high, with the range of each side (fixes "between 25 and 239 m²"). For the target's outliers only, the top 3 groups of up to 2 breakdown columns (on the demo: 43 Adosado, 6 Ático; 32 Playa).
- Size limit: about 60 lines, roughly 2.000 tokens. On the demo: Promoción Sí 2.908 (n = 50, +28,5 %) and No 2.263 (n = 680).

### D4 Output check

Recommendation: yes, a deterministic check after the reply, no second call.
- Extract every number from each insight's title and description (Spanish format, with %, signs and thousands points) and compare it with the numbers in the prompt: equal after rounding to the precision written in the insight. Exempt: integers from 0 to 10 used as words ("3 días") and years or numbers that are part of an ISO date that appears in the data.
- An insight with any number not found is dropped, and a warning is logged with the category, the title and the numbers not found (never the API key or the CSV). The remaining insights are kept.
- If every insight is dropped, the result is empty insights, as when there is no key. The fixture script already fails on empty insights, so a bad run never reaches the demo.
- Alternative: one retry with the numbers not found listed. It costs a second call and is not deterministic; it can come later if dropped insights turn out to be frequent.

### D5 Model and temperature

What reproducibility can mean here: the insights are generated once per upload and stored, and the demo fixtures are committed, so nobody sees them change. Run to run, the same CSV will not give the same text with any current model. On Claude Opus 5.5 and Sonnet 5.5 `temperature` is not available (a non-default value returns 400). On the current `claude-sonnet-4-6` it is allowed, but even `temperature=0` is not fully deterministic.

Recommendation: `claude-opus-5-5`. Reproducibility then comes from the input and the output, not from sampling:
- The input is a deterministic summary (D2, D3).
- The output is held to a JSON schema with structured outputs (`output_config.format`, or `messages.parse` with `InsightsOut`, both in SDK 1.13.0). This removes the code-fence stripping and malformed JSON.
- The check in D4 limits what can vary to wording.
- Effort `medium` (the model's default, set explicitly) and no `temperature`.
- The refusal fallback that the API recommends for this model, plus handling `stop_reason == "refusal"` (no insights, logged).

Cost per analysis: about 4.000 tokens in and 1.500 out plus thinking, a few cents at $4 / $20 per million tokens (Sonnet 4.6 is $3 / $15).

Alternative: keep `claude-sonnet-4-6` with `temperature=0`. It is closer to repeatable, but on an older model that follows the new rules less reliably, and it is still not deterministic.

### D6 Testing

Without Anthropic (pytest, every call mocked, as the conventions require):
- `format_es`: thousands, decimals, negatives, percentages.
- The summary builder on small CSVs built in the test: periods, means, an incomplete period, peaks with dates, trend figures, size limits (25 months → 24), no summary without a date column.
- The breakdowns: groups, n, the percentage, "otros", low-cardinality numeric columns, outlier sides and ranges, excluded identifiers.
- The prompt: the rules are in the system prompt, and the data block holds the summary with Spanish figures.
- The check: kept and dropped insights, rounding, exempt integers and dates, all dropped, and the warning text.
- `generate_insights` with a mocked client: the request (model, effort, schema, no `temperature`), a refusal, and dropped insights.

Real run with Borja's key, two steps:
1. `python -m demo.generate_demo_fixture --dry-run` (a new flag): prints the insights and the check's report (kept, dropped and why) for both CSVs, writes nothing. Two calls, a few cents. We review the text together, adjust the prompt if needed, and repeat.
2. When the text is right: the normal run writes both fixtures, which we review before the commit (S7).

## Tasks

Provisional until D1-D6 are answered. Route: inline (no Writer trigger).

- [x] T0 inline: close `odd/tasks/forecast-quality.md` (dd96132)
- [x] T1 inline: `docs: add feature document for the insights prompt` (this file)
- [ ] T2 D1: `format_es` and the shared target helper (moved from `tasks._run_predictions`)
- [ ] T3 S2: temporal summary
- [ ] T4 S3: breakdowns and outlier sides
- [ ] T5 S1: system prompt and data block
- [ ] T6 S4: output check
- [ ] T7 S5: model, effort, structured output, refusal; `generate_insights` receives the CSV (worker and fixture script)
- [ ] T8 S6: `--dry-run` in the fixture script; Borja's real run
- [ ] T9 S7: fixtures regenerated by Borja, reviewed, committed
- [ ] T10: verifier, RDD

## Log

- L1 Borja (2026-10-13): "Siguiente PR: el prompt de los insights. Crea la rama desde main. Si el documento de forecast-quality tiene algo pendiente de cierre, va en el primer commit. Lee insights_llm.py y la revisión del backlog (backlog/insights-prompt-review), y escribe el documento odd/tasks con las decisiones abiertas y tu recomendación para cada una: Reglas del prompt: sin afirmaciones causales, solo cifras que estén en los datos recibidos, sin inventar contexto externo, y formato numérico español (coma decimal, punto de miles). Resumen temporal cuando hay columna de fecha: qué se le pasa al modelo (totales o medias por periodo, picos con su fecha, tendencia) y con qué límite de tamaño. Cruces entre columnas: si se le pasan medias del objetivo por categoría (por ejemplo, con y sin promoción), para qué columnas y con qué límite. Validación de la salida: si se comprueba que las cifras de los insights aparecen en los datos de entrada, y qué se hace si no. Temperatura y modelo, pensando en que los resultados sean reproducibles. Qué se puede testear sin llamar a Anthropic y cómo hacemos la prueba real con mi clave. No escribas tests hasta que te conteste. Al final de la PR regeneraremos los fixtures de la demo."
- L2 Branch `fix/insights-prompt` from main 3485774; dd96132 closes `odd/tasks/forecast-quality.md` (L24: #12 merged, branches deleted). Read `insights_llm.py`, `schemas/insights.py`, `tests/test_insights_llm.py`, `demo/generate_demo_fixture.py` and the backlog review; measured both demo CSVs (Current state). Model facts from the Claude API reference: `temperature` returns 400 on Opus 5.5 and Sonnet 5.5; structured outputs through `output_config.format` or `messages.parse`. Waiting for Borja on D1-D6.
