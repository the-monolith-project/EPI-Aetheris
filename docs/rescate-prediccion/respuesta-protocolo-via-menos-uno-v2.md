# Respuesta del coordinador al protocolo de evaluación — Vía −1

**Versión:** 2. Sustituye la respuesta anterior, redactada sin disponer de la definición completa.
**Responde a:** `protocolo-evaluacion-rescate-prediccion.md` v2, definición completa, 2026-08-18.
**Estado:** respuesta emitida. Pendiente de firma en la sección 10.

---

## 1. Confirmación de recepción

Se confirma por escrito la recepción de la definición completa de la Vía −1, según exige su sección 16. La definición se leyó íntegra antes de emitir esta respuesta, incluidas las secciones 5, 7 y 13.

La definición es correcta y mejora el diseño anterior. Identifica dos contaminaciones reales que la respuesta v1 no había considerado: que el año externo participe en los percentiles que etiquetan filas de entrenamiento, y que un año antiguo se evalúe entrenando con años posteriores. La construcción de historia expansiva `H(y)` y la regla de que la etiqueta de un año sea idéntica en todos los folds que la reutilizan son ambas correctas y se adoptan sin objeción.

---

## 2. D1 — Papel de 2020

**Sin cambios respecto de la v1. Se firma.** 2020 queda excluido tanto como año objetivo como del pool histórico, y la exclusión aplica a cualquier país y cualquier vía, no solo a la Vía −1 nacional.

Nota de alcance que se mantiene: las corridas regionales multipaís ya ejecutadas incluyeron 2020 en el pool y como año de prueba. Esas tablas quedan con nota al pie declarándolo. Si esas vías se retoman, se rehacen sin él.

---

## 3. D2 — Años externos, corregida

### 3.1 — Se acepta la corrección sobre 2016

**2016 se retira del protocolo prospectivo.** La objeción del protocolo es correcta y la recomendación anterior del coordinador era errónea.

Las 6 semanas `alto` reportadas en la v1 se obtuvieron etiquetando 2016 contra el pool fijo de producción, formado por años posteriores a 2016. Eso es exactamente la contaminación que la Vía −1 elimina. La cifra se conserva como análisis retrospectivo, claramente etiquetada como tal, y no vuelve a citarse como soporte prospectivo.

Se confirma además que `H(2016) = {2014, 2015}` no alcanza los pisos: dos años históricos con ventana ±1 dan como máximo 6 observaciones, contra un piso de 12 observaciones y 3 años. Verificado sobre la fuente canónica: 2016 y 2017 quedan con las 52 celdas sin etiqueta. El rechazo es correcto.

### 3.2 — 2024 se mantiene como año externo reservado

Se reproduce la tabla con la fuente canónica (`db/seed/seed_datos_reales.sql`) y con la construcción prospectiva `H(t)`, como exigía la sección 15:

| Año | `H(y)` | Celdas sin etiqueta | Distribución |
|---|---|---|---|
| 2016 | 2014–2015 | 52 | ninguna celda etiquetable |
| 2017 | 2014–2016 | 52 | ninguna celda etiquetable |
| 2018 | 2014–2017 | 2 | 50 bajo |
| 2019 | 2014–2018 | 2 | 48 bajo, 2 medio |
| 2021 | 2014–2019 | 0 | 52 bajo |
| 2022 | 2014–2021 | 0 | 36 bajo, 11 medio, **5 alto** |
| 2023 | 2014–2022 | 0 | 52 bajo |
| 2024 | 2014–2023 | 0 | 52 bajo |

Las dos celdas sin etiqueta de 2018 y 2019 son las semanas de borde, donde la ventana ±1 no cruza el año y el pool no alcanza el piso. Es el comportamiento esperado de la regla, no un defecto.

**Confirmado: 2024 no contiene ninguna semana `alto` bajo la construcción prospectiva.** Se mantiene como año externo reservado, y se declara desde ahora, antes de ejecutar, que ahí el recall de `alto` será `N/A` y que la evaluación solo podrá hablar de F1 macro, precisión, clases `bajo`/`medio` y falsos positivos de `alto`.

