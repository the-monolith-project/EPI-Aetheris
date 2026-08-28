# EPI-Aetheris: cambio de orientación hacia el Camino Ancho

**Fecha del registro:** 2026-08-19  
**Punto de referencia solicitado:** `faf90edd21c323e55d2a5b3e02e2c12525143152`  
**Estado:** síntesis técnica del cambio; no sustituye los registros formales de `docs/contexto/`

## 1. Propósito de este documento

Este documento explica qué se quería conseguir originalmente con EPI-Aetheris, qué evidencia obligó
a cambiar la orientación, en qué consiste la ruta denominada **Camino Ancho**, qué recursos utiliza,
qué se ha construido y qué falta por resolver.

El cambio no abandona el propósito de relacionar clima y dengue. Cambia la forma de presentar y usar
esa relación: de una clasificación predictiva que no pudo demostrar capacidad prospectiva suficiente,
a un conjunto de indicadores descriptivos, reproducibles y explícitos sobre sus limitaciones.

## 2. Qué se quería conseguir originalmente

La meta inicial era construir una herramienta abierta y reproducible que utilizara clima previo para
clasificar el riesgo semanal de dengue como `bajo`, `medio` o `alto`.

La primera fase se diseñó a nivel nacional porque la señal departamental de MINSAL era demasiado
incompleta para sostener un clasificador propio. Los departamentos seguirían apareciendo en el mapa,
pero únicamente como una capa descriptiva de casos, no como predicciones departamentales.

La propuesta buscaba:

1. utilizar datos públicos y reales;
2. evitar que los casos de la misma semana entraran como predictores;
3. emplear variables climáticas de semanas anteriores;
4. separar entrenamiento y evaluación en el tiempo;
5. anticipar semanas de mayor actividad con margen útil;
6. superar referencias simples, no solo producir una métrica aparentemente favorable;
7. mantener el sistema gratuito, autocontenido y reproducible con Docker.

El componente central era un clasificador Random Forest con 21 predictores climáticos rezagados. La
etiqueta de riesgo provenía de un canal endémico histórico y debía construirse sin usar información
del año evaluado ni de años futuros.

## 3. Qué mostró la evaluación del clasificador

Antes de seguir ajustando el modelo se construyó un mecanismo de evaluación `forward-chaining`, es
decir, cada año se evaluó utilizando únicamente años anteriores. También se congelaron fuentes,
parámetros, criterios, semillas y firmas de artefactos para evitar seleccionar una configuración
después de observar el resultado.

### Vía −1: validación limpia del problema original

La Vía −1 confirmó que el mecanismo podía separar los años sin fuga temporal, pero reveló una
limitación estructural: el único año externo con semanas `alto` fue 2022 y su entrenamiento no
contenía ningún ejemplo de esa clase.

El modelo obtuvo `0 de 5` aciertos de `alto`, recall `0,000` y el mismo F1 macro que las referencias
climatológica y mayoritaria. La corrida validó el mecanismo técnico, no la capacidad predictiva.

### Vía 0: transferencia entre países

Se evaluó si entrenar con otros países podía aportar ejemplos y producir una relación climática
transferible a países no observados. Ninguno de los 16 países cumplió la condición predeclarada de
transferencia sostenida. Para El Salvador, aun con ejemplos `alto` de otros países, el modelo obtuvo
`0 de 5` aciertos en 2022.

La evidencia no respaldó adoptar un clasificador regional como sustituto del modelo nacional.

### Vía 1: casos anteriores y clima

Se probaron casos de semanas anteriores, solos y combinados con clima. Las dos variantes produjeron
los mismos resultados y volvieron a obtener `0 de 5` aciertos de `alto` en 2022.

Además, depender de casos recientes habría cambiado la propuesta: sería una estimación del presente
o del muy corto plazo, no una anticipación basada únicamente en clima. La fuente nacional disponible
tampoco se actualiza semanalmente de forma operativa.

### Vía 2: etiqueta relativa al mismo año

