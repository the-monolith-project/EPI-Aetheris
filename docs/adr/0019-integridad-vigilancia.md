# 0019 - Integridad de la vigilancia (Módulo 4)

**Estado:** Aceptado (2026-09-08)

## Contexto

El selector de capas del mapa tenía una capa `'confianza'` deshabilitada
("próximamente") y el panel `AuditoriaDatos.astro` era estático, con la
nota de que M4 no tenía fórmula. El punto A de
`docs/contexto/02-decisiones-abiertas.md` dejaba abierta tanto la
fórmula como el lugar de la salida.

El coordinador cerró la fórmula el 2026-09-08: tres métricas
verificables, sin combinarlas en un número único, y `antiguedad` en
lugar de latencia real de reporte. No hay dato de fecha de publicación
del boletín (`fecha_procesado` es el timestamp de *nuestra* corrida del
parser). Recuperar latencia real queda fuera de alcance.

El número es 0019: 0017 (endurecimiento del backend) y 0018 (extensión
de la capa climática al año en curso) ya están en `dev`.

## Decisión

**A. Tres métricas, nunca un índice compuesto.**

1. `completitud` — n/14 departamentos con fila en
   `casos_epidemiologicos` para `(anio, semana_epi, clasificacion)`,
   `nivel_admin = 1`, dengue MINSAL (`probable` y `confirmado` por
   separado). Hueco ≠ cero. También se agrega por año (semanas con
   14/14 frente a 52 nominales).
2. `cuadre` — expone `validacion_cuadra` y la magnitud
   `suma_departamental − total_nacional_publicado` ya almacenados en
   `boletines_procesados`. M4 no recalcula la suma de 14.
3. `antiguedad` — semanas epidemiológicas (PAHO/CDC, librería
   `epiweeks`) entre hoy y la última SE con dato, por serie (dengue
   MINSAL departamental, OpenDengue nacional, clima, IRA, neumonías,
   virus respiratorios). No es latencia de reporte.

**B. On-request, nada persistido, sin cambio de esquema.** Mismo patrón
que M1/M2/M3. Endpoint `GET /api/v1/vigilancia/integridad`. `week` y
`year` juntos piden la vista semanal del mapa; sin parámetros, el
resumen anual y la antigüedad. `@limiter.limit(RATE_LIMIT_HEAVY)` y
`Cache-Control` de cómputo (900 s).

**C. Capa `'confianza'` del mapa.** Se habilita. El color codifica
únicamente "hay dato / falta dato / el boletín no cuadra". No es un
semáforo de riesgo. El aviso de honestidad niega transmisión e índice
compuesto.

**D. `AuditoriaDatos.astro`.** Pasa a computado para completitud anual y
antigüedad; conserva estáticos los hechos que no son métrica (ventana,
exclusión de 2020).

### Alternativas descartadas

* Un índice compuesto 0–1 o un semáforo — descartado: vuelve opaca una
  función cuyo valor es precisamente mostrar hechos auditables.
* Latencia real de reporte (evento → publicación) — descartado: no hay
  fecha de publicación en `boletines_procesados`. Recuperarla exigiría
  un backfill desde los PDF, fuera de esta tarea.
* Persistir las métricas en una tabla nueva — descartado: el cálculo es
  barato y las fuentes ya están en Postgres.

## Consecuencias

* Positivo: la capa "próximamente" deja de ser una promesa incumplida y
  el corte de 2023 se vuelve una cifra (antigüedad), no un silencio.
* Positivo: sin migración. Un ADR de esquema no aplica.
* Negativo: `antiguedad` depende de `date.today()`, así que el cache de
  15 minutos puede mostrar un valor de semanas desfasado en el borde de
  una SE. Aceptado: cambia como máximo una vez por semana.
* Neutral: el id de capa sigue siendo `'confianza'` para no romper el
  selector; la etiqueta visible es "Integridad de la vigilancia".
