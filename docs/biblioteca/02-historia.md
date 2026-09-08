---
titulo: "De la idea original a hoy"
descripcion: "De EPICAST al pivote Camino Ancho: cinco vías de validación, el cierre del 18 de agosto de 2026 y la herramienta descriptiva que quedó."
orden: 2
categoria: "El proyecto"
---

EPI-Aetheris empezó con una meta concreta: **clasificar el riesgo de brote de dengue (alto / medio / bajo) por semana epidemiológica**, usando clima rezagado como predictor. Esa meta se evaluó con datos reales, se documentó y se cerró. Lo que el sistema hace hoy —Camino Ancho— es el resultado de esa evidencia, no un cambio de marca.

## EPICAST, el nombre y el equipo

En la fase de ideación el proyecto se llamó **EPICAST**. El 8 de julio de 2026 el equipo votó el nombre vigente, **EPI-Aetheris**. "EPI Aethery" fue un error de transcripción de esas semanas y no se usa en material nuevo.

El mismo día se cerraron el tamaño del equipo (cinco integrantes, tres en programación), el nivel académico (bachillerato técnico, INSAMT) y la ventana de datos que alimentaría cualquier modelo departamental: **2018, 2019, 2021, 2022 y 2023**, con **2020 excluido** por subregistro real durante la pandemia y por riesgo de extracción en los boletines de ese año. 2019 (26.434 casos nacionales, pico histórico) entra en esa ventana a propósito: una serie 2021–2023 sola nunca muestra un brote severo.

## La primera entrega: clasificador nacional

El parser departamental de MINSAL se construyó y sigue alimentando el mapa. La señal departamental, sin embargo, es delgada: en 2019 el desglose por departamento cubre 439 probables y 176 confirmados frente a 27.470 sospechosos nacionales. Ante el riesgo de no tener ningún clasificador a tiempo, el 9 de agosto de 2026 el coordinador eligió la **Opción C**: el primer clasificador operaría a **nivel nacional** sobre OpenDengue (serie semanal limpia, 2018–2024), y el mapa pintaría los casos departamentales de MINSAL como **capa descriptiva**, con la clasificación nacional mostrada aparte.

Ese clasificador usaba canal endémico por percentil (cortes P75/P90, clima rezagado como único predictor). Al evaluarlo contra los únicos años de la ventana con semanas reales "alto" —2019 y 2022— el **recall de la clase alta fue 0,000** en ambos, empatado con la línea base climatológica. Ampliar la ventana de rezago climático, cambiar el corte a P50/P75, alargar los años de entrenamiento e incorporar el índice ONI de NOAA no rescató esa métrica de forma estable. Los experimentos quedaron documentados y se revirtieron de producción.

## Cinco vías de validación

En agosto de 2026 se abrió una línea de rescate con protocolo temporal forward-chaining, sin fuga, y cinco vías. El [informe de cierre](https://github.com/the-monolith-project/EPI-Aetheris/blob/main/docs/rescate-prediccion/informe-cierre-rescate-prediccion.md) (18 de agosto de 2026) resume el resultado:

| Vía | Pregunta | Resultado |
|---|---|---|
| −1 | ¿La evaluación puede ejecutarse sin fuga temporal? | Mecanismo validado (17 pruebas, control mutante). Sirve para interpretar experimentos; no es evidencia predictiva por sí sola. |
| 0 | ¿Un modelo regional transfiere a países no vistos? | 0 de 16 países con transferencia sostenida. Se cierra la vía multipaís. |
| 1 | ¿Casos previos rescatan la etiqueta y el clima añade valor? | 0 de 10 semillas en el único fold evaluable; el clima no aporta. |
| 2 | ¿El clima clasifica la posición relativa dentro de la temporada? | Éxito estable en 3 de 5 folds; 2019 falla 0/10 y 2024 queda en 8/10. Objetivo distinto al declarado. |
| 3 | ¿Features climáticas con mecanismo biológico rescatan la etiqueta? | 0 de 10 semillas en el único fold evaluable. |

Ninguna vía sostuvo de forma estable el criterio de éxito predeclarado. Las vías 1 y 3 conservaban la etiqueta histórica y chocaban con el mismo límite: en el único externo con semanas "alto", el entrenamiento no contenía ejemplos de esa clase. La vía 0 descartó que otros países resolvieran esa ausencia de forma transferible.

La recomendación del informe fue explícita: **cerrar la línea sin adoptar ningún modelo experimental** y entregar el resultado negativo como evidencia reproducible. El código (`entrenar_clasificador.py` y afines) permanece en el repositorio; no se extiende ni se expone como predicción en vivo.

## El experimento de lead time

El mismo 18 de agosto se corrió la validación empírica de la tesis de "ventana de anticipación": que el índice de idoneidad biofísica (`Iv`) más un detector de anomalías (Z ≥ 1,5 durante dos semanas consecutivas) adelantaría el ascenso real de casos.

De diez años-nivel evaluados (cinco nacionales y cinco en San Salvador, el único departamento con suficiencia), solo dos tenían a la vez alerta y un inicio de temporada definido. Los lead times fueron **+29 y −30 semanas**, sin acuerdo de signo. En seis de diez casos el detector no disparó ninguna alerta, aunque el Z-score cruzó 1,5 en el 100 % de los años evaluados: el criterio de dos semanas consecutivas filtra casi toda la señal.

No hay una cifra de anticipación que el proyecto pueda comunicar. Esa tesis se retira. Las fórmulas de `Iv` y el Z-score, usadas como **series continuas**, sí se conservan.

## Camino Ancho

Con esas dos piezas —informe de cierre y experimento de lead time— el coordinador cierra cualquier afirmación de capacidad predictiva. El proyecto se reorienta a **Camino Ancho**: una herramienta descriptiva de análisis espacio-temporal. La pregunta pasa de "¿habrá un brote?" a "¿qué está ocurriendo en cada departamento, qué tan inusual es frente a su historia, y qué tan completa es la información?".

Cuatro módulos:

1. **Idoneidad biofísica (`Iv`)** — implementado el 18–19 de agosto de 2026.
2. **Anomalía climática continua** (Z-score leave-one-out) — implementado el mismo tramo, sin alerta binaria.
3. **Presión epidemiológica relativa** — fórmula cerrada el 21 de agosto de 2026 e implementada (percentil leave-one-out, series probable/confirmado separadas).
4. **Confianza de vigilancia** — sin fórmula aprobada; el selector del mapa lo deja como capa no disponible.

Nada de M1–M3 se persiste: se calcula al consultar la API. El mapa sigue mostrando casos MINSAL desacumulados como capa descriptiva. En septiembre se suman el observatorio respiratorio (IRA, neumonías, vigilancia viral), las alertas de campo humanas (luego operables con token de escritura, sin tabla de usuarios) y la arquitectura de información de dos caras.

Esa es la trayectoria: una meta ambiciosa, un protocolo que no dejó elegir el resultado después de verlo, y un producto que describe lo que los datos ya muestran.