Una etiqueta intraanual produjo resultados mejores en varios folds, pero necesitaba conocer el año
completo para calcular sus percentiles. Por lo tanto, solo sirve para describir retrospectivamente la
posición de una semana dentro de su propia temporada.

También cambia el significado del resultado: una semana `alto` de un año leve podría contener menos
casos que una semana `bajo` de un año severo. No era un reemplazo válido para el riesgo contra la
historia ni una salida prospectiva.

### Vía 3 y otros intentos de rescate

Se reemplazaron los rezagos climáticos crudos por siete transformaciones inspiradas en mecanismos
biológicos, como acumulación térmica, interacción de temperatura y humedad y pulsos de lluvia. No
mejoraron el fold decisivo: nuevamente hubo `0 de 5` aciertos de `alto`.

También se exploraron una ventana climática más amplia, ONI/El Niño y una primera corrida multipaís.
Ninguna produjo evidencia suficiente para rescatar, para El Salvador, la promesa original bajo una
evaluación temporal limpia.

## 4. Por qué se cambió de ruta

Seguir ajustando el mismo clasificador sobre los mismos años habría elevado el riesgo de sobreajuste
y de seleccionar retrospectivamente una combinación favorable. El problema principal no era elegir
otro algoritmo: era la estructura de la evidencia disponible.

Los principales motivos del cambio fueron:

- muy pocos años nacionales utilizables;
- concentración de la clase `alto` en un solo año externo;
- datos departamentales de MINSAL con cobertura y actividad insuficientes para entrenar 14 modelos;
- falta de actualización semanal de algunas fuentes de casos;
- ausencia de transferencia climática estable entre países;
- alternativas que mejoraban métricas pero respondían una pregunta retrospectiva diferente;
- imposibilidad de demostrar una anticipación consistente sin fuga temporal.

Por estas razones se decidió conservar lo que sí puede sostenerse con los datos: describir las
condiciones climáticas favorables, compararlas con el historial local y hacer visibles las
limitaciones de vigilancia. Esta es la base del **Camino Ancho**.

## 5. Validación de la promesa de anticipación

Antes de implementar el nuevo camino se probó específicamente la hipótesis de que un índice
biofísico podía adelantarse entre cuatro y seis semanas al ascenso observado de casos.

La validación utilizó clima departamental 2014–2024 y casos MINSAL departamentales de 2018, 2019,
2021, 2022 y 2023. Se comparó la primera señal climática con el inicio de temporada observado.

Solo aparecieron dos pares comparables:

| Nivel | Resultado |
|---|---:|
| Nacional, 2018 | señal climática 29 semanas antes |
| San Salvador, 2023 | señal climática 30 semanas después |

Los resultados tienen signos opuestos y descansan en una muestra extremadamente pequeña. Además,
el umbral climático se cruzaba de manera aislada en todos los años, por lo que no funcionaba como un
precursor raro y limpio.

La conclusión correcta no es que el clima carezca de relación con el dengue. La conclusión es más
limitada: **estos datos y este mecanismo no sostienen una ventana de anticipación medible y
consistente**. Por eso se retiraron del producto el número de semanas prometido y la alerta binaria.

## 6. En qué consiste el Camino Ancho

El Camino Ancho transforma el producto en un tablero de apoyo descriptivo. Se organiza en cuatro
módulos, además de la capa de casos existente. La variante implementada actualmente corresponde al
**Camino Ancho v3**: conserva los indicadores continuos y retira la alerta y la promesa de lead time
que no sobrevivieron a la validación.

### Módulo 1: idoneidad biofísica

Calcula un índice continuo `Iv` entre 0 y 1 para cada departamento y semana. Combina:

- temperatura media;
- precipitación acumulada de la semana actual y anterior;
- humedad relativa media.

La fórmula implementada es:

```text
Iv = f_T(temperatura) × (0,3 + 0,7 × f_R(precipitación)) × f_H(humedad)
```

