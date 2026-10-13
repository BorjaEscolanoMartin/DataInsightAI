# demo

Objective: a public, read-only `/demo` page that shows a precomputed analysis of two synthetic datasets with the current look (PR 3 of `.claude/brief-ci-tests-demo.md`), plus Vitest in the web app.
Branch: `feat/demo` from `main` (ce3b7c4). Delivery: ask-on-risk, single PR expected. Runners: `pytest` and `ruff` in `apps/api`; `npm test` (Vitest), `typecheck`, `lint` and `build` in `apps/web`.

## Specs

- S1 Datasets: "Dos datasets: demo_ventas_diarias.csv (previsión) y demo_viviendas.csv (regresión)." Selector (L2): two buttons with `aria-pressed`, local state, sales selected by default; both fixtures imported statically.
- S2 Scope: "Esta PR solo hace la demo funcional, con el aspecto actual. El rediseño irá en otra PR." "La descarga del PDF queda fuera de la demo, porque exige sesión."
- S3 Tests: "Vitest en el front, con un test mínimo: /demo se renderiza con el fixture sin hacer ninguna petición de red. Añádelo a CI." Dev dependencies approved (L2): vitest, @vitejs/plugin-react, jsdom, @testing-library/react.
- S4 Shared view: "Extrae la vista del análisis de projects/[id]/page.tsx a un componente reutilizable, sin cambiar su comportamiento, y úsalo en la página del proyecto y en /demo." Props are only what it renders (filename, size, row and column counts, profile, insights, predictions), so the fixture needs no ids.
- S5 Middleware: "Comprueba si el middleware llama a Supabase en /demo. Si lo hace, propón cómo evitarlo." It does: the matcher covers every non-static path and always calls `supabase.auth.getUser()`. Fix: exclude `/demo` in the matcher (`demo(?:/|$)`). L2: "prueba el matcher con unstable_doesMiddlewareMatch si existe en nuestra versión de Next, en lugar de una RegExp" (it exists in next 15.5.27, `next/experimental/testing/server`). Also prove `/projects` still matches.
- S6 Fixture: "El script que genera el fixture llama a Anthropic: enséñamelo y lo ejecuto yo. Lee la clave del entorno y nunca la escribe. Antes del commit revisamos que el JSON no lleve rutas, IDs ni nada de Supabase." Script `apps/api/demo/generate_demo_fixture.py` runs profile_csv, generate_insights and _run_predictions on each CSV.
- S7 Generator (brief PR 3 step 0): move `generate_demo_data.py` and both CSVs from `.claude/demo-data/` to `apps/api/demo/`, adapted to the project conventions (English identifiers and comments, ruff). L2: "el test de determinismo de T2".
- S8 Demo page: `src/app/demo/page.tsx` outside `/projects`; a "Ver demo" link on `/login` (`/` only redirects). L2: "en T6, un aviso visible de que los datos son sintéticos; y en el build dime el First Load JS de /demo. Si supera 300 kB, lo hablamos antes de seguir".
- S9 Closure: independent verifier (the middleware change touches the auth guard), RDD; Judgment Day and /security-review by Borja.

## Tasks

- [x] T1 inline: `docs: add feature document for the public demo` (this file)
- [x] T2 S7 inline: move the demo data generator and CSVs to apps/api/demo, with a determinism test
- [ ] T3 S6 inline: fixture generator script (shown to Borja, run by Borja), fixture JSON reviewed before commit
- [ ] T4 S4 inline: extract AnalysisView, used by the project page
- [ ] T5 S5 inline: exclude /demo from the middleware, tested with unstable_doesMiddlewareMatch
- [ ] T6 S1, S2, S8 inline: /demo page, selector, synthetic-data notice, "Ver demo" link; report First Load JS of /demo
- [ ] T7 S3 inline: Vitest setup, /demo render test without network, CI step
- [ ] T8 S9: verifier, RDD; Judgment Day and /security-review by Borja

Route: inline (no Writer trigger). Open questions: none after L2.

## Log

- L1 Borja (2026-10-13): "Empezamos la PR 3, la demo, siguiendo la sección «PR 3 — Demo pública» del brief. Si alguna rama anterior tiene documento sin cerrar, ese cierre va en el primer commit. Decisiones tomadas: Dos datasets: demo_ventas_diarias.csv (previsión) y demo_viviendas.csv (regresión). Plantéame cómo elegir entre los dos en /demo, con tu recomendación. Esta PR solo hace la demo funcional, con el aspecto actual. El rediseño irá en otra PR. Vitest en el front, con un test mínimo: /demo se renderiza con el fixture sin hacer ninguna petición de red. Añádelo a CI. Además: Extrae la vista del análisis de projects/[id]/page.tsx a un componente reutilizable, sin cambiar su comportamiento, y úsalo en la página del proyecto y en /demo. Comprueba si el middleware llama a Supabase en /demo. Si lo hace, propón cómo evitarlo. El script que genera el fixture llama a Anthropic: enséñamelo y lo ejecuto yo. Lee la clave del entorno y nunca la escribe. Antes del commit revisamos que el JSON no lleve rutas, IDs ni nada de Supabase. La descarga del PDF queda fuera de la demo, porque exige sesión. Antes del primer test, el documento odd/tasks con el plan y las preguntas abiertas."
- L2 Borja (direct message): "Confirmo el plan con los botones como selector, con aria-pressed, y las cuatro dependencias de Vitest. Añade: el test de determinismo de T2; en T5, prueba el matcher con unstable_doesMiddlewareMatch si existe en nuestra versión de Next, en lugar de una RegExp; en T6, un aviso visible de que los datos son sintéticos; y en el build dime el First Load JS de /demo. Si supera 300 kB, lo hablamos antes de seguir". No feature document was left open (all five in odd/tasks have every task checked).
- L3 T2: apps/api/demo/generate_demo_data.py is the brief's generator with English identifiers, comments and docstrings, a `generate(output_dir)` function and module constants (SEED, DAILY_SALES_CSV, HOUSING_CSV); column names and values stay in Spanish (they are the demo data). Its output is byte-identical to the original CSVs (md5 59fd5dd8… and 782c6ea2…), which are copied to apps/api/demo/ (the originals stay in the git-ignored .claude/demo-data/). tests/test_demo_data.py: the generator reproduces the committed files, and two runs write identical files. Both passed at first; mutations: SEED 43 killed the first, an unseeded generator killed both. 119 passed, ruff clean.
