# Corrida del canal endémico — serie nacional (2026-08-10)

> Resumen de una página de `backend/ingestion/corrida_canal_endemico_nacional.py` (TAREA-02 de la sesión del pivote "Opción C"). Exploratorio: no entrena nada, alimenta la elección de cortes de percentil que sigue abierta en `docs/contexto/02-decisiones-abiertas.md`, punto A. Salida completa (no versionada) en `backend/ingestion/data/interim/canal_endemico_nacional/`.

## Método

Canal endémico sobre `casos_epidemiologicos` (`clasificacion='total'`, fuente `opendengue_v1_3`, nivel nacional), años base **2018, 2019, 2021, 2022, 2023** (2020 excluido, misma ventana que el entrenamiento departamental ya cerrado). Regla de fuga: el año objetivo nunca entra en su propia línea base. Ventana de semanas vecinas **±1** (mínimo aritméticamente viable — ver punto A), sin envolver entre años: la semana 1 pierde la vecina "semana 0" en vez de tomar la última semana del año anterior. Dos esquemas de corte candidatos, ninguno cerrado: **P75/P90** y **P50/P75**.

## Suficiencia

260 celdas (año objetivo × semana) evaluadas. **250 (96,2 %) cumplen el piso de suficiencia** (12 observaciones, ≥3 de 4 años base). Muy por encima del 87,9–92,8 % de celdas en cero que dio la vía departamental (MINSAL) — la serie nacional no tiene huecos de publicación ni ceros estructurales. Las 10 celdas insuficientes son casi todas semana 1 de cada año (pierde una vecina por el borde de ventana).

## Distribución de clases resultante (solo celdas con suficiencia)

| Año | Esquema | Bajo | Medio | Alto |
|---|---|---|---|---|
| 2018 | P75/P90 | 46 | 4 | 0 |
| 2018 | P50/P75 | 34 | 12 | 4 |
| **2019** (pico histórico) | P75/P90 | 9 | 13 | **28** |
| **2019** | P50/P75 | 0 | 9 | **41** |
| 2021 | P75/P90 | 49 | 1 | 0 |
| 2021 | P50/P75 | 47 | 2 | 1 |
| 2022 | P75/P90 | 19 | 9 | 22 |
| 2022 | P50/P75 | 10 | 9 | 31 |
| 2023 | P75/P90 | 50 | 0 | 0 |
| 2023 | P50/P75 | 48 | 2 | 0 |

## Lectura, no decisión

- Ambos esquemas separan correctamente 2019 (pico) y 2022 (segundo pico) del resto — ninguno produce una clase vacía o casi vacía a nivel nacional, a diferencia de lo que se temía para la vía departamental.
- **P75/P90** da una frontera más conservadora: 2019 queda mayoritariamente "alto" (56 %) pero no absoluto, y años bajos (2018, 2021, 2023) casi no tocan "alto".
- **P50/P75** es más agresivo: marca "alto" el 82 % de las semanas de 2019 y hasta 1 semana de 2021 (un año de baja transmisión) — riesgo de sobre-etiquetar como brote lo que es variación normal.
- Ninguna de las dos observaciones decide el corte — eso sigue siendo del coordinador (punto A). Esta corrida solo confirma que, a nivel nacional, hay señal real y suficiencia de datos para que la elección importe.

## Pendiente

Repetir el mismo método sobre la vía departamental una vez resuelto el reconteo de MINSAL (tarjeta 26), para comparar directamente contra estos números antes de decidir si el segundo clasificador se activa.