`f_T` representa idoneidad térmica entre 16 °C y 38 °C; `f_R` es una función logística de
precipitación; `f_H` penaliza humedad inferior al 50 %.

Este valor describe condiciones ambientales compatibles con el vector. **No es una probabilidad de
brote, una estimación de casos ni una recomendación médica.** La función de humedad es una
estimación propia del equipo y la calibración completa sigue siendo provisional.

### Módulo 2: anomalía climática continua

Compara el `Iv` de una semana con el historial de ese mismo departamento y semana epidemiológica.
El año consultado se excluye de su propio baseline para evitar contaminación.

El resultado `anomaly_sigma` indica qué tan alejado está el valor actual de su referencia histórica.
Se mantiene como una escala continua y descriptiva: no existe umbral de alerta, semáforo de urgencia
ni afirmación de que un valor alto implique un brote.

### Módulo 3: presión relativa

Está previsto para comparar actividad observada contra una referencia histórica de forma
interpretable. Todavía no tiene una fórmula aprobada ni implementación. La interfaz lo muestra
deshabilitado como `próximamente` para no inventar una definición.

### Módulo 4: confianza de vigilancia

Está previsto para hacer visible la suficiencia y continuidad de los datos epidemiológicos por
departamento. Tampoco tiene una fórmula aprobada. Su finalidad será impedir que ausencia de datos se
confunda con ausencia de casos.

### Capa existente: volumen MINSAL

El mapa conserva la capa departamental de casos probables reportados por MINSAL. Es una capa
descriptiva e independiente; no debe interpretarse como salida del índice climático ni como riesgo
calculado por departamento.

## 7. Recursos de datos

### Clima

- **Proveedor:** Open-Meteo Archive API.
- **ERA5-Land:** temperatura máxima, mínima y media, humedad relativa media y punto de rocío.
- **ERA5:** suma y horas de precipitación, porque ERA5-Land no entrega esas variables en el pipeline
  vigente.
- **Cobertura usada por el Camino Ancho:** 2014–2024.
- **Resolución operativa:** 14 centroides departamentales de El Salvador.
- **Agregación:** medias semanales para variables de estado y sumas semanales para precipitación.

M1 y M2 consumen específicamente `temp_media`, `precipitation_sum` y
`humedad_relativa_media`. Las demás variables permanecen disponibles para el sistema y para
experimentos documentados, pero no forman parte del `Iv` actual.

### Casos epidemiológicos

- **MINSAL:** boletines epidemiológicos públicos con datos departamentales. Para la validación de
  inicio de temporada se sumaron `probable` y `confirmado` en 2018, 2019, 2021, 2022 y 2023. Esta
  suma fue un supuesto explícito del experimento, no una convención epidemiológica cerrada.
- **OpenDengue:** serie nacional semanal usada por el clasificador y las evaluaciones anteriores. No
  es necesaria para calcular M1 y M2 en tiempo de consulta.
- **2020:** se conserva en la ingesta climática, pero se excluyó de los experimentos de casos por
  las limitaciones documentadas de vigilancia durante la pandemia.

El Camino Ancho puede calcular idoneidad y anomalía sin casos recientes. Los casos se utilizan como
capa descriptiva y como referencia retrospectiva para comprobar qué afirmaciones son defendibles.

### Geografía

- códigos departamentales ISO 3166-2:SV;
- centroides de los 14 departamentos para consultar clima;
- GeoJSON departamental para la visualización en Leaflet;
- región nacional `SV` para las comparaciones históricas nacionales.

### Datos versionados y trazabilidad

El repositorio incluye un seed de datos reales en `db/seed/seed_datos_reales.sql`. Un primer arranque
limpio de PostgreSQL carga ese seed, por lo que la aplicación puede reproducirse sin descargar otra
vez las fuentes ni volver a procesar todos los boletines.

Los experimentos anteriores utilizaron manifiestos congelados, hashes SHA-256, semillas fijas,
pruebas contra fuga y artefactos intermedios separados. Esto permite distinguir un resultado
reproducible de una exploración ajustada después de ver las métricas.

