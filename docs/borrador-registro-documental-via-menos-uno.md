# Borrador de registro documental — Vía −1

**Fecha de preparación:** 2026-08-18

**Destinatario:** Eduardo Rivas

**Estado:** borrador operativo; no constituye por sí mismo un registro oficial

## Propósito

Este documento reúne el texto necesario para cerrar el registro documental de la Vía −1 sin tener
que reconstruir las decisiones, sus alcances ni la evidencia técnica. Eduardo debe revisar y copiar
los bloques indicados en las fuentes de autoridad correspondientes.

Las fuentes que respaldan este borrador son:

- `docs/respuesta-protocolo-via-menos-uno-v2.md`, especialmente las secciones 2–5, 7, 9 y 10.5;
- `docs/protocolo-evaluacion-rescate-prediccion.md`, especialmente las secciones 15–17;
- `docs/corrida-via-menos-uno.md`, que contiene la validación reproducible;
- `backend/ingestion/via_menos_uno_manifesto_congelado.json`, que fija la configuración ejecutada.

## Registro requerido

| Acción | Archivo de destino | Forma de registro |
|---|---|---|
| Registrar D1 | `docs/contexto/01-decisiones-cerradas.md` | Agregar la ampliación de alcance en «Ventana de entrenamiento del modelo» |
| Registrar D3 | `docs/contexto/01-decisiones-cerradas.md` | Agregar la ampliación en «Criterio de éxito, línea base y margen de error» |
| Registrar D1–D4 y los estados de fold | `docs/contexto/CHANGELOG.md` | Agregar una entrada nueva al final; no editar entradas anteriores |
| Cerrar la puerta documental | `docs/protocolo-evaluacion-rescate-prediccion.md` | Actualizar únicamente después de completar los dos registros anteriores |

No hace falta crear un ADR: estas decisiones no cambian el esquema ni introducen una arquitectura
nueva. Tampoco corresponde modificar `docs/contexto/02-decisiones-abiertas.md`, código, migraciones o
el documento de respuesta firmado.

## 1. Texto listo para D1 en decisiones cerradas

Insertar el siguiente párrafo al final de la sección **«Ventana de entrenamiento del modelo
(cerrado)»** de `docs/contexto/01-decisiones-cerradas.md`:

> **Ampliación de alcance — cerrada 2026-08-18 (coordinador, Vía −1):** en cualquier país y en
> cualquier vía de modelado o evaluación, 2020 queda excluido tanto como año objetivo como del pool
> histórico usado para construir etiquetas. La exclusión no elimina 2020 de la ingesta, el
> almacenamiento ni las series descriptivas o narrativas: su alcance es exclusivamente el modelado y
> la evaluación. Las corridas regionales multipaís ya realizadas, que incluyeron 2020 en el pool y
> como año de prueba, conservan una nota al pie que declara esa limitación; si esas vías se retoman,
> deben repetirse sin 2020.

Este texto amplía la decisión previa sin borrar su contexto histórico y evita interpretar la
exclusión como una orden de retirar datos reales del sistema.

## 2. Texto listo para D3 en decisiones cerradas

Insertar el siguiente párrafo en la sección **«Criterio de éxito, línea base y margen de error
(cerrado 2026-08-09)»**, después de los párrafos que definen la línea base y la métrica decisiva:

> **Ampliación del criterio — cerrada 2026-08-18 (coordinador, Vía −1):** toda evaluación debe
> reportar cuatro referencias: climatológica, constante mayoritaria, constante siempre `alto` y
> persistencia. Solo la referencia climatológica conserva carácter decisivo según el criterio
> vigente. Se agrega un veto: un resultado no puede declararse exitoso si la constante mayoritaria
> o la constante siempre `alto` supera al modelo en F1 macro. Persistencia y las dos constantes se
> reportan para dar contexto, pero no se convierten en umbrales decisivos adicionales. Cuando un
> externo no contiene observaciones reales de la clase `alto`, su recall se registra como `N/A` y
> las demás métricas, la matriz de confusión y los falsos positivos continúan siendo reportables.

La comparación decisiva ya existente contra la climatológica no se reemplaza; se complementa con
las referencias y el veto firmados.

## 3. Entrada lista para el historial

Agregar el siguiente punto **al final** de `docs/contexto/CHANGELOG.md`:

> - **2026-08-18 (Vía −1 — decisiones firmadas, estados congelados y mecanismo técnico validado):** Eduardo Rivas confirmó la recepción de la definición completa y firmó D1–D4 y la declaración previa de estados de fold en `docs/respuesta-protocolo-via-menos-uno-v2.md`. **D1:** 2020 queda excluido como año objetivo y del pool histórico en cualquier país y vía; esto no retira 2020 de la ingesta, el almacenamiento ni de usos descriptivos, y las vías regionales previas que lo usaron deben conservar la nota de limitación y repetirse sin él si se retoman. **D2:** 2016 se retira del protocolo prospectivo porque `H(2016)={2014, 2015}` no satisface los pisos; 2024 queda como externo reservado sin semanas `alto`, con recall de `alto` en `N/A`, y se declara que no existe un test simultáneamente intacto y evaluable para esa clase. **D3:** son obligatorias las referencias climatológica, constante mayoritaria, constante siempre `alto` y persistencia; solo la climatológica es decisiva y se veta declarar éxito si cualquiera de las dos constantes supera al modelo en F1 macro. **D4:** se conserva argmax fijo y no se barren umbrales; cualquier reapertura exige un anexo por vía bajo las condiciones firmadas. Los folds quedaron congelados antes de ejecutar: 2019 `no_entrenable`; 2021 `entrenable_con_clase_ausente` con recall `N/A`; 2022 `entrenable_con_clase_ausente`, con 5 `alto` externos y ninguno en entrenamiento; 2023 y 2024 `entrenable` con recall `N/A`. La implementación separada reprodujo esa firma sin diferencias: 308 filas, 21 predictores y 5 semanas `alto`, todas en 2022; allí el modelo predijo `bajo` en las 52 semanas para las semillas 0–9, con F1 macro 0,273 y recall 0/5, empatando las referencias climatológica y mayoritaria. Pasaron 17 pruebas de independencia, una mutación deliberada hizo fallar la prueba esperada y dos ejecuciones produjeron artefactos sustantivos idénticos byte por byte. Durante la validación también se corrigió en el protocolo el dato factual del calendario CDC/MMWR: sus años tienen 52 o 53 semanas, no 51; el algoritmo ya usaba `fecha_inicio`, por lo que filas y resultados no cambiaron. El resultado valida la reproducibilidad y la independencia temporal del mecanismo, no desempeño predictivo final. Evidencia completa en `docs/corrida-via-menos-uno.md`; protocolo en `docs/protocolo-evaluacion-rescate-prediccion.md`.

## 4. Cierre posterior del protocolo

Solo después de guardar y revisar los registros anteriores, aplicar estos cambios en
`docs/protocolo-evaluacion-rescate-prediccion.md`:

1. En la sección 16, cambiar:

   ```text
   - [ ] D1 y D3 están registradas formalmente en decisiones cerradas y en el historial.
   ```

   por:

   ```text
   - [x] D1 y D3 están registradas formalmente en decisiones cerradas y en el historial.
   ```

2. En la sección 17, cambiar los dos estados:

   ```text
   - **D1 — 2020 excluido de objetivo y pool en todo país y toda vía:** firmado y registrado
   - **D3 — cuatro referencias, climatológica decisiva y veto de constantes:** firmado y registrado
   ```

3. Sustituir el párrafo que asigna registros pendientes al coordinador por:

   > El coordinador registró D1 y D3 en `docs/contexto/01-decisiones-cerradas.md` y
   > `docs/contexto/CHANGELOG.md`, y dejó constancia histórica de D2, D4 y los estados de fold. Con
   > ello quedan completas las firmas, la implementación, la validación técnica y el registro
   > documental exigidos por la puerta de la sección 16.

## 5. Comprobación final para Eduardo

- [ ] D1 quedó registrada como regla de modelado y evaluación, no como eliminación de datos de 2020.
- [ ] D3 conserva a la climatológica como única referencia decisiva e incorpora el veto de las dos constantes.
- [ ] D2, D4 y todos los estados de fold aparecen en la entrada nueva del historial.
- [ ] La entrada del historial fue agregada al final y ninguna entrada previa fue reescrita.
- [ ] Los enlaces y nombres de archivo coinciden con los documentos existentes.
- [ ] El protocolo se marcó como completo solo después de guardar los registros oficiales.
- [ ] `docs/respuesta-protocolo-via-menos-uno-v2.md` permaneció sin cambios sustantivos después de la firma.

Una vez completada esta lista, la puerta documental de la Vía −1 queda cerrada. Eso habilita el
inicio de las Vías 0–3 desde el punto de vista del protocolo, sin alterar la advertencia ya firmada:
cualquier vía que conserve la etiqueta de canal endémico debe resolver primero la limitación
estructural demostrada por los folds.
