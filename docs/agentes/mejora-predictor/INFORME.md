# Búsqueda de mejoras al predictor de dengue: informe (2026-10-02)

Rama `feat/mejora-predictor-agente`. Tres experimentos con protocolo escrito y commiteado antes
de correr, scripts reproducibles y resultados versionados. Cada cifra de este informe sale de
uno de estos archivos, todos en `docs/agentes/mejora-predictor/resultados-nuevos/`:

| Experimento | Protocolo y resultados | Script | Resultados |
|---|---|---|---|
| Insumos de M0 (clima, ONI, año, ceros) | `docs/experimentos/experimento-nowcast-insumos.md` | `backend/ingestion/experimento_nowcast_insumos.py` | `insumos.json` |
| Calibración de rangos y ajustes de corto plazo | `docs/experimentos/experimento-nowcast-rangos.md` | `backend/ingestion/experimento_nowcast_rangos.py` | `rangos.json` |
| Brotes sin precedente y una familia lineal | `docs/experimentos/experimento-nowcast-recorte.md` | `backend/ingestion/experimento_nowcast_recorte.py` | `recorte.json` |

Piezas compartidas en `backend/ingestion/experimento_nowcast_comun.py`, con 20 pruebas sin base
de datos en `backend/ingestion/tests/test_experimento_nowcast_comun.py`.

## Qué mejora hay

No hay una mejora lista para reemplazar el modelo publicado. Hay un candidato acotado y dos
indicios que merecen su propia firma:

1. **Calibrar M0 con 104 pares en vez de 52 (capa R2).** En la validación de OpenDengue (2019 y
   2021-2024) es la única capa de calibración que pasa el criterio fijado. Su efecto se
   concentra en 2022, el año que la calibración actual cubre peor.

   | h | cobertura 95 % (52 → 104 pares) | cobertura 50 % | WIS |
   |---|---|---|---|
   | 4 | 0,88 → 0,91 | 0,55 → 0,54 | 56,6 → 54,9 |
   | 8 | 0,88 → 0,91 | 0,57 → 0,56 | 78,8 → 80,9 |

   En la serie del tablero no corrige el problema que motivó la pregunta: la cobertura del
   95 % de C en 2026 pasa de 0,79 a 0,76 a 4 semanas y de 0,79 a 0,72 a 8. Sirve para el
   tramo de OpenDengue, no para C.
2. **El peso 0,5 de M0 en C es alto a 1 y 2 semanas.** En 2025-2026 la tendencia amortiguada
   sola tiene WIS 4,7 a 1 semana, contra 6,0 de C y 5,7 de la persistencia suavizada. El peso
   elegido por desempeño reciente (C1) mejora C a 1 y 2 semanas y la empeora a 4 y 8; no pasa
   su criterio. Un peso fijo por horizonte es una hipótesis para otra firma, con semanas
   posteriores a ella, porque 2025-2026 ya sirvieron para elegir C.
3. **Quitar el ONI no empeora nada medible.** Ver la sección siguiente.

## Qué se descartó y por qué

| Línea | Resultado | Cifra decisiva |
|---|---|---|
| Ablación de clima (I2), ONI (I1), clima y ONI (I3), año (I4) | Sin efecto medible con el umbral fijado (±0,03 de skill contra M0 a 4 y 8 semanas, en 4 de 5 años) | Skill contra M0 a h = 4 y h = 8: I1 +0,02 y +0,03; I2 −0,02 y −0,04; I3 −0,01 y −0,05; I4 −0,02 y −0,04. Ninguno con 4 de 5 años en el mismo sentido en los dos horizontes |
| Ceros de vacaciones repartidos como insumo (I5) | No pasa la validación | WIS 57,3 contra 56,6 de M0 a h = 4; 3 de 5 años ganados |
| CQR-r asimétrica (R1) | No pasa: estrecha los rangos | Cobertura del 95 %: 0,77 a h = 4 |
| Conformal adaptativo (R3) | No pasa: cuesta 8 % a 13 % de WIS | WIS 63,7 contra 56,6 a h = 4 |
| Calibrar la mezcla C (R4) | No cumple en el tablero | Cobertura del 95 %: 0,69 a h = 4 |
| Corrección del sesgo reciente (S1) | Empeora en las dos series | Skill contra M0: −0,14 a h = 1, −0,44 a h = 4 |
| Peso de la mezcla por desempeño reciente (C1) | No cumple: gana a 1-2 semanas, pierde a 4-8 | WIS 4,8 contra 6,0 a h = 1; 31,1 contra 28,6 a h = 8 |
| Regresión cuantílica lineal (L0) como familia que extrapola | No pasa la validación normal; 0 de 5 años ganados a h = 4 | Skill medio por año contra la persistencia limpia −0,37 a h = 4 |

Ideas de la revisión bibliográfica descartadas sin correr, por falta de datos o de condiciones:
modelos de retraso de notificación (MINSAL no publica fechas de notificación ni versiones
sucesivas), serotipos, entomología, movilidad y búsquedas web (no existen series públicas con
licencia clara en el proyecto), modelos espacio-temporales (la serie departamental termina en
2023), y redes neuronales (574 semanas de OpenDengue y 89 del tablero, y exigirían una
dependencia nueva). Esto último es una línea no abierta, no un resultado negativo.

