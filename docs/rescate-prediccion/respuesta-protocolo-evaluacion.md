# Respuesta del coordinador al protocolo de evaluación — rescate de predicción

**Estado:** respuesta emitida. Pendiente únicamente de la firma formal en la sección 7.
**Responde a:** `protocolo-evaluacion-rescate-prediccion.md` (2026-08-17), que bloquea la Vía −1 y las Vías 0–3 hasta que D1–D4 tengan respuesta explícita.
**Sustituye a:** el documento de respuesta anterior, que dejaba D2, D3 y D4 sin resolver. Las respuestas de aquí son firmes salvo donde se indique lo contrario.

Este documento no modifica producción. Sí cierra decisiones metodológicas, y dos de ellas tocan estatutos ya cerrados del proyecto — ver sección 6.

---

## D1 — Papel de 2020

**Respuesta: se acepta la opción recomendada. 2020 queda excluido tanto como año objetivo como del pool histórico.**

Fundamento verificado: el `ANIOS_BASE` de producción ya es `[2018, 2019, 2021, 2022, 2023]` — 2020 no aparece en ningún rol. La opción recomendada por el protocolo coincide con el precedente vigente, y con el razonamiento ya registrado de que las cifras de 2020 reflejan la capacidad de reporte del sistema durante la pandemia y no la transmisión real. La alternativa exigiría justificación específica que no existe.

**Ampliación de alcance, que el protocolo no contemplaba y sí hace falta:** la exclusión aplica a **cualquier país y cualquier vía**, no solo a El Salvador nacional. El motivo del subregistro de 2020 vale igual para Colombia, Guatemala o Brasil.

Consecuencia inmediata, porque hay trabajo ya hecho que la incumple: **las corridas regionales multipaís incluyeron 2020**, tanto en el pool como en calidad de año de prueba (aparece con soporte de 52 semanas "alto" en las tablas de las corridas B y C). Esas tablas quedan con una nota al pie declarando que incluyeron 2020, y si alguna de esas vías se retoma, se rehace sin él. No se corrigen retroactivamente los números publicados: se anotan.

---

## D2 — Año externo final

**Respuesta: no existe un año que sea a la vez intacto y evaluable. Se declara formalmente que no hay test final independiente en el sentido pleno, y se procede con la configuración de abajo.**

### Verificación

La pregunta previa del protocolo —si los resultados nacionales de 2024 influyeron en la elección de features, modelo o criterio— se responde **no**. Los trece informes de entrenamiento existentes usan como años de prueba únicamente 2014, 2019 y 2022; 2024 no aparece en ningún `ANIOS_BASE` ni en ningún informe de selección. Su única presencia en el código es como límite superior de la ventana de ingesta.

Pero eso no basta, porque hay una segunda pregunta que el protocolo no hace y que decide el asunto: **¿tiene 2024 casos de la clase que el criterio exige detectar?** Etiqueté los años externos contra el pool de años base de producción, con el mismo corte P75/P90, la misma ventana ±1 y el mismo piso de suficiencia:

| Año externo | Casos anuales | Distribución de etiqueta | Semanas "alto" |
|---|---|---|---|
| 2024 | 8.477 | 50 bajo | **0** |
| 2017 | 4.402 | 50 bajo | **0** |
| 2016 | 8.789 | 6 alto / 9 medio / 35 bajo | 6 |
| 2015 | 50.169 | 35 alto / 8 medio / 7 bajo | 35 |
| 2014 | 53.196 | 48 alto / 2 bajo | 48 |
| 2020 | 5.334 | 7 alto / 43 bajo | *(excluido por D1)* |

**2024 no contiene ninguna semana "alto".** Reservarlo como evaluación final no entrega la mitad decisiva del criterio: el recall de la clase alta no es calculable ahí. Es exactamente la trampa que ya dejó sin métrica decisiva la corrida de producción sobre 2023.

Y el cuadro completo es peor que un problema de 2024:

- **Intactos pero no evaluables:** 2024 y 2017, ambos con cero semanas "alto".
- **Evaluables pero quemados:** 2014 y 2015, usados como años de prueba en el experimento de ventana ampliada y en la corrida A multipaís.
- **Evaluable y poco tocado:** 2016, con 6 semanas "alto", visto una sola vez como año de prueba en la corrida A multipaís (donde apareció con soporte 5, bajo un pool distinto).
- **Excluido:** 2020, por D1.

### Decisión

