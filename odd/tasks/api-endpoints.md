# api-endpoints

Objective: endpoint tests for the API against Postgres (PR 2 of `.claude/brief-ci-tests-demo.md`, section 5), with the real REDs D6 (403 → 404 on another user's resources) and P4 (storage error detail returned to the client).
Branch: `test/api-endpoints` from `main` (d40e292). Delivery: ask-on-risk, single PR expected. Runner: `pytest` in `apps/api`, Postgres 16 (`docker compose up -d db` locally, the `postgres:16-alpine` service in CI).

## Specs

- S1 Test database: "cómo montar la base de datos de test con Postgres (por test o por transacción con rollback)". Approved: schema created once per session with `alembic upgrade head`; each test runs inside a connection-level transaction, the `get_db` session joins it with `join_transaction_mode="create_savepoint"` and everything is rolled back at the end. The conftest refuses to run unless the database name ends with `_test`. Without Postgres the tests fail, never skip.
- S2 Users A and B: "cómo simular los usuarios A y B". Approved: `app.dependency_overrides[get_current_user]` with two fixed UUIDs and a fixture to switch user. Plus (L3): "El test sin cabecera Authorization fija el código actual; si es 403, plantéamelo como decisión."
- S3 Real RED, D6: "Si un recurso existe pero es de otro usuario, responder **404** (hoy da 403) en `get_dataset`, `get_analysis` y `_get_analysis_with_auth`". User B reading A's dataset, analysis or PDF gets 404. First task (L3): "empieza por los rojos del 403 → 404."
- S4 Real RED, P4: "P4 con mensaje genérico y el detalle en el log con logging (solo tipo y mensaje de la excepción, nada de cabeceras ni objetos de la petición)." A storage failure on upload returns a generic 500 message to the client and persists nothing.
- S5 Characterization, projects: B cannot read A's project (404); (L3) "Caracteriza también que el usuario B no puede editar ni borrar un proyecto de A: 404 y el proyecto sigue intacto."
- S6 Characterization, upload: "solo `.csv` (422), más de 50 MB (422), proyecto ajeno (404) y caso correcto (201, crea `Dataset` + `Analysis` en `pending` y encola la tarea)"; the three errors persist nothing. (L3) "En el test de más de 50 MB, reduce MAX_FILE_SIZE en el test en lugar de generar 50 MB." `upload_file` and `run_analysis.delay` are mocked.
- S7 Characterization, services: `run_forecast` with fewer than 10 points → `points: []`; "`ml_baseline.run_regression`: devuelve r2, rmse e importancias con un dataset pequeño determinista"; "`tasks._run_predictions`: sin columnas numéricas → `None`; con fecha → forecast; sin fecha → regresión."
- S8 Method (brief section 1): "test-first parando en cada rojo, mutaciones para los tests que pasan a la primera". Characterization tests pass at first by definition and each one is validated with a mutation.

Out of scope (already done): auth.py tests (PRs #4, #5, #7) and the H1 forecast fix (PR #6).

## Tasks

- [x] T1 inline: `docs: add feature document for the API endpoint tests` (this file)
- [x] T2 S1-S3 inline: Postgres test fixtures + `fix(api): return 404 for datasets and analyses owned by another user`
- [ ] T3 S4 inline: `fix(api): hide storage error details from the client`
- [ ] T4 S2, S5, S6 inline: characterization of auth header, projects isolation and upload
- [ ] T5 S7 inline: characterization of forecasting, ml_baseline and _run_predictions
- [ ] T6 S8: mutations, independent verifier (ownership guards are high risk), RDD

Route: inline (no Writer trigger).

## Log

- L1 Borja (2026-10-13): "Siguiente PR: tests de la API (la PR 2 del brief, sección 5). Crea la rama desde main actualizado. Primer commit: el cierre del documento de auth-pyjwt (L15 con Judgment Day y L16 con /security-review). Antes de escribir tests, plantéame las decisiones: cómo montar la base de datos de test con Postgres (por test o por transacción con rollback), cómo simular los usuarios A y B, y qué tests son rojos reales (403 → 404 en recursos ajenos, el error de almacenamiento que hoy se devuelve al cliente) y cuáles son de caracterización. Sigue el documento de la feature"
- L2 Branch test/api-endpoints from d40e292; eff46e1 closes odd/tasks/auth-pyjwt.md. Proposed: transaction rollback per test, dependency_overrides for A/B, REDs D6 (datasets.py:143, analyses.py:36, analyses.py:75) and P4 (datasets.py:71 returns f"Storage upload failed: {e}"), the rest characterization.
- L3 Borja (confirmed directly with "si"): "Apruebo las decisiones, incluida P4 con mensaje genérico y el detalle en el log con logging (solo tipo y mensaje de la excepción, nada de cabeceras ni objetos de la petición). Cuatro añadidos: El test sin cabecera Authorization fija el código actual; si es 403, plantéamelo como decisión. Caracteriza también que el usuario B no puede editar ni borrar un proyecto de A: 404 y el proyecto sigue intacto. En el test de más de 50 MB, reduce MAX_FILE_SIZE en el test en lugar de generar 50 MB. Crea el documento de la feature y empieza por los rojos del 403 → 404."
- L4 T2 in progress (not committed): tests/conftest.py gains the Postgres fixtures (db_engine with the _test guard, a 5 s connect timeout and alembic upgrade head without alembic.ini so its logging config does not disable existing loggers; db_session with create_savepoint; as_user; client; make_dataset) and DATABASE_URL defaults to postgresql+psycopg://postgres:postgres@localhost:5432/datainsight_test. RED tests written: tests/test_datasets.py (dataset) and tests/test_analyses.py (analysis, report.pdf), each with an owner control and B's response compared to a missing id. Without Postgres: the 72 existing tests pass and the 3 new ones error fast with "connection timeout expired". Blocked: `docker` is not available in this WSL distro (Docker Desktop off or its WSL integration disabled).
- L5 Borja: "Docker ya está disponible en WSL. Ejecuta los dos comandos y lanza los rojos". `docker compose up -d db` and `createdb datainsight_test` done. RED (3 failed): dataset, analysis and report.pdf of user A requested by user B give "assert 403 == 404"; each owner control passed first (200, 200, 409). After the run the test database holds 0 projects, 0 datasets, 0 analyses (rollback works) and alembic_version 001.
- L6 Borja: "Sigue con el verde. Que el helper cargue el recurso con una sola consulta (JOIN con el proyecto filtrando por user_id), para que un recurso ajeno y uno inexistente sigan exactamente el mismo camino. Los tests deben comparar el cuerpo completo de la respuesta, no solo el código. Después, mutación: quitar el filtro por usuario debe hacer caer los tres". GREEN: app/db/ownership.py with owned_dataset and owned_analysis built on one `_owned_by` (JOIN projects + Project.user_id filter); get_dataset, get_analysis and _get_analysis_with_auth use them, so a foreign and a missing id raise the same 404 from the same branch (get_analysis now reuses _get_analysis_with_auth). The tests compare the whole JSON body with a missing id's. 75 passed, ruff clean, no 403 left in app/. Mutation (filter removed, __pycache__ deleted, PYTHONDONTWRITEBYTECODE=1, file restored): 3/3 killed, B got 200, 200 and 409 (A's data readable).
