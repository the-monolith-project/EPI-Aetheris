# Experimento: brotes sin precedente en la historia y una familia que extrapola (2026-10-02)

> Protocolo fijado el 2026-10-02, antes de la primera corrida, en la rama
> `feat/mejora-predictor-agente`. Los años, los modelos, la métrica y los criterios quedan
> escritos aquí antes de ver un resultado. Cualquier cambio posterior va en una sección de
> enmiendas con fecha, antes de la corrida a la que afecta.

## Motivación

El sitio dice que la predicción puede quedarse corta ante un brote sin precedente en la serie,
y que su ventaja depende de que la historia de entrenamiento ya incluya un brote grande. El
soporte es un solo año: con la historia recortada a 2016 en adelante, el skill de 2019 fue
−0,32 contra la referencia publicada (`modelo-actual.md`, sección 5.2). Los árboles de M0 no
extrapolan por encima del rango de entrenamiento; una regresión cuantílica lineal sobre las
mismas variables sí puede hacerlo. Este experimento amplía la evidencia a más de un año y mide
esa alternativa.

## Preguntas

1. Cuando la historia de entrenamiento no contiene ningún año de magnitud igual o mayor que el
   año de prueba, ¿M0 conserva alguna ventaja sobre la persistencia?
2. ¿Una regresión cuantílica lineal con las mismas variables, calibrada igual, iguala a M0 en
   la validación normal y lo supera cuando falta el precedente?

## Diseño

**Años de prueba y recorte.** Para cada año de prueba Y se excluyen de los objetivos de
entrenamiento, además de 2020, todos los años cuyo total anual de OpenDengue es mayor o igual
que el de Y. Los años excluidos se conservan solo como insumo de rezagos, igual que 2020. Las
referencias se calculan con la misma historia recortada, para que modelo y referencia dispongan
de la misma información; la persistencia limpia con la historia completa se reporta al lado.

| Y | total de Y | años excluidos (total anual) | máximo anual que queda | razón Y / máximo |
|---|---|---|---|---|
| 2019 | 27.470 | 2014 (53.460), 2015 (50.169) | 8.789 (2016) | 3,1 |
| 2022 | 16.542 | 2014, 2015, 2019 (27.470) | 8.789 (2016) | 1,9 |
| 2024 | 8.552 | 2014, 2015, 2016 (8.789), 2019, 2022 | 8.448 (2018) | 1,0 |

Los totales salen de la base semilla (`modelo-actual.md`, sección 3.1). 2019 y 2022 son
pruebas de brote sin precedente; 2024 tiene un precedente de su misma magnitud y sirve de
control de que el recorte por sí solo no explica una caída. 2021 y 2023 no se pueden recortar
sin dejar la historia por debajo del mínimo de pares.

**Modelos.**

| Modelo | Definición |
|---|---|
| M0 | El publicado: HGBR por cuantil con los hiperparámetros del ADR 0020, calibración CQR-r con 52 pares, cadencia 2. |
| L0 | `sklearn.linear_model.QuantileRegressor` por cuantil sobre las mismas variables estandarizadas con la media y la desviación del entrenamiento propio, `alpha = 0,001` (penalización L1), `solver = "highs"`, mismo objetivo `log1p`, misma calibración CQR-r, misma cadencia, mismo mínimo de pares. |

Dos modelos, sin variantes adicionales.

**Corridas.**

- Validación normal (historia completa desde 2014): objetivos en 2019, 2021, 2022, 2023 y
  2024, h = 1 a 8, M0 y L0. M0 debe reproducir los cuantiles del experimento de mejora.
- Recorte: para cada Y de la tabla, objetivos en Y, h = 1 a 8, M0 y L0 con la historia
  recortada de Y.
- Serie del tablero (se mira una vez, solo si L0 pasa la validación normal): objetivos de
  2025-S1 a 2026-S37, L0 y la mezcla C construida con L0 en lugar de M0.

## Referencias

Persistencia limpia (criterio), climatología estacional y persistencia estacional del
experimento de mejora, con la historia recortada en las corridas de recorte. En el tablero, la
persistencia suavizada del experimento de tendencia.

## Métrica

WIS sobre 23 cuantiles, skill contra la referencia, cobertura del 50 % y del 95 %, fracción de
lo observado bajo la mediana, y el cociente entre la mediana predicha y lo observado en las
semanas del pico de cada año (las 8 semanas de mayor conteo), como medida de saturación.

## Criterios

**Pregunta 1.** La robustez ante brotes sin precedente se declara sostenida para un modelo si
su skill contra la persistencia limpia recortada es mayor que 0 en 2019 y en 2022, a h = 4 y
a h = 8. Si en alguno de los dos años es menor o igual que 0, la afirmación del sitio (la
predicción puede quedarse corta sin precedente) queda confirmada para ese modelo. 2024 no
entra al criterio.

**Pregunta 2, validación normal.** L0 pasa si, a h = 4 y a h = 8, contra la persistencia
limpia: skill medio por año mayor que 0, gana en al menos 4 de 5 años, cobertura del 95 % en
[0,85; 0,99] y del 50 % en [0,35; 0,65], y WIS agrupado no mayor que el de M0.

**Pregunta 2, recorte.** L0 supera a M0 sin precedente si su WIS es menor que el de M0 en
2019 y en 2022, a h = 4 y a h = 8.

**Tablero.** Si L0 pasó la validación normal: C con L0 cumple si a h = 4 y a h = 8 su WIS no
supera al de la C publicada y la cobertura del 95 % es de al menos 0,85, con skill mayor que 0
contra la persistencia suavizada.

## Qué habilita cada resultado

- Robustez sostenida para M0: el sitio puede suavizar la salvedad sobre brotes sin precedente,
  citando los dos años.
- Robustez no sostenida (lo esperado): la salvedad se mantiene con dos años de soporte en vez
  de uno, y la cifra pasa a la Biblioteca.
- L0 pasa la validación normal y supera a M0 sin precedente: queda descrita como candidata a
  reemplazo o a mezcla, con su propia firma y prueba prospectiva pendientes.
- L0 no pasa la validación normal: se archiva como familia descartada con las cifras, aunque
  extrapole mejor.

## Controles

- Aserción anti-fuga y control negativo a h = 4 en la validación normal y en cada recorte.
- La exclusión de años se verifica con una aserción sobre los índices reales de entrenamiento:
  ningún objetivo cae en un año excluido.
- M0 en la validación normal reproduce los cuantiles de `mejora_validacion.json`.
- Control de mutación para L0 a h = 4 en la validación normal: el WIS debe empeorar.

## Reproducibilidad

Script `backend/ingestion/experimento_nowcast_recorte.py`, solo lectura sobre Postgres, 4
procesos de un hilo y `nice`. Salida en `backend/ingestion/data/interim/nowcast/recorte_*.json`
y copia versionada en `docs/agentes/mejora-predictor/resultados-nuevos/`.