### 3.3 — Se declara que no existe test final intacto y evaluable

Los folds 2019 a 2023 no son tests intactos: sus resultados ya influyeron en el diagnóstico del proyecto. 2024 es intacto pero no evaluable para recall. **No existe ningún año que sea simultáneamente intacto y evaluable en la clase decisiva.** Todo resultado de la Vía −1 se reporta como validación forward-chaining exploratoria, nunca como desempeño final independiente.

---

## 4. D3 — Criterio ampliado

**Sin cambios respecto de la v1. Se firma.**

Las cuatro referencias son obligatorias de reportar. Solo la climatológica sigue siendo decisiva. Se agrega el veto: un resultado no puede contarse como éxito si cualquiera de los dos predictores constantes supera al modelo en F1 macro.

El veto existe porque el caso que describe ya ocurrió: en la corrida regional multipaís, 2024 quedó marcado como "SUPERA" con F1 macro 0,139, cuando un predictor que dijera `alto` siempre habría obtenido 0,262 y recall 1,000 en ese mismo año.

Se confirma la lectura del protocolo en su sección 10: persistencia y las constantes se reportan pero no se convierten en umbrales adicionales.

---

## 5. D4 — Tratamiento del umbral

**Sin cambios respecto de la v1. Se firma.** Argmax fijo. No se barren umbrales sobre la etiqueta actual.

Fundamento: se probó selección de umbral por validación interna y el procedimiento eligió 0,50, es decir ningún cambio; y el AUC de la probabilidad de `alto` frente al `alto` real es 0,234 en 2019 y 0,231 en 2022, por debajo de 0,5. El ordenamiento está invertido y ningún umbral rescata eso.

Cualquier reapertura futura requiere anexo por vía, con AUC en folds internos superior a 0,5 como condición de entrada, lista de candidatos congelada antes de correr, selección solo en folds internos y una única evaluación del externo.

---

## 6. Corrección de hecho al protocolo

La sección 4 del protocolo afirma que la cobertura climática de la foto actual es 2018–2024, y su sección 7 usa esa afirmación como segundo motivo para rechazar 2016. **La afirmación es incorrecta.**

Verificación sobre `db/seed/seed_datos_reales.sql`, excluyendo `oni_anom`:

| Año | Filas de clima | Variables distintas |
|---|---|---|
| 2014 | 5.194 | 7 |
| 2015–2019 | 5.096 cada uno | 7 |
| 2020 | 5.194 | 7 |
| 2021–2024 | 5.096 cada uno | 7 |

Existe cobertura climática completa desde 2014, incluido 2016. **El rechazo de 2016 sigue siendo correcto**, pero se sostiene únicamente sobre el primer motivo: `H(2016)` no alcanza los pisos de suficiencia. Corregir el segundo motivo en el protocolo antes de aprobarlo, para que ninguna decisión posterior se apoye en un dato falso.

---

## 7. Declaración previa de estados de fold

Esta sección se registra **antes de ejecutar cualquier corrida** y es la parte más importante de esta respuesta. Los estados de abajo se derivan de la construcción del protocolo aplicada a la fuente canónica, no de una corrida del modelo.

| Externo | Entrenamiento | Clases en entrenamiento | `alto` real en el externo | Estado declarado |
|---|---|---|---|---|
| 2019 | 2018 | 50 bajo | 0 | `no_entrenable` — una sola clase |
| 2021 | 2018, 2019 | 98 bajo, 2 medio | 0 | `entrenable_con_clase_ausente` + `recall_alto_no_evaluable` |
| 2022 | 2018, 2019, 2021 | 150 bajo, 2 medio | 5 | `entrenable_con_clase_ausente` — **cero ejemplos de `alto` en entrenamiento** |
| 2023 | 2018, 2019, 2021, 2022 | 186 bajo, 13 medio, 5 alto | 0 | `entrenable` + `recall_alto_no_evaluable` |
| 2024 | 2018, 2019, 2021, 2022, 2023 | 238 bajo, 13 medio, 5 alto | 0 | `entrenable` + `recall_alto_no_evaluable` |

