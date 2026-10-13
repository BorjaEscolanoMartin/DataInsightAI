# auth-pyjwt

Objective: verify Supabase tokens with PyJWT instead of python-jose, closing the Dependabot alerts for python-jose (critical) and ecdsa (high).
Branch: `fix/auth-pyjwt` from `main` (afb0822). Delivery: ask-on-risk, single PR expected (forecast ~300 authored lines). Runner: `pytest` in `apps/api`.

## Specs

- S1 Order: "primero cambiar los ayudantes de los tests para que firmen sin python-jose, con el código aún sin cambiar y los 61 tests en verde; después cambiar el código sin tocar ningún test." (The suite has 65 tests at afb0822, not 61: PR #6 added 4.) Test helpers sign by hand with `cryptography` (ES256, RS256, HS256), because PyJWT refuses to sign two attack cases (empty HMAC key, non-string kid).
- S2 "Mantener nuestra caché del JWKS (sin PyJWKClient)."
- S3 Claims, per PyJWT 2.15.1 behaviour checked locally: require exp, aud, sub and iss with `options={"require": [...]}` plus `audience=` and `issuer=` (without `require`, a token without exp is accepted). PyJWT rejects a non-string sub (`InvalidSubjectError`) and any `crit` extension (`Unsupported critical extension`).
- S4 Error mapping: "qué excepciones mapear a 401 sin que los errores del JWKS dejen de ser error del servidor." Catch only `jwt.InvalidTokenError` for 401. The key is built with `PyJWK.from_dict(jwk)` without forcing the algorithm, with `algorithms=["ES256"]`, so a kid naming an RSA key is `InvalidAlgorithmError` (401). A broken key in the JWKS (`InvalidKeyError`/`PyJWKError`), httpx errors and `JwksUnavailableError` stay server errors.
- S5 "Que el uv.lock final ya no contenga python-jose ni ecdsa."
- S6 New tests (L2, L3): "crit rechazado, y clave rota del JWKS → error del servidor" as real REDs: "enséñame que fallan con python-jose y commitéalos junto con la migración en C3, comprobando que en tests/ solo hay líneas añadidas." "Si el JWKS trae una clave rota y otras buenas, un token con un kid bueno debe seguir dando 200. Inclúyelo en el test de la clave rota." The 65 existing tests do not change in the migration commit.
- S7 Migration commit type: "C2 como fix(auth):, no refactor, porque cambia comportamiento."
- S8 Closure: "Al terminar: mutaciones sobre el código final, verificador independiente y RDD; después lanzo Judgment Day y /security-review."

## Tasks

- [x] T1 inline: `docs: add feature document for the PyJWT migration` (this file)
- [x] T2 S1 inline: `test(auth): sign test tokens without python-jose`, 65 green with python-jose still in the code — 9914c8e
- [x] T3 S2-S7 inline: `fix(auth): verify tokens with PyJWT`, with the two S6 tests (RED on python-jose first)
- [ ] T4 S8: mutations on the final code, independent verifier, RDD; then Judgment Day and /security-review by Borja

Route: inline (no Writer trigger). Verification trigger fires (high risk: auth, dependencies): independent verifier after T3.

## Log

- L1 Borja (2026-10-13): "Siguiente PR: migrar la verificación de tokens de python-jose a PyJWT, para cerrar los avisos de Dependabot de python-jose (crítico) y ecdsa (alto). Crea la rama desde main actualizado y el documento de la feature, que esta vez sí se commitea. Antes de escribir nada, plantéame: Orden en dos pasos: primero cambiar los ayudantes de los tests para que firmen sin python-jose, con el código aún sin cambiar y los 61 tests en verde; después cambiar el código sin tocar ningún test. Mantener nuestra caché del JWKS (sin PyJWKClient). Según la documentación de PyJWT: cómo exigir exp, aud, sub e iss, si valida que sub sea texto, cómo trata la cabecera crit, y qué excepciones mapear a 401 sin que los errores del JWKS dejen de ser error del servidor. Que el uv.lock final ya no contenga python-jose ni ecdsa. Al terminar: mutaciones sobre el código final, verificador independiente y RDD; después lanzo Judgment Day y /security-review."
- L2 Borja: "Apruebo el plan con tres cambios: Los dos tests nuevos (crit rechazado, y clave rota del JWKS → error del servidor) van antes de C2 como rojos reales: enséñame que fallan con python-jose y que C2 los pone en verde. Los 65 tests existentes no cambian en C2; compruébalo con git diff --stat sobre tests/. Si el JWKS trae una clave rota y otras buenas, un token con un kid bueno debe seguir dando 200. Inclúyelo en el test de la clave rota. C2 como fix(auth):, no refactor, porque cambia comportamiento."
- L3 Borja: "Confirmo, es mío. Los dos tests nuevos no van en un commit propio: enséñame que fallan con python-jose y commitéalos junto con la migración en C3, comprobando que en tests/ solo hay líneas añadidas."
- L4 PyJWT 2.15.1 (already in uv.lock as a transitive dependency) probed locally: exception tree (all token errors under InvalidTokenError; InvalidKeyError and PyJWKError only under PyJWTError), require semantics, sub type, crit, non-string kid rejected by get_unverified_header, RSA JWK with forced ES256 raises InvalidKeyError.
- L5 T2: one hand signer `_signed_token` (ES256 raw r||s, RS256 PKCS1v15, HS256) built on `cryptography`; the legacy HS256 tokens keep their header without kid, as python-jose produced them. 65 passed, no jose import left in tests; PyJWT verifies the hand-signed ES256, RS256 and HS256 tokens. Commit 9914c8e.
- L6 T3 RED on python-jose: crit registered-claim and unknown-extension accepted ("DID NOT RAISE HTTPException"); broken JWK missing-x and missing-kty answered 401 (jose JWKError). Broken JWK point-off-the-curve already a server error with jose (ValueError), kept as regression. The good-kid half returns the user id in every case.
- L7 T3 GREEN: pyjwt[crypto]>=2.15 replaces python-jose; `uv lock` removed ecdsa, pyasn1, python-jose and rsa; `uv lock --check` OK; no python-jose/ecdsa entry in uv.lock. auth.py: PyJWK.from_dict without forced algorithm, require exp/aud/iss/sub, only InvalidTokenError mapped to 401, the redundant kid isinstance check removed (PyJWT enforces it). Venv synced to the lock (jose and ecdsa absent): 70 passed, ruff clean. tests/ diff vs 9914c8e: 51 added, 0 removed.
