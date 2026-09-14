# Segunda confirmación independiente — proto-predictor de nowcast de horizonte corto

> Requisito de la decisión 5 firmada en `experimento-nowcast-corto-plazo.md`: antes de exponer
> cualquier cifra, una reproducción independiente del pipeline debe confirmar (o refutar) el
> resultado positivo de la ventana 2014+.
>
> Este documento se redacta en dos tiempos. La sección **"Método predeclarado"** se escribe y
> commitea **antes de correr nada** (el historial de git es la única prueba de que el método
> precede a la ejecución). Las secciones de resultados y veredicto se añaden después.

## Qué se confirma

Ejecución del 2026-09-09 (commit `3529d69`), fila 2014+: un nowcast probabilístico de la serie
nacional semanal de dengue (OpenDengue `total`, región SV) supera a los baselines de persistencia
RW y climatología estacional en horizontes de 1 a 8 semanas, en los 5 años de prueba
(2019, 2021, 2022, 2023, 2024), recortando el WIS agrupado entre 25 % y 30 %. Con ventana 2016+ el
modelo se rompe en 2019 (un brote sin precedente en el entrenamiento satura el modelo de árboles).

## Método predeclarado (redactado antes de correr)

### Principio

Reimplementación **desde cero** de: la fórmula del WIS, el bucle de forward-chaining, la
construcción de features, el cálculo de baselines y el criterio de veredicto. El script original
(`experimento_nowcast_corto_plazo.py`) se consulta **solo** para dudas de esquema/SQL. La lógica de
scoring y de partición temporal es independiente.

Código nuevo: `backend/ingestion/nowcast_segunda_confirmacion.py`, solo lectura de Postgres,
numpy + psycopg2 + sklearn, sin pandas, sin dependencias nuevas.

### Invariantes (sin excepción, en todos los esquemas)

1. **Forward-chaining con aserción dura.** Para cada origen `t`, todo par de entrenamiento `(X, y)`
   tiene `fecha(objetivo) < fecha(t)` estrictamente. La aserción se verifica contra los índices
   reales que devuelve el generador de pares (no como tautología del filtro).
2. **Control negativo de la aserción.** Se desplaza el corte una semana (se permite
   `fecha(objetivo) == fecha(t)`) y se comprueba que la aserción entonces **sí dispara**. Esto
   demuestra que la comprobación discrimina en el borde, no solo cuando la fuga es masiva.
3. **2020 excluido** como año de origen, como año de objetivo y del pool de la climatología (D1).
   Se retiene únicamente como insumo de rezagos autorregresivos para semanas vecinas.
4. **Dos ventanas de historia:** 2014+ y 2016+, el experimento completo en ambas.
5. **WIS** con el conjunto de 23 cuantiles de los hubs (0.010, 0.025, 0.05, 0.10…0.95, 0.975,
   0.99). Baselines mínimos: persistencia RW y climatología estacional (se añade persistencia
   estacional para paridad con el original).
6. **Objetivo = `log1p(conteo)`**. Nada de etiqueta categórica. Predicción devuelta en escala de
   conteo vía `expm1`, con corrección de cruce de cuantiles por `sort`.
7. **Control de mutación:** con las etiquetas de entrenamiento permutadas (semilla fija), el WIS
   del modelo debe dispararse.
8. **Conteo de fallbacks:** cada vez que el modelo no puede ajustar (pocos pares) o no puede
   construir features y cae a un pronóstico de respaldo, se cuenta y se reporta. Un conteo > 0
   significa que la fila "modelo" contiene baseline y se marca como tal.

### Reimplementación del WIS — prueba unitaria previa

Antes de cualquier corrida se verifica la identidad: para un pronóstico degenerado (los 23
cuantiles iguales a `m`), `WIS(y, m·1) == |y − m|` exacto a coma flotante. Deriva de: término de
mediana `0.5|y−m|`, cada uno de los 11 pares aporta `(alpha/2)(2/alpha)|y−m| = |y−m|`, total
`11.5|y−m|`, normalizado por `K + 1/2 = 11.5`. Si la reimplementación no reproduce esta identidad,
los pesos alpha o la normalización están mal. Prueba secundaria: WIS monótono no creciente al
añadir cobertura correcta; WIS de un intervalo que no cubre crece `2/alpha` por unidad de
distancia.

### Esquemas de validación (los tres se reportan)

