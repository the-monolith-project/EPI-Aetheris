# Cierre documental — ingesta respiratoria

**Rama:** `feature/ingesta-respiratoria`  
**Fecha original de la propuesta:** 2026-08-28  
**Cierre documental:** 2026-09-01

Las preguntas que esta rama no tomó por su cuenta quedan con una sola
verdad. No hay confirmación pendiente para merge por ADR 0012, seed ni
tooling de Astro.

---

## 1. Seed `db/seed/seed_datos_reales.sql` (ADR 0010) — hecho

Foto regenerada 2026-09-01 con los mismos flags del ADR (`pg_dump --data-only
--disable-triggers`, catálogos fuera). Incluye `vigilancia_virus_respiratorios`
y las filas de Neumonías/IRA en `casos_epidemiologicos`.

Recuentos de la foto:

```text
Neumonías: 2.749
Vigilancia viral: 3.028
IRA: 2.742
```

Los `tipo_evento_id` del volcado siguen el orden de un volumen limpio
(`0001` dengue=1, `0007` ira=2, `0008` neumonia=3), no el orden accidental
de la base de desarrollo.

---

## 2. ADR 0012 — Aceptado

Estado inequívoco: **Aceptado** (2026-08-28). `vigilancia_virus_respiratorios`
es la tabla correcta para muestras, detecciones y positividad nacionales.
No se reabre ni queda “pendiente de confirmación”.

---

## 3. `astro check` / ESLint / Prettier — disponibles

`web/package.json` ya declara `check`, `lint`, `format:check` y las
dependencias `@astrojs/check`, ESLint, Prettier y Playwright. La nota
anterior de que `@astrojs/check` no estaba instalado quedó obsoleta
(adopción ya presente en `web/package.json`). La validación de cierre de esta rama
ejecuta esos scripts; no se instala nada nuevo aquí.

---

## 4. 2020 para SARS-CoV-2 — fuera de alcance

Sigue sin descargarse. COVID-19 como fila de la tabla laboratorial aparece
en 2023. Bajar 2020 exigiría decisión explícita aparte, no forma parte
del cierre de esta rama.

---

## 5. Ya resuelto en código (sin cambio)

- Neumonías reutiliza `'notificado'` (ADR 0011).
- Virus no van a `casos_epidemiologicos`.
- M4 sigue sin fórmula: el panel de cobertura cuenta huecos y cita la
  exploración; no calcula un score.