1. **2024 queda reservado como año externo final**, por ser el único genuinamente intacto. **Se declara desde ahora, antes de correr nada, que el recall de la clase alta no será calculable en ese año** y que la evaluación final solo podrá hablar de F1 macro y de las clases medio y bajo. Declarado antes de correr es una limitación conocida; declarado después sería una excusa, y no se aceptará como tal.
2. **2016 se suma como segundo año externo**, marcado como levemente contaminado (visto una vez en la corrida A). Es la única prueba disponible que toca la clase que importa. Su soporte de 6 semanas es pequeño: cualquier lectura de recall sobre él debe reportar los aciertos absolutos y no puede presentarse como evidencia fuerte por sí sola.
3. **Se registra explícitamente que no existe un test final intacto y evaluable simultáneamente.** Todo resultado se reporta como validación forward-chaining exploratoria, nunca como desempeño final independiente.
4. 2019 y 2022 quedan confirmados como años de desarrollo, tal como el protocolo ya asumía.

### Salvedad sobre las cifras

La tabla de arriba se calculó sobre el extracto PAHO de OpenDengue, no sobre la base cargada del proyecto. Hay diferencias de pocos casos entre extractos (2019 da 27 semanas "alto" aquí frente a las 28 del informe de entrenamiento). La conclusión sobre 2024 no depende de eso —cero es cero con holgura— pero **antes de fijar esto en el protocolo hay que reproducir la tabla contra la base propia.**

---

## D3 — Criterio ampliado

**Respuesta: las cuatro referencias son obligatorias de reportar. Solo la climatológica sigue siendo decisiva. Se agrega un piso de descalificación.**

Estado real de partida, más avanzado de lo que suponía el protocolo: el criterio cerrado el 2026-08-09 ya declara una línea base doble. La **climatológica** es la decisiva (superar F1 macro y recall de "alto", por año de prueba) y la de **persistencia** ya está cerrada como referencia de exhibición obligatoria, no como umbral a superar, y declarada no desplegable en vivo. Lo genuinamente nuevo son las dos constantes.

### Qué se aprueba

- **Constante mayoritaria** y **constante siempre-alto** se aprueban como referencias **adicionales y obligatorias de reportar**, en el mismo estatus que persistencia: se muestran, no son decisivas.
- **La climatológica sigue siendo la única decisiva.** No se amplía el criterio de aprobación.

### Por qué no se hacen decisivas

Porque "siempre alto" es un rival cuya dificultad varía de forma brutal según el año. Donde la clase alta es el 2 % de las semanas, ganarle es trivial; donde es el 65 %, es casi imposible. Convertirlo en criterio metería el efecto año —el problema que estamos tratando de aislar— dentro del criterio mismo.

### Piso de descalificación (esto sí es nuevo y sí es vinculante)

**Cualquier resultado en el que un predictor constante supere al modelo en F1 macro se reporta como no válido como éxito, aunque el modelo haya superado a la climatológica.**

No es un criterio adicional que haya que superar: es un veto de cordura. Existe porque ya ocurrió el caso que describe. En la corrida regional multipaís, el año 2024 quedó marcado como "SUPERA" con F1 macro 0,139, mientras que un predictor que dijera "alto" siempre habría obtenido 0,262 y recall 1,000 en ese mismo año. El modelo superó el criterio en el año en que fue peor que la respuesta más tonta posible. Sin este piso, eso vuelve a pasar y vuelve a leerse como éxito.

---

## D4 — Tratamiento del umbral

**Respuesta: argmax fijo. No se barren umbrales sobre la etiqueta actual. Reapertura condicionada por vía.**

Verificado en el repositorio: `entrenar_clasificador.py` no tiene hoy ningún mecanismo de umbral —no aparece `umbral`, `threshold`, `predict_proba` ni `argmax`— y producción usa `.predict()` directo. No hay precedente que preservar; esto sería un mecanismo enteramente nuevo.

### Por qué no se permite sobre la etiqueta actual

Hay evidencia directa, no una preferencia metodológica:

- Se probó selección de umbral por validación interna dentro de los años de entrenamiento, y el procedimiento eligió 0,50 — es decir, ningún cambio respecto de argmax.
- El AUC de la probabilidad de "alto" contra el "alto" real es **0,234 en 2019 y 0,231 en 2022**. Está por debajo de 0,5: el ordenamiento de probabilidades está invertido respecto de la verdad.

Ningún umbral rescata una señal que apunta al revés. Permitir el barrido añadiría un grado de libertad con pago conocido de cero y riesgo real de contaminación del año externo.