**Consecuencia estructural, declarada por adelantado:** el único fold cuyo año externo contiene semanas `alto` es 2022, y en ese fold el entrenamiento no contiene ni un solo ejemplo de esa clase. Los dos folds que sí tienen `alto` en entrenamiento —2023 y 2024— tienen cero `alto` en el externo.

Por lo tanto **ningún fold de la Vía −1 puede confirmar ni refutar la parte del criterio basada en recall de `alto`**. No por desempeño del modelo, sino por la estructura de los datos bajo una construcción sin fuga.

Esto no invalida la Vía −1: la valida. Su sección 10 ya establece que la vía queda validada cuando demuestra reproducibilidad e independencia temporal, aunque el modelo falle. El resultado esperado es precisamente ese, y se declara ahora para que al ejecutarse no se lea como un fracaso del modelo sino como lo que es: la demostración de que la evidencia prospectiva no es alcanzable con estos datos y esta etiqueta.

**El corpus prospectivo completo contiene 5 semanas `alto` sobre 308 celdas etiquetadas.**

---

## 8. Sobre ampliar la ventana histórica

Se evaluó si ampliar o modificar la historia rescata la estructura de folds, siguiendo el criterio de la literatura de que más años de entrenamiento mejoran el desempeño. **No lo rescata.** Se probaron tres construcciones sobre la fuente canónica:

| Construcción | Semanas `alto` en todo el corpus | Folds con `alto` en entrenamiento y en el externo |
|---|---|---|
| A — expansiva, la del protocolo | 5 | **0 de 5** |
| B — ventana móvil de los 5 años más recientes | 18 | **0 de 5** |
| C — expansiva excluyendo años epidémicos del pool | 29 | **0 de 5** |

En las tres, las semanas `alto` se concentran en un solo año (2022). Cambiar la regla de historia mueve cuántas hay, no dónde están. La estructura del problema no depende de la construcción elegida, así que **no se propone modificar `H(y)`**: la expansiva del protocolo se conserva.

Sobre el argumento de "más años": la referencia de la literatura observa que el desempeño predictivo se estabiliza alrededor de los 12 años de entrenamiento. Dos precisiones que impiden aplicarlo aquí:

1. **Ese umbral es inalcanzable con esta fuente.** La serie semanal nacional de OpenDengue para El Salvador comienza en 2014 (más una fila de borde en 2013). Antes de eso solo existe resolución anual a nivel nacional y mensual a nivel departamental para 2000–2009. El máximo posible son 11 años semanales, de los cuales 6 son etiquetables prospectivamente. No hay forma de llegar a 12 sin cambiar de fuente o de resolución.
2. **Ese estudio concluyó que el clima no mejoró significativamente a un modelo estacional autorregresivo, con 28 años y 18 series.** Más años estabilizan la *estimación*, no convierten en útil un predictor que no lo es. Ampliar la ventana no era el camino a un modelo que funcione.

---

## 9. Estatutos que estas respuestas modifican

No entran en vigor hasta quedar registradas.

| Decisión | Qué cambia | Dónde se registra |
|---|---|---|
| D1, ampliación de alcance | La exclusión de 2020 aplica a todo país y toda vía, no solo a la ventana nacional | `docs/contexto/01-decisiones-cerradas.md` + `CHANGELOG.md` |
| D3, veto de constantes | Se agrega un veto que puede invalidar un resultado que sí supera la línea base decisiva | `docs/contexto/01-decisiones-cerradas.md` + `CHANGELOG.md` |

D2 y D4 no modifican estatutos: D2 registra una limitación de los datos y D4 confirma el comportamiento vigente de producción. Ambas van al historial igual, junto con la declaración previa de estados de fold de la sección 7, para que ninguna sesión futura las reabra como ideas nuevas.