| Esquema | Qué hace | Qué claim discrimina |
|---|---|---|
| **A — held-out terminal** | Entrena solo hasta fin de 2022, **sin reajuste**, predice todo 2023–2024 fuera de muestra. | Skill en años de baja transmisión ya vistos. **No** discrimina el titular 2014+, porque 2019 queda en el entrenamiento para ambas ventanas. Se declara explícitamente. |
| **B — rolling origin denso** | Cada semana desde 2019 (fuera de 2020) es un origen; ventana expansiva; reajuste según cadencia del esquema C. Skill por año y agrupado. | **Este es el esquema que toca el titular.** El único año que separa 2014+ de 2016+ es 2019, y B lo evalúa como origen. |
| **C — cadencia de reajuste** | Esquema del original (rolling desde 2019) con reajuste **semanal** y con reajuste **cada 4 semanas**, además del cada-2 original. | Si la cadencia de 2 semanas era load-bearing. |

Además, **corrida de paridad**: configuración idéntica al original (cadencia 2, mismas features del
*script*, h ∈ {1,2,4,8}, ventanas 2014+ y 2016+), comparada fila por fila contra la tabla de
resultados del commit `3529d69`.

### Diagnóstico directo del mecanismo de saturación

Para los orígenes de la semana pico de 2019, se reporta el cuantil 0.99 predicho por el modelo (en
escala log) contra el máximo `z = log1p(conteo)` presente en el conjunto de entrenamiento de ese
origen, por ventana. Hipótesis: bajo 2016+ el q0.99 queda pegado al máximo de entrenamiento (~6.08)
y por debajo del pico real de 2019 (~7.69); bajo 2014+ el q0.99 sube por encima. Esto confirma el
mecanismo de forma directa en vez de inferirlo del número de skill.

### Criterio de éxito (el firmado, sin redefinir)

Sobre h = 4, ventana 2014+: (1) skill relativo agrupado > 0 frente al baseline decisivo;
(2) WIS del modelo ≤ WIS del baseline decisivo en ≥ 4 de los 5 años de prueba;
(3) cobertura del 95 % en [0.85, 0.99] y del 50 % en [0.35, 0.65].

### Condición de parada

Si la corrida de paridad no reproduce la tabla del commit `3529d69` (WIS agrupado con diferencia
> 5 % o cambio de veredicto en cualquier fila), se detiene y se reporta la discrepancia con el
detalle numérico. No se "ajusta" ninguno de los dos lados para que cuadren.

### Veredicto — forma esperada

Uno de: *el resultado 2014+ se sostiene* / *se sostiene con matices* / *no se sostiene*, con el
porqué numérico. Se anota de antemano que, aun con reproducción numérica exacta, el contraste
2014+ vs 2016+ descansa sobre **un solo año (2019) con un solo brote**; el veredicto debe reflejar
ese tamaño de muestra del evento discriminante, además de la pregunta ya abierta sobre 2014–2015
frente a MINSAL.

---

## Resultados (ejecución 2026-09-09, reproducción independiente)

Serie cargada: T = 574 semanas, 2013-12-29 a 2024-12-22, casos máx = 2897 (z = log1p = 7.97). El
máximo de toda la serie cae en 2014–2015 y está **por encima** del pico de 2019 (2178, z = 7.69).

Aserción anti-fuga: verificada en 15–17 orígenes por celda contra los índices reales de objetivo
que devuelve el generador de pares; **control negativo de borde** (relajar el corte un día para
permitir `fecha(objetivo) == fecha(origen)`) hace fallar la aserción en todas las celdas — la
comprobación discrimina en el límite, no solo ante fuga masiva. `n_fallback = 0` en las 26 celdas
(ninguna fila "modelo" contiene baseline encubierto).

### Corrida de paridad — mi WIS vs el original (commit 3529d69)

Configuración idéntica (cadencia 2, features del *script*, comparador = baseline de menor WIS
agrupado). Todos los números son **reproducción independiente**; entre paréntesis, el valor del
commit 3529d69.

