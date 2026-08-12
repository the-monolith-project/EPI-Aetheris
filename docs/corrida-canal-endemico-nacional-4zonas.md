# Corrida del canal endémico — 4 zonas OPS, serie nacional (2026-08-11)

> Resumen de una página de `backend/ingestion/corrida_canal_endemico_4zonas.py`. Continuación directa de `corrida_canal_endemico_nacional.py` (docs/corrida-canal-endemico-nacional.md) — no reabre ninguno de sus parámetros. Exploratorio: no entrena nada, no decide el colapso a 3 clases que sigue abierto en `docs/contexto/02-decisiones-abiertas.md`, punto A. Salida completa (no versionada) en `backend/ingestion/data/interim/canal_endemico_nacional_4zonas/`.

## Método

Mismo cálculo de línea base ya validado: `casos_epidemiologicos` (`clasificacion='total'`, fuente `opendengue_v1_3`, nivel nacional), años base **2018, 2019, 2021, 2022, 2023** (2020 excluido), regla de fuga, ventana de semanas vecinas **±1** sin envolver entre años, piso de suficiencia de 12 observaciones con ≥3 de 4 años base.

Sobre esa misma línea base se calculan ahora las **cuatro zonas clásicas del canal endémico OPS/PAHO**, a partir de P25/P50/P75:

| Zona | Corte |
|---|---|
| Éxito | valor ≤ P25 |
| Seguridad | P25 < valor ≤ P50 |
| Alarma | P50 < valor ≤ P75 |
| Epidemia | valor > P75 |

El cálculo se separa en dos pasos independientes: **paso 1** calcula las 4 zonas (no decide nada sobre 3 clases); **paso 2** colapsa a 3 clases según un mapeo explícito pasado como parámetro, no hardcodeado dentro del paso 1 — así se pueden comparar mapeos distintos sin recalcular percentiles.

**Nota de convención:** el corte usa límite inferior estricto (`>`), igual que `clasificar()` en el módulo base — no la definición de libro `[P50, P75)` para alarma. Es deliberado: así el colapso queda matemáticamente idéntico, celda por celda, al esquema P50/P75 ya calculado, y se puede verificar contra él (ver abajo).

## Suficiencia

Misma cifra que la corrida anterior, porque es la misma línea base: 260 celdas evaluadas, **250 (96,2 %) cumplen el piso de suficiencia**.

## Verificación cruzada

Mapeo de colapso usado para la verificación: `éxito + seguridad → bajo`, `alarma → medio`, `epidemia → alto`. Comparado celda por celda (no solo en el total agregado) contra `clase_p50_p75_original` de `clasificar()` en `corrida_canal_endemico_nacional.py`, sobre las 250 celdas con suficiencia:

| Año | Éxito+Seguridad (colapsado) | Bajo (P50/P75 original) | Alarma (colapsado) | Medio (original) | Epidemia (colapsado) | Alto (original) |
|---|---|---|---|---|---|---|
| 2018 | 15+19=34 | 34 | 12 | 12 | 4 | 4 |
| 2019 | 0+0=0 | 0 | 9 | 9 | 41 | 41 |
| 2021 | 39+8=47 | 47 | 2 | 2 | 1 | 1 |
| 2022 | 6+4=10 | 10 | 9 | 9 | 31 | 31 |
| 2023 | 26+22=48 | 48 | 2 | 2 | 0 | 0 |

**0 discrepancias en 250 celdas.** El script aborta con `SystemExit` sin escribir salida si hay al menos una — no ocurrió.

## Distribución de las 4 zonas (solo celdas con suficiencia)

| Año | Éxito | Seguridad | Alarma | Epidemia |
|---|---|---|---|---|
| 2018 | 15 | 19 | 12 | 4 |
| **2019** (pico histórico) | 0 | 0 | 9 | **41** |
| 2021 | 39 | 8 | 2 | 1 |
| 2022 | 6 | 4 | 9 | **31** |
| 2023 | 26 | 22 | 2 | 0 |

## Lectura, no decisión

- 2019 no tiene ninguna semana en éxito ni seguridad — toda la serie de ese año cae en alarma o epidemia, consistente con ser el pico histórico.
- 2022 (segundo pico) reparte casi la mitad de sus semanas en epidemia, pero conserva más semanas en éxito/seguridad que 2019 — la distinción de 4 zonas separa mejor la intensidad relativa de ambos picos que el colapso a 3 clases, que en P50/P75 los deja a los dos mayoritariamente "alto".
- 2021 y 2023 (años bajos) concentran la gran mayoría de semanas en éxito/seguridad, con muy poca presencia en alarma y casi ninguna en epidemia.
- Esta corrida no decide el colapso final a 3 clases — sigue siendo del coordinador (punto A). Lo que aporta es el nivel de detalle intermedio (4 zonas) para que esa decisión se tome viendo dónde exactamente se pierde información al colapsar, en vez de sobre el resultado ya reducido.

## Pendiente

Igual que la corrida anterior: repetir sobre la vía departamental si el reconteo de MINSAL la habilita (tarjeta 26), y decidir el mapeo de colapso a 3 clases (punto A) — esta corrida deja el insumo de 4 zonas listo para esa decisión, no la toma.