### Condición de reapertura

Si la Vía 1 (casos previos como predictor) o la Vía 2 (etiqueta relativa al propio año) cambian el objetivo, la evidencia de arriba deja de aplicar, porque se mide sobre otra etiqueta. En ese caso el ajuste de umbral **puede** considerarse, con estas condiciones acumulativas:

1. **Condición de entrada:** el AUC de la probabilidad de la clase alta, medido en folds internos de entrenamiento, debe superar 0,5. Si no lo supera, no hay señal que ajustar y no se barre.
2. Lista de umbrales candidatos congelada y escrita **antes** de correr.
3. El umbral se elige exclusivamente en folds internos de entrenamiento. Si no hay folds internos válidos, se conserva argmax.
4. El año externo se evalúa **una sola vez**, con el umbral ya congelado.
5. La reapertura se solicita por vía y por escrito, no se asume concedida.

Cualquier barrido sobre el año externo es descriptivo y no puede seleccionar nada, tal como el protocolo ya establece.

---

## 5. Nota sobre la Vía −1

El protocolo menciona una Vía −1 en varios puntos, pero **su definición no aparece en el material del que dispone el coordinador al escribir esta respuesta.** No se encontró en el protocolo ni en los documentos de tarea circulados.

En consecuencia, las cuatro respuestas de D1 a D4 se redactaron de forma general, para que apliquen a cualquier vía: mismo tratamiento de 2020, mismos años externos, mismo criterio ampliado con su piso de descalificación, y argmax fijo mientras se use la etiqueta actual. No se hizo ninguna suposición sobre qué es la Vía −1 ni sobre qué necesita.

**Si alguna de estas cuatro respuestas no encaja con lo que la Vía −1 realmente requiere, indíquenlo y se corrige.** Esta respuesta no es una postura cerrada frente a algo que no se pudo leer: es la mejor respuesta posible con la información disponible, y se revisa sin problema en cuanto se aporte la definición faltante. Lo que sí se pide a cambio es que la corrección venga con el texto de la Vía −1 adjunto, para no volver a responder a ciegas.

---

## 6. Estatutos que estas respuestas modifican

Dos de las cuatro decisiones tocan documentación ya cerrada del proyecto y **no entran en vigor hasta quedar registradas**:

| Decisión | Qué cambia | Dónde se registra |
|---|---|---|
| D1, ampliación de alcance | La exclusión de 2020 pasa de ser una regla de la ventana nacional a aplicar a todo país y toda vía | `docs/contexto/01-decisiones-cerradas.md` + `CHANGELOG.md` |
| D3, piso de descalificación | Se agrega un veto que puede invalidar un resultado que sí supera la línea base decisiva | `docs/contexto/01-decisiones-cerradas.md` + `CHANGELOG.md` |

D2 y D4 no modifican estatutos: D2 registra una limitación de los datos y D4 confirma el comportamiento vigente de producción. Ambas van al historial de todas formas, para que la próxima sesión no las reabra como ideas nuevas.

---

## 7. Registro de aprobación

Reemplaza la sección 10 del protocolo, que debe actualizarse en sincronía.

- **D1 — 2020 excluido de objetivo y de pool, en todo país y toda vía:** pendiente de firma
- **D2 — 2024 como externo final sin recall de "alto" calculable, 2016 como segundo externo, sin test final intacto:** pendiente de firma
- **D3 — cuatro referencias obligatorias de reportar, solo climatológica decisiva, más piso de descalificación:** pendiente de firma
- **D4 — argmax fijo, reapertura condicionada por vía con AUC > 0,5 como condición de entrada:** pendiente de firma
- **Reproducción de la tabla de D2 contra la base propia:** pendiente
- **Aprobado por:** pendiente
- **Fecha de aprobación:** pendiente

---

## 8. Checklist para comenzar las Vías 0–3

Ningún experimento arranca hasta que todo esto esté marcado:

- [ ] D1–D4 firmados en la sección 7.
- [ ] Definición de la Vía −1 aportada, y confirmación de que D1–D4 son compatibles con ella o corrección solicitada (sección 5).
- [ ] Tabla de D2 reproducida contra la base del proyecto, con las cifras propias.
- [ ] Cambios de D1 y D3 registrados en el archivo de decisiones cerradas y en el historial.
- [ ] Pruebas de independencia del fold existentes y **vistas fallar** ante una fuga deliberada, no solo escritas.
- [ ] Años externos congelados por escrito, con la declaración de que no existe un test final intacto y evaluable a la vez.
