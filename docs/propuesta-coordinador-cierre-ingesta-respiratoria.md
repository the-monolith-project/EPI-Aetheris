# Propuesta al coordinador — cierre de la ingesta respiratoria

**De:** implementación en `feature/ingesta-respiratoria`  
**Fecha:** 2026-08-28  
**Qué se pide:** decisiones que esta rama **no** tomó, para no saltarse al coordinador.

El resto (heatmap de Neumonías, panel de cobertura descriptivo, unificar `/ira` en `/respiratorio`, selector de año, cargar IRA con el loader ya aprobado) se implementó en la rama sin esperar estas respuestas.

---

## 1. Regenerar `db/seed/seed_datos_reales.sql` (ADR 0010)

**Hecho hoy:** Neumonías (2,749 filas) y vigilancia de virus (3,028) están en el volumen de desarrollo. El seed versionado **no** las incluye.

**Qué pasa si no se regenera:** `git clone` + `docker compose down -v` + `up` aplica la migración `0008` (tabla vacía y catálogo `neumonia`) y no trae las filas. Hay que volver a correr `corrida_respiratorios.py` + loaders (y `corrida_ira.py` + `cargar_ira.py`).

**Propuesta:** regenerar el volcado `pg_dump --data-only` según ADR 0010 (hechos sí, catálogos no) cuando el equipo decida que vale una foto más reciente.

**No se hizo aquí:** el ADR dice que actualizar el seed es decisión explícita, no un efecto colateral de otra tarea.

---

## 2. Confirmar ADR 0012 (estado escrito como Aceptado)

La tabla `vigilancia_virus_respiratorios` se creó **después** del ADR, con evidencia de 264 PDF. El estado del archivo está en **Aceptado** para poder migrar, siguiendo el brief de la rama.

**Propuesta:** que el coordinador confirme o corrija ese estado. Si se rechaza el diseño EAV, hace falta una migración nueva que lo reemplace (sin rollback automático, ADR 0009).

---

## 3. `astro check` / ESLint

El checklist de la rama pide `astro check`/lint **si están disponibles**. `@astrojs/check` no está en `web/package.json`. La aprobación técnica de esas herramientas (2026-08-13) dice que **instalar ≠ adoptar**.

**Qué se hizo:** `pnpm build` (cuando se pudo) y revisión HTTP de `/respiratorio`. No se instaló `@astrojs/check`.

**Propuesta:** si el coordinador quiere typecheck en CI, instalarlo en un cambio aparte (`docs/levantamiento-gaps-stack-web.md`).

---

## 4. 2020 para SARS-CoV-2

La exploración no encontró fila `COVID 19` en 2018–2022; aparece en 2023. **No se descargó 2020.**

**Propuesta:** solo bajar 2020 si se quiere contexto de pandemia como serie aparte, con `descargar_2020.py`, sin meter esos PDF en dengue/IRA.

---

## 5. Fuera de esta propuesta (ya resuelto en código)

- Neumonías reutiliza `'notificado'` (ADR 0011 lo anticipaba para este formato).
- Virus no van a `casos_epidemiologicos`.
- M4 sigue sin fórmula: el panel de cobertura **cuenta** huecos y cita la exploración; no calcula un score.
