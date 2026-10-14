# Yearly extremes in the insights and the W10 API changes

Objective: the insights temporal summary lists each year's highest and lowest period with incomplete years marked, and the prompt forbids generalising across years; the API stops sending `bin` and renames two chart titles (W10). Branch `feat/insights-yearly` from `main` 2310186; one PR against `main`, no push without Borja's yes. Runner: `pytest` + `ruff check .` in `apps/api`; web tests after the fixture regeneration.

## Specs

- S1: "el resumen temporal del prompt debe incluir, por año, el mes con la media más alta y el más bajo con sus cifras, marcando los años incompletos". D1: calendar years. D2: a year is incomplete when it lacks any of its periods or has an incomplete one, marked with its span («2024 (incompleto: oct–dic)»); its highest and lowest are chosen among its complete periods only; only years within the periods the block already shows, with at least 2 complete periods; quarters work the same way (4 per year); yearly data adds nothing.
- S2: "el prompt debe pedir que no se afirme «en ambos años», «cada año» o «siempre» lo que no se cumple en todos, ni se llame máximo o mínimo a lo que solo lo es dentro de un año." D3, exact rule: "No generalices entre años: escribe «en ambos años», «cada año» o «siempre» solo si se cumple en todos los años de «Por año», incluidos los incompletos; si no, di en qué año ocurre. Llama máximo o mínimo solo al valor más alto o más bajo de toda la serie; el de un año es «el más alto de 2025». De un año marcado como incompleto no digas cuál es su máximo o su mínimo del año entero."
- S3 (W10): "dejar de generar bin en los análisis nuevos (la web ya usa start/end y conserva el respaldo para los antiguos)".
- S4 (W10): "cambiar los títulos a «Valores de X» y «X frente a Y»". D4: saved analyses keep their stored titles (a saved analysis is a snapshot; no rewrite in the web, no data migration).
- S5: "Cuando todo pase, prepárame el comando para regenerar los fixtures, que lo ejecuto yo, y después revisa los insights cifra a cifra, con especial atención a las afirmaciones entre años." "No hagas push sin mi sí."

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S1 (summary data) | inline | done: RED (no `years`), GREEN; `_year_extremes` groups the shown periods by calendar year, picks highest and lowest among complete periods, marks a year incomplete when a period is missing or partial, skips years with fewer than 2 complete periods and yearly data; mutants (1 complete period enough; partial months counted) fail | (this commit) |
| T2 | S1 (prompt lines), S2 | inline | pending | |
| T3 | S3 | inline | pending | |
| T4 | S4 | inline | pending | |
| T5 | S5 | inline | pending (Borja runs the regeneration) | |

## Log

- L1 (2026-10-14, Borja): "Nueva tarea, una PR contra main (rama feat/insights-yearly desde main actualizado), con dos partes. (1) Insights: el resumen temporal del prompt debe incluir, por año, el mes con la media más alta y el más bajo con sus cifras, marcando los años incompletos; y el prompt debe pedir que no se afirme «en ambos años», «cada año» o «siempre» lo que no se cumple en todos, ni se llame máximo o mínimo a lo que solo lo es dentro de un año. (2) API, W10 del backlog: dejar de generar bin en los análisis nuevos (la web ya usa start/end y conserva el respaldo para los antiguos) y cambiar los títulos a «Valores de X» y «X frente a Y». Antes del primer test, plantéame las decisiones con tu recomendación: año natural o ciclo de 12 meses, cómo se marcan los años incompletos, el texto exacto de la regla del prompt, y si los títulos antiguos guardados necesitan algo. Test-first. Cuando todo pase, prepárame el comando para regenerar los fixtures, que lo ejecuto yo, y después revisa los insights cifra a cifra, con especial atención a las afirmaciones entre años. No hagas push sin mi sí." (pasted; Borja: "es mía")
- L2 (2026-10-14, Borja): "D1–D4: sí, las cuatro como las propones. Antes de empezar, respóndeme la parte (3): ¿producción sirve el último commit de main? ¿Se implementaron el grosor de las barras de categorías y el ancho de la columna de etiquetas? Después sigue con el método de siempre." Answer: both production deployments (Vercel `Production`, Railway `empathetic-smile / production`) are `main` 2310186, state success; category bars keep `barSize={8}` and a 100 px label column (since b6a026f), not in W1–W10, so not done.