---

## 10. Registro de aprobación

Reemplaza la sección 17 del protocolo, que debe actualizarse en sincronía. Los elementos están separados por responsable para que no se confunda una firma con una tarea pendiente.

### 10.1 — Firma del coordinador (Eduardo). Son estas cinco y ninguna más

| # | Qué se firma | Estado |
|---|---|---|
| 1 | **D1** — 2020 excluido como año objetivo y del pool histórico, en todo país y toda vía | firmado |
| 2 | **D2** — 2016 retirado del protocolo prospectivo; 2024 como externo reservado con recall de `alto` en `N/A`; se declara que no existe test intacto y evaluable a la vez | firmado |
| 3 | **D3** — cuatro referencias obligatorias de reportar, solo la climatológica decisiva, más el veto de predictores constantes | firmado |
| 4 | **D4** — argmax fijo, sin barrido de umbrales; reapertura solo por anexo por vía | firmado |
| 5 | **Declaración previa de estados de fold** de la sección 7, congelada antes de ejecutar | firmado |

Al firmar la 2 y la 5 quedan congelados por escrito los años externos, que el protocolo exige por separado en su sección 16. No hace falta una firma adicional para eso.

### 10.2 — Acciones del coordinador después de firmar

| Qué | Estado |
|---|---|
| Registrar D1 y D3 en `docs/contexto/01-decisiones-cerradas.md` y en `CHANGELOG.md`, por modificar estatutos cerrados (ver sección 9) | pendiente |
| Registrar en el historial D2, D4 y la declaración de la sección 7, aunque no modifiquen estatutos, para que ninguna sesión futura las reabra | pendiente |

### 10.3 — Acciones a cargo del autor del protocolo. El coordinador no firma nada de esto

| Qué | Estado |
|---|---|
| Corregir el dato de cobertura climática: la sección 4 del protocolo dice 2018–2024, la cobertura real es 2014–2024 (detalle y verificación en la sección 6 de este documento) | pendiente |
| Retirar el segundo motivo de rechazo de 2016 en la sección 7 del protocolo, que se apoya en ese dato incorrecto. El rechazo se mantiene por el primer motivo, que sí es válido | pendiente |
| Actualizar la sección 17 del protocolo para que refleje este registro | pendiente |

Las tareas de implementación que el protocolo exige antes de correr —script separado de producción, pruebas de independencia, manifiesto congelado— no son firmas ni figuran aquí. Están en la sección 11.

### 10.4 — Ya cumplido en este documento

| Qué | Estado |
|---|---|
| Confirmación por escrito de recepción de la definición completa (sección 16 del protocolo) | hecho, sección 1 |
| Reproducción de la tabla de D2 con la fuente canónica y `H(t)` | hecho, sección 3.2 |

### 10.5 — Cierre

- **Aprobado por:** Eduardo Rivas 
- **Fecha de aprobación:** 18-08-2026 a las 8:23 GMT-6

---

## 11. Puerta para comenzar las Vías 0–3

Se adopta íntegra la sección 16 del protocolo, con dos adiciones:

- [ ] Corrección del dato de cobertura climática aplicada al protocolo, sección 6 — **autor del protocolo**.
- [x] Declaración previa de estados de fold firmada y congelada antes de ejecutar, sección 7 — **coordinador**.

Advertencia para quien planifique las Vías 0–3 después de esto: **cualquier vía que conserve la etiqueta de canal endémico choca con la misma pared estructural** descrita en la sección 7, porque el problema está en la etiqueta y no en el modelo. La Vía 2 cambia la etiqueta, pero una etiqueta relativa al propio año usa semanas futuras de ese mismo año y por lo tanto tampoco sobrevive a un estándar prospectivo estricto sin una redefinición previa. Esto debe resolverse antes de comprometer tiempo en esas vías, no durante.