Ninguna cifra de la revisión se verificó: el proxy de red de este entorno bloquea pnas.org,
pmc.ncbi.nlm.nih.gov, medrxiv.org y plos.org. Ninguna se usa como dato. La revisión mezcla
métricas no comparables (SUCRA, R², sensibilidad y valor predictivo de alertas municipales,
CRPS de un ejercicio estatal) y contextos distintos del de este proyecto.

## Afirmaciones del sitio frente a lo medido

| Afirmación o pregunta | Lo medido | Estado |
|---|---|---|
| "Ante un brote sin precedente en la serie, la predicción puede quedarse corta" | Sin un año de magnitud comparable en la historia, M0 queda detrás de la persistencia en 2019 (skill −0,80 a h = 4 y −0,28 a h = 8) y en 2022 (−1,02 y −0,33). En el pico, su mediana vale el 12 % (2019) y el 41 % (2022) de lo observado. Con la historia completa, 57 % y 91 %. En 2024, que sí tiene precedente, el recorte no cambia el resultado (+0,01 y +0,28) | Confirmada, con dos años de soporte en vez de uno |
| El modelo usa clima y ONI | Cierto; su aporte no es medible con el umbral fijado. El clima ayuda en 2022 (sin clima, skill −0,47 contra −0,15 a h = 4) y estorba en 2024 (+0,26 contra +0,03) | Se puede decir que se usan; no que mejoran la predicción |
| La ventaja a 5-8 semanas se midió en 2019-2024 | Reproducida sin diferencia: skill medio contra la persistencia limpia +0,12 a +0,18, 4 de 5 años | Confirmada |
| Los rangos tienen la probabilidad nominal (glosario) | Validación: 0,55 al 50 % y 0,88 al 95 % a 4 semanas. Tablero 2026: 0,79 al 95 %. Ninguna de las cinco capas probadas lleva 2026 a 0,85 | Sigue por debajo del nominal; limitación medida |
| A 1-3 semanas M0 rinde como la persistencia limpia | Reproducido: skill agrupado −0,01, +0,06 y +0,05 | Confirmada |

## Reproducción y límites del entorno

- Postgres 16 local (sin Docker en el entorno), migraciones `0001` a `0013`,
  `seed_datos_reales.sql` y `seed_tablero_minsal.sql` (356 filas del tablero, verificadas con
  la consulta del paquete de instrucciones). Los scripts se corren desde `backend/ingestion/`
  con `POSTGRES_HOST=localhost`; tardaron 2 h 08 min, 46 min y 24 min con 4 procesos de un
  hilo. Cada uno tiene un modo `--humo` (pocos orígenes, sin escribir resultados versionados)
  que se usó para probar el código antes de las corridas completas; ningún parámetro, umbral
  ni candidato se cambió después de esas pruebas, y las enmiendas de implementación están
  fechadas en cada protocolo.
- Los tres scripts reproducen con diferencia 0 las 2.044 predicciones de M0 de
  `mejora_validacion.json`, y C reproduce las 416 de 2024 de `tendencia_verificacion.json`.
- En 2025-2026 las predicciones difieren de las publicadas desde el origen 2025-01-05 (mediana
  hasta 9 % distinta en el peor caso, entre 0,6 % y 1,4 % en promedio). La semilla no trae ONI
  de 2025-2026 y este entorno no alcanza al servidor de NOAA para cargarlo. Las comparaciones
  entre variantes dentro de ese tramo usan los mismos datos; las cifras absolutas de 2025-2026
  no son las del artefacto servido.
- No se usó ninguna semana objetivo desde 2026-S38. El script de la prueba prospectiva
  congelada (`experimento_nowcast_tendencia.py`) no se modificó. No se tocaron la API, el
  frontend, los artefactos de `backend/api/datos/` ni el esquema.
- Las pruebas del repositorio pasan: 382 aprobadas y 18 saltadas.

## Decisiones para la persona dueña del proyecto

1. Si se firma un experimento para N_CAL = 104 en la base de M0 (tramo de OpenDengue), con
   semanas no vistas. La validación de esta rama lo apoya; no hay forma de confirmarlo con
   OpenDengue, que termina en 2024.
2. Si se retira el ONI de M0. No empeora nada medible y simplifica la carga de datos, pero
   cambiar el modelo publicado requiere su propia firma.
3. Si se firma un experimento de peso por horizonte en C (por ejemplo, menos peso de M0 a 1 y
   2 semanas), evaluado solo con semanas posteriores a la firma.
4. Si la Biblioteca incorpora la cifra de saturación ante brotes sin precedente (12 % y 41 %
   de lo observado en el pico) junto a la salvedad que ya tiene.
5. Si se carga el ONI de 2025-2026 en la semilla, para que el tramo del tablero sea
   reproducible desde un clon limpio.

## Pendiente, en el orden en que lo haría

1. Repetir la fase B de los experimentos con ONI de 2025-2026 cargado, para cerrar la
   diferencia con el artefacto servido.
2. Una evaluación de la cobertura de 2026 centrada en la posición de la mediana en el cambio
   de año (semanas 1 a 3) y en las semanas 19 a 22, que es donde fallan los rangos; ninguna
   capa de ancho lo corrige.
3. Una comparación con modelos externos, si se encuentran predicciones públicas para El
   Salvador sobre el mismo objetivo, horizonte y periodo. No se hizo ninguna aquí.
