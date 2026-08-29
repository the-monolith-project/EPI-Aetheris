# Procedencia de los números del diagnóstico — leer antes de mirar los resultados

Respuesta al pedido de Isaac de los archivos originales del punto 4.

## Qué hay y qué no

Los **cuatro análisis que pediste están en un solo script**, no en cuatro:
`diagnostico_senal_etiqueta_auditable.py`.

| Pedido | Dónde está |
|---|---|
| 1. Umbral / AUC = 0,23 | Sección 3 del script |
| 2. Comparación RF / GB / ET / LogReg | Sección 4 |
| 3. Pool de percentiles no pareado | Sección 5 |
| 4. Preliminar de etiqueta intra-anual (Vía 2) | Sección 6 |

Salidas que pediste, todas generadas:

- **Matrices de confusión** — en el log, secciones 2 y 4, para modelo y línea base.
- **Métricas por clase** (precisión / recall / F1 / soporte) — log, sección 2; completas en el JSON.
- **Probabilidades por fila** — `probabilidades_por_fila.csv`, 100 filas (2019 y 2022), con etiqueta real, predicción y las tres probabilidades.
- **Aciertos absolutos** — al lado de cada recall en todo el log, formato `X de Y`.
- **Semillas** — 42 como referencia; 0 a 9 para la Vía 2, con resultado por semilla en el JSON.
- **Hiperparámetros** — impresos al inicio del log y guardados en el JSON.
- **Comando ejecutado** — impreso al inicio del log.
- **Versiones de dependencias** — impresas al inicio del log. **Ver la advertencia 1.**
- **Todo junto** — `resultados_diagnostico.json`, para hacer diff contra tu re-corrida.

**Lo que NO viene de este script**, para que no lo busques acá:

- El `0 de 55` de la transferencia multipaís sale de `experimento_multipais.py`, que ya está en el repositorio con su propio informe.
- El ONI como predictor nacional y la ventana climática ampliada son experimentos del equipo, con sus informes ya en `docs/`.

---

## Advertencia 1 — las versiones no son las del proyecto

Este diagnóstico corrió con **scikit-learn 1.8.0 y numpy 2.4.4**. El proyecto fija **scikit-learn 1.5.1**. No son la misma versión, y RandomForest puede diferir entre versiones mayores.

**Re-corré el script bajo las versiones fijadas del proyecto antes de citar cualquier número en un informe.** Si algo cambia, gana tu corrida, no ésta.

## Advertencia 2 — hay una discrepancia real, y no es un error de nadie

Los informes que están en `docs/` reportan para 2022 un **F1 macro de 0,169**. Esta réplica da **0,240** para el mismo año.

Lo verifiqué y la causa está identificada: **el dataset cambió de tamaño después de que esos informes se generaran.**

- Los informes de `docs/` se generaron el 15 de agosto contra un dataset de **247 filas**.
- El 16 de agosto se cargó clima de 2014–2017. Eso le dio a 2018 tres semanas más de historia climática para construir rezagos, y el dataset pasó a **250 filas**.
- Esta réplica usa el volcado versionado actual, o sea las 250 filas.

Tres filas más en el conjunto de entrenamiento cambian el bosque y con él el F1 de 2022.

**Lo que no cambia, y es lo que importa:** el recall de la clase alta sigue en **0,000 (0 de 22)** en 2022 y **0,000 (0 de 28)** en 2019, con las dos versiones del dataset. La conclusión no depende de esto. Lo que sí depende es cualquier cifra de F1 que se cite textualmente.

**Consecuencia práctica que hay que resolver:** los informes de `docs/` citan números de un dataset que ya no existe. Si esas cifras entran al documento investigativo tal cual, no son reproducibles por quien clone el repositorio hoy. O se regeneran los informes contra el dataset actual, o se declara explícitamente contra qué versión se generaron. Es decisión de Eduardo cuál de las dos.

## Advertencia 3 — el barrido de umbral es más matizado de lo que se dijo

Se comunicó como "ningún umbral rescata el modelo". Con el barrido completo a la vista, la afirmación precisa es distinta y más útil:

Bajando el umbral **sí se consigue recall no nulo** — en 2022 con t=0,05 llega a 0,500 (11 de 22). Lo que pasa es que el F1 macro se cae por debajo de la línea base al mismo tiempo (0,169 contra 0,184), así que **el criterio sigue sin cumplirse, porque exige superar en las dos métricas a la vez**. Lo mismo en 2019: t=0,05 da recall 0,179 (5 de 28) pero F1 macro 0,086 contra 0,102 de la base.

La razón está en el AUC por debajo de 0,5. Mirá las precisiones:

- 2019, t=0,05: precisión de "alto" = 0,238, con una tasa base de 28/50 = 0,56.
- 2022, t=0,05: precisión de "alto" = 0,324, con una tasa base de 22/50 = 0,44.

En los dos casos **la precisión está por debajo de la tasa base**, es decir que las semanas que el modelo marca como alto tienen *menos* probabilidad de serlo que una semana elegida al azar. Ese es el contenido real del AUC de 0,23: el ordenamiento no es débil, está invertido.

Si querés dejarlo cerrado del todo, la corrida que falta es elegir el umbral por validación *dentro* de los años de entrenamiento y recién después aplicarlo al año de prueba. Yo lo corrí así y el procedimiento interno terminó eligiendo t=0,50 —o sea, ningún cambio— pero esa corrida no está en este script y vale que la rehagas vos.

## Advertencia 4 — sobre las 10 semillas de la Vía 2

Las 10 semillas miden la variabilidad del bosque, **no** la de haber observado estos 5 años y no otros. El `7/10` de 2023 no es un resultado que se sostenga solo. Está impreso en el log al final de la sección 6 para que no se lea de más.

---

## Reproducir

```bash
python3 diagnostico_senal_etiqueta_auditable.py \
    --seed-sql db/seed/seed_datos_reales.sql \
    --salida ./salida_diagnostico
```

No necesita Postgres levantado: lee el volcado versionado directamente. No escribe a la base, no toca artefactos de producción, no modifica ningún script del pipeline.