## 8. Recursos técnicos

| Capa | Recurso | Función |
|---|---|---|
| Persistencia | PostgreSQL 15 | almacena regiones, semanas, clima, casos y procedencia |
| Backend | Python, FastAPI y psycopg2 | calcula M1/M2 y expone la API mediante SQL directo |
| Cálculo experimental | Python, NumPy y scikit-learn | ejecuta las vías y evaluaciones históricas |
| Frontend | Astro, TypeScript, Tailwind y Leaflet | presenta el selector de capas y el mapa |
| Orquestación | Docker Compose | levanta base, backend y frontend de forma reproducible |
| Control de cambios | Git | conserva código, documentos, seeds y evolución del enfoque |

El Camino Ancho no introdujo nuevas dependencias, otro framework ni cambios de esquema. Reutiliza la
arquitectura existente y mantiene el objetivo de costo de replicación tendiendo a cero.

Para ejecutar la aplicación normalmente se requieren Docker, Docker Compose y Git. El sistema levanta
tres servicios: `db`, `backend` y `web`. La red solo es necesaria al actualizar las fuentes; el seed
versionado permite reproducir el estado histórico en un entorno nuevo sin depender de una descarga
en vivo.

## 9. Implementación disponible

### Backend

- `backend/api/idoneidad.py`: fórmulas, series de `Iv`, baseline y anomalía.
- `GET /api/v1/spatial/current?week=<semana>&year=<año>`: valores departamentales para una semana.
- `GET /api/v1/temporal/<codigo>?anio=<año>`: serie anual contra la banda histórica departamental.
- `backend/api/tests/test_idoneidad.py`: pruebas de fórmulas y comportamiento puro.
- `backend/api/tests/test_endpoints_idoneidad.py`: pruebas de los contratos HTTP contra PostgreSQL.

### Validación

- `backend/ingestion/validar_leadtime_camino_ancho.py`: validación retrospectiva de la anticipación.
- `backend/ingestion/inicio_temporada_departamental.py`: cálculo exploratorio del inicio de temporada
  por departamento.
- `docs/experimento-validacion-leadtime-camino-ancho.md`: metodología, resultados y limitaciones.

### Frontend

`web/src/components/MapaDepartamentos.astro` reutiliza un único mapa Leaflet y permite seleccionar:

1. volumen de casos MINSAL;
2. idoneidad biofísica;
3. anomalía climática continua;
4. presión relativa, deshabilitada;
5. confianza de vigilancia, deshabilitada.

La anomalía utiliza una escala continua azul, gris y naranja. Se evitó el rojo de alerta y el
lenguaje de cruce de umbral porque la validación no respaldó esa interpretación.

## 10. Cambios registrados desde el punto de referencia

El bloque incorporado alrededor de `faf90edd21c323e55d2a5b3e02e2c12525143152` quedó integrado en
`main` mediante tres líneas de trabajo:

| Cambio | Contenido |
|---|---|
| `ab68452` / PR #24 | validación empírica de la ventana de anticipación |
| `c89c28c` / PR #25 | backend de M1 y M2, endpoints y pruebas |
| `faf90ed` / PR #26 | selector de capas descriptivas en el mapa |

En conjunto se añadieron o modificaron ocho archivos, con aproximadamente 2.062 líneas agregadas y
94 eliminadas. No se modificó el esquema de base de datos.

## 11. Qué puede afirmarse y qué no

### Afirmaciones respaldadas

- El mecanismo de evaluación temporal puede ejecutarse sin fuga bajo las reglas congeladas.
- El clasificador original no supera sus referencias de forma suficiente para adoptarse.
- `Iv` produce una distribución no degenerada sobre el corpus climático real.
- La API puede calcular `Iv` y anomalía por departamento y semana.
- Las capas descriptivas pueden mostrarse en el mapa sin convertirlas en riesgo departamental.
- La promesa de cuatro a seis semanas de anticipación no está respaldada y fue retirada.