| Alcance | h | WIS base | WIS modelo | WIS-log base | WIS-log modelo | Skill medio/año | Años ganados | Veredicto |
|---|---|---|---|---|---|---|---|---|
| 2014+ | 1 | 46.7 (46.7) | 33.7 (33.7) | 0.210 (0.210) | 0.174 (0.174) | +0.31 (+0.31) | 5/5 | cumple |
| 2014+ | 2 | 50.8 (50.8) | 38.3 (38.3) | 0.264 (0.264) | 0.192 (0.192) | +0.31 (+0.31) | 5/5 | cumple |
| 2014+ | 4 | 74.6 (74.6) | 53.1 (53.1) | 0.316 (0.316) | 0.240 (0.240) | +0.33 (+0.33) | 5/5 | cumple |
| 2014+ | 8 | 105.9 (105.9) | 75.1 (75.1) | 0.428 (0.428) | 0.305 (0.305) | +0.37 (+0.37) | 5/5 | cumple |
| 2016+ | 1 | 54.5 (54.5) | 56.4 (56.4) | 0.209 (0.209) | 0.215 (0.215) | +0.24 (+0.24) | 4/5 | parcial |
| 2016+ | 2 | 54.1 (54.1) | 62.9 (62.9) | 0.263 (0.263) | 0.234 (0.234) | +0.17 (+0.17) | 4/5 | parcial |
| 2016+ | 4 | 76.4 (76.4) | 78.1 (78.1) | 0.315 (0.315) | 0.289 (0.289) | +0.23 (+0.23) | 4/5 | parcial |
| 2016+ | 8 | 103.7 (103.7) | 100.2 (100.2) | 0.396 (0.396) | 0.365 (0.365) | +0.23 (+0.23) | 4/5 | cumple |

Skill por año, h = 4 (independiente / commit): 2014+ → +0.28/+0.36/+0.15/+0.39/+0.47, idéntico.
2016+ → **−0.32**/+0.41/+0.14/+0.39/+0.55, idéntico. Cobertura h4: 2014+ 0.42 / 0.94; 2016+
0.38 / 0.88 — ambas iguales al commit. Control de mutación (etiquetas permutadas, semilla 12345):
2014+ h4 WIS 53.1 → **128.8** (colapsa como se esperaba), igual al commit byte a byte.

**El WIS reimplementado coincide con el original en las 8 filas, a la décima, en las cuatro
métricas.** La condición de parada (> 5 % de diferencia o cambio de veredicto) no se activa en
ninguna fila. La prueba unitaria de la identidad degenerada del WIS (`WIS(y, m·1) == |y−m|`) pasó
en 2000 casos aleatorios antes de la corrida.

### Esquema A — held-out terminal (entrena ≤ 2022, sin reajuste, predice 2023–2024)

| Alcance | h | WIS base | WIS modelo | WIS-log base | WIS-log modelo | Skill/año 2023 | 2024 |
|---|---|---|---|---|---|---|---|
| 2014+ | 1 | 26.6 | 16.2 | 0.281 | 0.217 | +0.32 | +0.50 |
| 2014+ | 2 | 29.5 | 17.3 | 0.401 | 0.227 | +0.32 | +0.52 |
| 2014+ | 4 | 36.8 | 21.4 | 0.431 | 0.251 | +0.40 | +0.44 |
| 2014+ | 8 | 43.4 | 26.9 | 0.466 | 0.271 | +0.22 | +0.51 |
| 2016+ | 1 | 29.0 | 15.4 | 0.280 | 0.217 | +0.41 | +0.56 |
| 2016+ | 2 | 30.1 | 16.8 | 0.399 | 0.226 | +0.37 | +0.53 |
| 2016+ | 4 | 36.4 | 20.8 | 0.303 | 0.253 | +0.43 | +0.43 |
| 2016+ | 8 | 36.4 | 26.5 | 0.303 | 0.272 | +0.27 | +0.28 |

El modelo gana a los baselines en **los dos años de prueba, las dos ventanas y los cuatro
horizontes**, recortando el WIS ~40–55 %. El script marca "NO CUMPLE" porque el criterio firmado
exige ≥ 4 de 5 años ganados y A solo tiene 2 años evaluables — es una **inaplicabilidad del
umbral, no un fallo del modelo**. Qué discrimina A: en años dentro del rango entrenado (2023 y 2024
son de baja transmisión), un único entrenamiento fijo sin reajuste ya basta para batir a
persistencia. Qué **no** discrimina A: el titular 2014+, porque 2019 queda en el conjunto de
entrenamiento para ambas ventanas — por eso las dos filas ganan.

### Esquema B — rolling origin denso, cadencia 1 (semanal)

