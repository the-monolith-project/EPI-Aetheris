# 0018 - Extensión de la capa climática (M1/M2) más allá de 2023

**Estado:** Aceptado (2026-09-08)

> No implementa el refresco recurrente (A2). La forma de ese job
> (GitHub Actions contra host externo vs `type: cron` en Render) sigue
> abierta. Este ADR cubre el backfill hasta el presente y el pool
> leave-one-out.

## Contexto

Los módulos 1 (idoneidad biofísica `Iv`) y 2 (anomalía climática
continua) dependen solo de clima ERA5-Land / ERA5 vía Open-Meteo, no de
los boletines MINSAL. MINSAL dejó de publicar tablas raspables; el mapa
se veía "detenido en 2023" aunque la capa biofísica podía seguir.

Hasta este ADR, `ANIOS_CLIMA = list(range(2014, 2025))` en
`backend/api/idoneidad.py` y en
`backend/ingestion/validar_leadtime_camino_ancho.py` (copias
deliberadas, sin paquete compartido). Aunque `variables_ambientales`
tuviera filas de 2025, los endpoints
`GET /api/v1/spatial/current` y `GET /api/v1/temporal/{codigo}` no las
consultaban.

El archive `archive-api.open-meteo.com` no acepta fechas futuras y el
reanálisis ERA5 tiene un rezago de unos 5 días. Cerrar ese último tramo
con el modelo de pronóstico sería nowcasting: otra tarea.

## Decisión

**A. `ANIOS_CLIMA` crece hasta el año calendario en curso.** Las dos
copias se mantienen iguales a mano. El default de `--anio-fin` en
`cargar_clima.py` pasa a ser el año en curso. `fecha_fin` se recorta a
hoy para no pedir al archive un 31 de diciembre futuro.

**B. AMPLIAR el baseline leave-one-out (coordinador, 2026-09-08).** Los
años nuevos entran al pool de `calcular_baseline_semana`. Congelar
2014–2024 habría ignorado clima reciente a propósito. Consecuencia
asumida: **mediana y σ de las semanas 2018–2023 ya publicadas se
recalculan y se mueven.** Queda escrito aquí y en el CHANGELOG; no es
un efecto colateral silencioso.

**C. El rezago ERA5 de ~5 días se declara, no se rellena.** Ausencia
de los últimos días no se convierte en cero ni se imputa con
pronóstico. No se usa `best_match` (ADR 0006).

**D. Honestidad de interfaz.** `AVISO_HONESTIDAD_IDONEIDAD` y el panel
de auditoría distinguen condición biofísica (clima, hasta el presente)
de incidencia y de presión epidemiológica (M3 / casos MINSAL, hasta
2023). M3, `/api/v1/analisis/dengue`, IRA y neumonías no cambian de
ventana.

**E. Sin cambio de esquema.** Nada de M1/M2 se persiste. El volcado
`db/seed/seed_datos_reales.sql` no se regenera en esta pasada: un
`git clone` + `docker compose up` sigue sin clima 2025+ hasta un
backfill operativo o un seed nuevo.

### Alternativas descartadas

* Congelar el pool en 2014–2024 y solo pintar años nuevos contra esa
  historia — descartado por el coordinador: omitir los años recientes
  del baseline sería su propia forma de deshonestidad.
* Cerrar el rezago de ~5 días con el modelo de pronóstico de
  Open-Meteo — fuera de alcance; es nowcasting.
* Job semanal (A2) — decisión de infraestructura abierta.

## Consecuencias

* Positivo: M1/M2 pueden describir la condición ambiental de 2024 hasta
  el presente (menos el rezago ERA5) sin fabricar casos.
* Positivo: el corpus leave-one-out no ignora el clima reciente.
* Negativo: los valores de anomalía σ ya mostrados para 2018–2023
  cambian al entrar años nuevos al pool. Quien compare capturas
  anteriores con las actuales verá diferencias numéricas.
* Negativo: sin A2 ni seed regenerado, producción en Render sigue con
  el volcado que termina en 2024 hasta que alguien corra
  `cargar_clima.py` contra esa base.
* Neutral: las dos copias de `ANIOS_CLIMA` siguen duplicadas; el test
  de fórmulas duplicadas falla si se desincronizan.