### Afirmaciones que no deben hacerse

- que `Iv` predice casos de dengue;
- que una anomalía positiva constituye una alerta;
- que existe una ventana validada de anticipación;
- que el mapa ofrece predicción departamental;
- que ausencia de datos significa cero casos;
- que M3 y M4 ya tienen una definición validada;
- que el clasificador original está listo para producción.

## 12. Estado actual y puntos pendientes

El cambio conceptual está bien encaminado y M1/M2 ya cuentan con backend e integración inicial en el
mapa. Sin embargo, la ruta todavía no debe considerarse cerrada.

1. **Registro oficial:** `docs/contexto/00-resumen.md`, decisiones cerradas, decisiones abiertas y
   `CHANGELOG.md` todavía no reflejan completamente la nueva orientación. También debe versionarse la
   propuesta canónica del Camino Ancho o trasladar sus requisitos a la documentación oficial.
2. **Fecha visible:** el frontend consulta actualmente una fotografía fija de la SE01/2023 sin
   mostrar esa fecha de manera suficientemente clara. Debe presentarla o incorporar un selector de
   año y semana.
3. **Nombre de la anomalía:** el cálculo usa mediana como centro y desviación estándar como escala.
   No es el z-score convencional basado en media; se debe corregir la fórmula o precisar el nombre y
   la explicación de la medida.
4. **Precipitación faltante:** la semana anterior ausente puede convertirse internamente en `0.0`.
   Debe devolverse ausencia explícita, excepto la regla documentada de semana 1.
5. **Calibración de humedad:** `f_H` es una estimación propia y toma el valor máximo en la gran
   mayoría del corpus. Se necesita análisis de sensibilidad antes de atribuirle capacidad
   discriminante.
6. **Texto sobre MINSAL:** el frontend menciona tablas en imagen como limitación general, pero la
   evidencia posterior mostró que en los boletines problemáticos la tabla normalmente estaba
   ausente. El texto debe ajustarse a la evidencia vigente.
7. **Pruebas reproducibles:** las pruebas de API dependen de una base previamente poblada y `pytest`
   no está instalado en la imagen. Debe documentarse un comando disponible o añadirse un entorno de
   pruebas, y verificar explícitamente que el corpus climático no esté vacío.
8. **M3 y M4:** sus fórmulas, entradas, interpretación y criterios de suficiencia siguen pendientes
   de decisión antes de implementarlos.

## 13. Lectura general del avance

El proyecto no encontró evidencia suficiente para defender el producto predictivo originalmente
planteado. En lugar de ocultar ese resultado o ajustar indefinidamente el modelo, convirtió la
evidencia negativa en una restricción de diseño.

El Camino Ancho conserva los activos válidos del proyecto —datos reales, pipelines, base de datos,
API, mapa, evaluación temporal y trazabilidad— y elimina las afirmaciones que no sobrevivieron a la
validación. El resultado actual es menos ambicioso en lenguaje predictivo, pero más sólido como
herramienta técnica de consulta y comunicación de condiciones climáticas y calidad de datos.

La siguiente etapa no consiste en volver a presentar los indicadores como predicciones. Consiste en
cerrar su semántica, hacer visible el periodo consultado, fortalecer la reproducibilidad y definir M3
y M4 con evidencia antes de implementarlos.

## 14. Referencias internas principales

- `docs/contexto/00-resumen.md`
- `docs/contexto/01-decisiones-cerradas.md`
- `docs/contexto/02-decisiones-abiertas.md`
- `docs/contexto/03-fuentes-de-datos.md`
- `docs/corrida-via-menos-uno.md`
- `docs/corrida-via-cero.md`
- `docs/corrida-via-uno.md`
- `docs/corrida-via-dos.md`
- `docs/corrida-via-tres.md`
- `docs/experimento-validacion-leadtime-camino-ancho.md`
- `backend/api/idoneidad.py`
- `backend/api/main.py`
- `web/src/components/MapaDepartamentos.astro`
