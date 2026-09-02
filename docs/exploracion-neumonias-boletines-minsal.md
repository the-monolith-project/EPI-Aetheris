# Exploración: Neumonías en los boletines MINSAL

**Fecha:** 2026-08-28 · **Estado:** exploración cerrada, nada ingerido a Postgres
**Herramienta:** `backend/ingestion/corrida_respiratorios.py` (parser exploratorio;
salida en `data/interim/corrida_respiratorios/`, gitignoreada)
**Tests:** `backend/ingestion/tests/test_corrida_respiratorios.py` sobre extractos
reales en `tests/fixtures/minsal/*.pagina_tabla_neumonias.txt`
**Protocolo:** `docs/protocolo-exploracion-respiratorios.md`

## Alcance del corpus

264 PDF reales en `backend/ingestion/data/raw/minsal/{2018,2019,2021,2022,2023}/`.
2020 no está en el filesystem (no se copió la exclusión de dengue: simplemente
no había carpeta; la decisión de bajarlo se evalúa con la vigilancia de virus,
no aquí). Nada se fabricó.

## Resultado global (264 boletines)

| Estado | n | Qué significa |
|---|---|---|
| `ok` | 189 | Tabla extraída, suma de 14 departamentos cuadra con un total impreso |
| `ok_discrepancia_minima` | 26 | Cuadre con diferencia ±1 o ±2 propia del boletín (solo 2023) — celdas conservadas |
| `sin_filas_sospecha_imagen` | 25 | Título presente, 0 filas extraíbles — tabla como imagen |
| `ausencia_esperada_vacacion` | 18 | Vacaciones / vigilancia intensificada, sin tabla departamental |
| `sin_texto_extraible` | 4 | 2019: SE28_v2, SE29_v2, SE32, SE35_v2 — 0 menciones de neumonías |
| `revision_manual` | 2 | Reimpresión SE34/2019 = SE33/2019; SE28/2022 declara SE27 en el título |

Cortes usables (`ok` + `ok_discrepancia_minima`, tras reclasificar la reimpresión):
2018: 46 · 2019: 22 · 2021: 50 · 2022: 48 · 2023: 49.

**2019 es el año dañado:** SE01–SE23 tienen la tabla como imagen o sin texto
extraíble; la serie extraíble de 2019 empieza en SE24. Igual patrón que IRA.

Verificación contra casos leídos a mano (5/5): SE01-02/2018 (San Salvador 172,
total 701, corte SE2), SE03/2018 (259 / 1,142, corte SE3 pese a narrativa
"SE 2-2018"), SE01/2023 (101 / 488), SE25/2023 (2,733 / 10,618), SE52/2023
(5,667 / 22,337 impresos; las celdas suman 22,336).

## Respuestas a las 16 preguntas del brief

1. **¿Existe tabla departamental?** Sí. Título típico: *Casos y tasas por grupo
   de edad y departamento de neumonías, SE-N de AAAA* (2018–2022) o *Casos y
   tasas por departamento de neumonías, SE N de AAAA* (2023).
2. **¿Existe en los cinco años?** Sí, con el hueco de 2019 temprana (imagen).
3. **¿Es un conteo único?** Sí: `Departamento | Total | Tasa x 100 mil`.
4. **¿Es clínico/notificado?** Sí: un total notificado, sin confirmación de
   laboratorio declarada. Encaja con la semántica de ADR 0011 (`notificado`),
   **si** el coordinador acepta reutilizarla. No se cierra aquí.
5. **¿Tiene probable/confirmado?** No, en ningún boletín revisado.
6. **¿Es acumulado desde SE1?** Sí. Sobre 2,940 pares consecutivos por
   (año, departamento): 2,912 crecientes, 3 iguales, 25 decrecientes (0.85 %).
   Los decrecientes son correcciones retroactivas (ver 14).
7. **¿Trae tasa x 100 mil?** Sí. No se usa para desacumular.
8. **¿La suma de departamentos cuadra?** En 189 boletines, exacto. En 26 de
   2023, ±1 o ±2 (`ok_discrepancia_minima`); celdas conservadas, nunca
   “corregidas”. Signos observados: −1 (14), +1 (11), +2 (1).
9. **¿Hay fila “Otros países”?** Aparece en 2021–2023, vacía en lo extraído.
   La reconciliación prueba ambas convenciones por si un boletín futuro
   trajera valores.
10. **¿Hay cambios de layout?** Dos familias, detectadas por documento:
    lado-a-lado con grupos de edad (2018–2022, 193 páginas) y página propia
    (2023, 49 páginas). 2018 imprime departamentos sin tilde.
11. **¿Qué ocurre en vacaciones?** 18 boletines sin tabla departamental
    (Semana Santa 2018 diaria, agostinas, fin de año, más SE12/2021 y
    SE14/2022). Detectado por contenido de portada, no por el nombre.
12. **¿Hay tablas como imagen?** 25: SE48/SE50/SE52 de 2018 y casi todo
    SE01–SE23 de 2019. Título extraíble, 0 filas. OCR fuera de alcance.
13. **¿Hay boletines reimpresos?** Uno: SE34/2019_v2 copia exacta de los 14
    valores de SE33/2019 (San Salvador 5,871 en ambos). Reclasificado a
    `revision_manual`. SE10/2018 **no** es reimpresión de Neumonías (sí lo
    era de IRA): SS 1,001 → 1,130.
14. **¿Hay correcciones negativas?** 23 diffs negativos tras desacumular
    (2018: 3, 2021: 1, 2023: 19). Se excluyen de la serie semanal, nunca se
    clampean a cero. Ejemplo: Cuscatlán 2023 SE41 535→518 (diff −17).
15. **¿Hay semanas combinadas?** SE01-02/2018 sí; para Neumonías el corte
    SE2 es un punto válido del acumulador (igual que IRA). No se divide.
16. **¿Qué cobertura efectiva queda?** Cortes usables: 46/52 (2018), 22/52
    (2019), 50/52 (2021), 48/52 (2022), 49/52 (2023). Huecos reales de 2018:
    SE1 (combinada en SE2), SE12, SE48, SE50–SE52. 2022: SE14, SE28
    (título SE27, no ingerible), SE30, SE51.

## Desacumulación

Mismas reglas que IRA/dengue. Puntos semanales con valor: 2,777 (28 de ellos
son el primer corte del año, marcados si no son SE1). Huecos sin interpolar:
462. Correcciones excluidas: 23. **Candidatos a loader (valor presente y
`nota` vacía, span de 1 semana):** 2,749 filas.

La tabla de egresos/fallecidos/letalidad hospitalaria (SIMMOW) que aparece
en la misma sección **no** es esta serie: es otra unidad de observación y
no se extrae aquí.

## Semántica para persistencia (pendiente de ADR / decisión)

Si se aprueba, Neumonías puede vivir en `casos_epidemiologicos` con
`tipo_evento='neumonia'` y `clasificacion='notificado'` (ADR 0011 ya contempla
el formato). No mezclar con IRA. No se escribe migración en esta fase.
