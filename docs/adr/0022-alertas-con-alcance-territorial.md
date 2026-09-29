# 0022 - Alertas con alcance territorial

**Estado:** Aceptado (2026-09-29)

## Contexto

Las alertas de campo (ADR 0013, ADR 0015) son nacionales por construcción: la tabla `alertas` no tiene territorio. Quien atiende en una unidad ve todas las alertas vigentes y no puede saber cuáles le corresponden. La ficha departamental y el mapa no pueden mostrar las alertas que aplican a un departamento.

## Decisión

**A. Columna `alertas.departamentos TEXT[]`, nula por defecto.** `NULL` significa alcance nacional. Una lista no vacía limita la alerta a esos departamentos. Una lista vacía no se guarda: la API la convierte en `NULL`.

**B. Códigos ISO 3166-2**, los mismos de `web/src/lib/departamentos.ts` (`SV-AH`, `SV-CA`, ..., `SV-US`). Un `CHECK` de la migración rechaza cualquier elemento fuera de los 14.

**C. El alcance lo asigna quien emite la alerta.** No se infiere de M1, M2 ni M3, igual que el tipo y el nivel (ADR 0013).

**D. Filtro en el GET público.** `GET /api/alertas?departamento=SV-SS` devuelve las alertas nacionales y las que incluyen ese departamento. Sin el parámetro, la respuesta es la de antes. Un código desconocido responde 422.

**E. Las alertas existentes quedan nacionales.** La migración no reescribe filas.

## Consecuencias

- El frontend puede filtrar por departamento, marcar los departamentos con alerta vigente en el mapa y mostrar en la ficha solo las alertas que aplican.
- El campo `departamentos` aparece en cada alerta del JSON (`null` o lista de códigos). Los clientes que lo ignoran siguen funcionando.
- Una alerta regional no dice nada sobre los demás departamentos: su ausencia no es una señal.

Migración: `db/migrations/0013_alertas_departamentos.sql`.