| Alcance | h | WIS base | WIS modelo | Skill/año 2019 | 2021 | 2022 | 2023 | 2024 | Gana WIS agrupado | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|
| 2014+ | 1 | 46.7 | 33.8 | +0.26 | +0.21 | +0.17 | +0.35 | +0.54 | sí | cumple |
| 2014+ | 2 | 50.8 | 37.7 | +0.18 | +0.27 | +0.23 | +0.36 | +0.54 | sí | cumple |
| 2014+ | 4 | 74.6 | 53.2 | +0.28 | +0.36 | +0.16 | +0.39 | +0.47 | sí | cumple |
| 2014+ | 8 | 105.9 | 74.8 | +0.22 | +0.53 | +0.25 | +0.27 | +0.59 | sí | cumple |
| 2016+ | 1 | 54.5 | 54.6 | **−0.29** | +0.41 | +0.12 | +0.42 | +0.60 | no | parcial |
| 2016+ | 2 | 54.1 | 61.2 | **−0.56** | +0.41 | +0.08 | +0.40 | +0.60 | no | parcial |
| 2016+ | 4 | 76.4 | 76.8 | **−0.30** | +0.40 | +0.16 | +0.39 | +0.56 | no | parcial |
| 2016+ | 8 | 103.7 | 99.8 | **−0.21** | +0.25 | +0.22 | +0.33 | +0.59 | sí | cumple |

Rolling origin semanal reproduce la corrida de paridad casi exactamente (2014+ h4: 53.2 vs 53.1).
El corte entre 2014+ (cumple) y 2016+ (2019 se rompe, skill −0.30 en h4) **no es un artefacto de
la cadencia de reajuste**.

### Esquema C — sensibilidad a la cadencia de reajuste (h = 4)

| Alcance | cadencia | WIS modelo | WIS-log modelo | Skill medio/año | 2019 | Veredicto |
|---|---|---|---|---|---|---|
| 2014+ | 1 sem (B) | 53.2 | 0.240 | +0.332 | +0.28 | cumple |
| 2014+ | 2 sem (paridad) | 53.1 | 0.240 | +0.330 | +0.28 | cumple |
| 2014+ | 4 sem | 53.7 | 0.242 | +0.321 | +0.27 | cumple |
| 2016+ | 1 sem (B) | 76.8 | 0.286 | +0.243 | −0.30 | parcial |
| 2016+ | 2 sem (paridad) | 78.1 | 0.289 | +0.234 | −0.32 | parcial |
| 2016+ | 4 sem | 80.6 | 0.295 | +0.216 | −0.38 | parcial |

Pasar de reajuste semanal a mensual mueve el WIS agrupado **< 3 %** y no cambia ningún veredicto.
**La cadencia de 2 semanas del original no era load-bearing.**

### Diagnóstico directo de la saturación en 2019 (h = 4, 52 orígenes con objetivo en 2019)

| Ventana | máx z de entrenamiento | q0.99 predicho (log), rango | z real del objetivo, rango |
|---|---|---|---|
| 2014+ | **7.97** (contiene el pico de 2014–2015) | 7.06 – 7.74 | 4.57 – 7.69 |
| 2016+ | **6.08** (solo 2016/2017/2018) | 5.53 – 7.68 | 4.57 – 7.69 |

Confirma el mecanismo con un **matiz sobre la explicación del doc original**: bajo 2016+ el modelo
de árboles por cuantiles **sí extrapola algo** por encima del máximo de entrenamiento (q0.99 llega
a 7.68, no queda topado en 6.08 — el boosting aditivo estira la cola), pero la mediana y el grueso
de la distribución sí saturan, y en escala natural el WIS explota (skill −0.30). Bajo 2014+ el
entrenamiento contiene un precedente real por encima del pico de 2019 (7.97 > 7.69), q0.99 lo
alcanza y el año se predice bien. La afirmación del doc de que "las hojas son cuantiles dentro de
muestra" es correcta como límite del árbol individual; la suma boosted la relaja parcialmente. La
conclusión operativa del doc no cambia: sin precedente comparable en el entrenamiento, el nowcast
subestima un brote de magnitud nueva.

### Divergencia doc / código (hallazgo del encargo — "detalles de features")

El texto de `experimento-nowcast-corto-plazo.md` (§6) describe armónicos
`sin/cos(2πk·semana/52)` y rezagos "`t, t−1, …, t−8`" (9 rezagos). El *script* que produjo la
tabla usa `2πk·doy/365.25`, `N_LAGS = 8` (rezagos `t … t−7`) y una feature `momentum = z[t] − z[t−4]`
que el doc no menciona. Para la paridad reimplementé lo que hace el **script**. Quien reprodujera
el pipeline solo desde la prosa del doc **no** obtendría la tabla. Es una diferencia menor en el
resultado (los tres esquemas confirman el patrón), pero conviene alinear el doc con el código.

