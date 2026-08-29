# Informe de cierre — rescate de la capa de predicción

**Fecha:** 2026-08-18

**Estado técnico:** Vías −1, 0, 1, 2 y 3 completadas

**Recomendación:** cerrar la línea de rescate sin adoptar ninguno de los modelos experimentales

## Bitácora de resultados

| Vía | Pregunta | Resultado | Cierre técnico |
|---|---|---|---|
| −1 | ¿La evaluación puede ejecutarse sin fuga temporal? | Mecanismo validado; 17 pruebas, control mutante y repetibilidad completa | usar el protocolo para interpretar experimentos, no como evidencia predictiva |
| 0 | ¿El modelo regional transfiere a países no vistos? | 0 de 16 países con transferencia sostenida | cerrar multipaís |
| 1 | ¿Casos previos rescatan la etiqueta histórica y el clima añade valor? | ambas variantes: 0 de 10 semillas en el único fold evaluable; clima sin aporte | no adoptar |
| 2 | ¿El clima clasifica la posición relativa dentro de la temporada? | éxito estable en 3 de 5 folds; 2019 falla 0/10 y 2024 queda en 8/10 | no adoptar; objetivo retrospectivo y distinto |
| 3 | ¿Features climáticas con mecanismo biológico rescatan la etiqueta histórica? | 0 de 10 semillas en el único fold evaluable | no adoptar |

Ninguna vía satisface de forma estable el criterio completo predeclarado. Las Vías 1 y 3 conservan la
etiqueta histórica y chocan con la misma limitación: en el único externo con semanas `alto`, el
entrenamiento no contiene ejemplos de esa clase. La Vía 0 descarta que otros países resuelvan de
forma transferible esa ausencia. La Vía 2 produce señal parcial porque redefine el objetivo, pero
necesita el año completo y falla la regla de estabilidad en dos externos.

## Tareas cerradas

- Protocolo temporal forward-chaining, cuatro referencias, veto de constantes y argmax fijo
  implementados en scripts separados de producción.
- Pruebas automáticas de independencia y controles mutantes ejecutados para cada mecanismo.
- Vías 0, 1, 2 y 3 corridas con datos públicos reales, 10 semillas y artefactos reproducibles.
- Informes individuales con métricas por año, recalls absolutos, limitaciones y recomendación.
- Confirmado que ninguna corrida modifica PostgreSQL, esquema, pipelines o modelos de producción.

## Pendientes de coordinación

- Eduardo debe incorporar en las fuentes oficiales el registro documental ya preparado para D1,
  D3 y el historial de la Vía −1.
- Eduardo debe ratificar el cierre de la línea y la decisión de no adoptar los modelos
  experimentales; las corridas no sustituyen esa decisión de producto.
- La Vía 4 sigue bloqueada por falta de celdas departamentales que satisfagan el piso. No debe
  ejecutarse salvo solicitud explícita del coordinador y decisión previa sobre el piso.

No queda otra corrida técnica pendiente dentro de las Vías 0–3.

## Recomendación de entrega

Entregar el resultado negativo como evidencia reproducible: el proyecto auditó fuga, transferencia,
autorregresión, cambio de objetivo y features con mecanismo sin escoger configuraciones después de
ver los externos. No integrar una clasificación experimental al tablero como si fuera una alerta.

El producto puede sostener su aporte de ingeniería con la ingesta reproducible, la trazabilidad, la
capa descriptiva y el canal endémico presentado como comparación histórica determinista, acompañado
por una explicación visible de que la capa predictiva no alcanzó evidencia suficiente. Esto es más
defendible que publicar una métrica parcial bajo una pregunta distinta.

## Evidencia

- `docs/corrida-via-menos-uno.md`
- `docs/corrida-via-cero.md`
- `docs/corrida-via-uno.md`
- `docs/corrida-via-dos.md`
- `docs/corrida-via-tres.md`
- `docs/borrador-registro-documental-via-menos-uno.md`

El registro formal en `docs/contexto/` permanece deliberadamente sin cambios, según la asignación
del coordinador.
