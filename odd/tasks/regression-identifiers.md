# Regression skips identifier columns

Objective: the regression target and its features never use identifier columns (the profile's `is_identifier`). Branch `fix/regression-identifiers` from `main` 0570d2b; single PR against `main`. Runner: `pytest` + `ruff check .` in `apps/api`.

## Specs

- S1 (D1): the regression target is the last numeric column that is not an identifier, read from the profile's `is_identifier` (no copy of the rule).
- S2 (D2): a regression needs at least one other numeric column that is not an identifier; with only identifiers, or one measure plus identifiers, there is no regression.
- S3 (D3): the regression features leave out identifier columns (numeric); categorical and boolean features are unchanged.
- S4 (D4): saved analyses keep their stored predictions; only new analyses change.
- S5: "Comprueba que los fixtures de la demo no cambian (viviendas no tiene identificadores) y añade un test de summary_target con un id al final."

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S1, S2, S5 (summary_target) | inline | done: RED (id chosen as target; all-identifier and measure-plus-id profiles regressed; summary target the id), GREEN; `targets.measures` (numeric, not `is_identifier`) shared by both targets; three `test_breakdowns` tests had a 0..N whole-number column of 50+ rows (a row counter since T7 of charts-fit), now N + 0,5 so they stay measures | a7337d6 |
| T2 | S3 | inline | done: RED (`id` passed as a feature), GREEN; features are `targets.measures` minus the target, plus categorical and boolean columns | (this commit) |
| T3 | S4, S5 (fixtures) | inline | done: `--keep-insights` regeneration leaves both demo fixtures byte-identical (forecast target Ventas, regression target Precio); saved analyses keep their stored predictions (nothing recomputes them) | (this commit) |

## Log

- L1 (2026-10-14, Borja): "Después, nueva rama fix/regression-identifiers desde main: regression_target no filtra identificadores. Antes del primer test, dime: 1) cómo se elige hoy el objetivo de la regresión y qué pasa si todas las columnas numéricas candidatas son identificadores; 2) si las variables de entrada del RandomForest pueden incluir columnas identificador. Plantéame las decisiones con tu recomendación; la regla de identificador se lee del campo is_identifier del perfil, sin copiarla. Test-first, cambios pequeños, método de siempre. Enséñame el resumen antes del push."
- L2: Today `regression_target` returns the last numeric column when there are at least two numeric columns, identifiers included (all-identifier CSVs regress one id on another); `tasks._run_predictions` passes every other numeric column, identifiers included, plus categorical and boolean columns as features. `data_summary.summary_target` uses `regression_target` without a date column, so the insights summary target changes too.
- L3 (2026-10-14, Borja): "D1–D4: sí, las cuatro; lo de aceptar solo categóricas como variables, al backlog. Comprueba que los fixtures de la demo no cambian (viviendas no tiene identificadores) y añade un test de summary_target con un id al final. Sigue con el método de siempre y enséñame el resumen antes del push."
- Backlog (L3): allow a regression whose only features are categorical or boolean columns (`backlog/regression-categorical-features`).