## Veredicto

**El resultado 2014+ se sostiene — con matices.**

**Qué se sostiene (sin ambigüedad):**

1. La tabla del commit 3529d69 se reproduce **exacta** con una reimplementación independiente del
   WIS, del forward-chaining y de los baselines (8/8 filas, 4 métricas, a la décima). No hay error
   en la fórmula del WIS ni en la partición temporal.
2. El positivo de 2014+ es **robusto a la cadencia de reajuste** (1/2/4 semanas: < 3 % de cambio) y
   a un **held-out terminal completo** (esquema A: el modelo recorta el WIS 40–55 % en 2023–2024
   fuera de muestra, sin reajuste, en las dos ventanas).
3. El corte 2014+ (cumple) vs 2016+ (2019 se rompe) **no es un artefacto de partición ni de
   cadencia**: aparece igual en rolling origin semanal (B) y en el diagnóstico directo de
   saturación.

**Los matices (por qué no es "se sostiene" a secas):**

1. **El evento que discrimina es n = 1.** Todo el contraste "2014+ rescata / 2016+ falla" descansa
   en **un solo año (2019) con un solo brote grande**. En los otros cuatro años de prueba (baja
   transmisión, dentro del rango visto) ambas ventanas ganan. La conclusión sobre robustez ante
   brotes sin precedente tiene soporte empírico de un caso.
2. **La paridad es un chequeo de bugs, no una corroboración del modelado.** Mi reimplementación
   siguió el *script* original; que los números coincidan prueba que el WIS y el forward-chaining
   están bien, no que la elección de features/modelo sea la correcta. Las piezas de evidencia
   genuinamente independientes son el esquema A, el barrido de cadencia y el diagnóstico de
   saturación — y los tres apuntan en la misma dirección que el doc.
3. **El titular sigue dependiendo de 2014–2015.** Si esos dos años (≈ 2× el nivel de 2016+, y su
   pico es lo que da el precedente z = 7.97) fueran un cambio de definición de caso y no
   transmisión real, la fila honesta es la 2016+ (parcial). El loader solo se verificó contra
   MINSAL para 2018 y 2022. Este punto ya estaba en el doc original y esta confirmación no lo
   resuelve.
4. **Intervalos estrechos.** Cobertura al 50 % en ~0.38–0.43 a h4 (nominal 0.50), 2016+ h4 al 95 %
   en 0.88 (borde de la banda firmada). Dentro del criterio, pero en el límite inferior; la
   calibración pendiente (decisión 5, punto 3) es real.

**Recomendación:** el resultado es suficientemente sólido como línea de investigación interna y la
segunda confirmación no encontró ninguna grieta en el pipeline. Antes de exponer cualquier cifra
siguen pendientes, sin cambios respecto al doc: (a) verificar 2014–2015 contra MINSAL/OPS —
determina cuál fila es el titular; (b) ensanchar los intervalos; (c) formalizar la regla de
"precedente comparable en el entrenamiento". El matiz nuevo que aporta esta confirmación es que la
evidencia sobre la fragilidad ante brotes sin precedente es de **un único año**, y convendría
buscar una segunda ventana o serie donde probar ese mecanismo antes de tratarlo como establecido.

## Trazabilidad

- Rama: `experimento/nowcast-segunda-confirmacion` (a partir de `3529d69`).
- Código: `backend/ingestion/nowcast_segunda_confirmacion.py` (solo lectura de Postgres,
  numpy + sklearn + psycopg2, sin pandas, sin dependencias nuevas).
- Salida cruda (gitignored): `backend/ingestion/data/interim/nowcast_confirmacion/*.json`.
- Comandos:
  ```bash
  cd backend/ingestion
  POSTGRES_HOST=localhost ../.venv/bin/python nowcast_segunda_confirmacion.py --wis-test
  POSTGRES_HOST=localhost ../.venv/bin/python nowcast_segunda_confirmacion.py --paridad
  POSTGRES_HOST=localhost ../.venv/bin/python nowcast_segunda_confirmacion.py --esquema-a
  POSTGRES_HOST=localhost ../.venv/bin/python nowcast_segunda_confirmacion.py --esquema-b
  POSTGRES_HOST=localhost ../.venv/bin/python nowcast_segunda_confirmacion.py --esquema-c --cadencias 4
  ```

