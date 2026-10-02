# Experimento: qué aportan a M0 el clima, el ONI y el tratamiento de los ceros (2026-10-02)

> Protocolo fijado el 2026-10-02, antes de la primera corrida, en la rama
> `feat/mejora-predictor-agente`. Las variantes, los años, la métrica y el criterio quedan
> escritos aquí antes de ver un resultado. Cualquier cambio posterior va en una sección de
> enmiendas con fecha, antes de la corrida a la que afecta.

## Motivación

M0 (ADR 0020) usa como variables ocho rezagos del conteo en `log1p`, tres resúmenes,
seis armónicos estacionales, siete medias de clima nacional, la anomalía ONI y el año de la
semana objetivo. Nunca se midió cuánto aporta cada grupo: no hay ablación en el repositorio
(`docs/agentes/mejora-predictor/modelo-actual.md`, sección 5.7). El sitio describe el clima
como insumo, y la Biblioteca no afirma que mejore la predicción; este experimento mide si esa
cautela es necesaria o si el clima se puede retirar sin pérdida.

La misma máquina sirve para medir un tratamiento de las semanas con cero casos de OpenDengue.
Hay nueve (2016-S15, S30, S51; 2018-S2; 2020-S53; 2022-S51; 2023-S30, S51, S52), seguidas de
una semana con aproximadamente el doble de lo habitual. La referencia limpia del experimento de
mejora deja de aprender de ellas; M0 las usa como dato tanto en los rezagos como en los
objetivos de entrenamiento. Aquí se mide si repartirlas entre las dos semanas, solo como insumo
del modelo, mejora los rangos sin cambiar la puntuación.

## Pregunta

Para cada grupo de insumo (clima, ONI, año, tratamiento de los ceros): ¿quitarlo o cambiarlo
mueve el WIS de M0 de forma sostenida en los años de validación, y en qué sentido?

## Variantes

Todas comparten lo demás con M0: `HistGradientBoostingRegressor` por cuantil con los
hiperparámetros publicados, 23 cuantiles, historia desde 2014, 2020 excluido como objetivo,
reajuste cada 2 semanas, calibración CQR-r con los 52 pares más recientes (winsorización al p90,
factor topado en 4,0), serie mixta con el hueco de 2025-S53 como ausencia.

| Variante | Qué cambia respecto a M0 |
|---|---|
| I0 | M0 sin cambios. Control: debe reproducir los cuantiles del experimento de mejora. |
| I1 | Sin la variable ONI. |
| I2 | Sin las siete medias de clima. Conserva el ONI. |
| I3 | Sin clima ni ONI. Quedan rezagos, resúmenes, estacionalidad y año. |
| I4 | Sin la variable año de la semana objetivo. |
| I5 | Ceros repartidos: en la serie de insumo (rezagos, resúmenes y objetivos de entrenamiento), cada semana de OpenDengue con 0 casos y la siguiente se reemplazan por su promedio. En el origen que es la propia semana con 0 (la siguiente no se conoce), el rezago `z[t]` toma el valor de la semana anterior. La puntuación usa siempre el conteo publicado. |

Son cinco variantes además del control. No se añaden otras después de ver un resultado.

## Datos y protocolo

Los del experimento de mejora: serie mixta (OpenDengue `total` hasta 2024, sospechosos del
tablero desde 2025), clima y ONI como en el modelo publicado, forward-chaining con ventana
expansiva y la aserción anti-fuga de `experimento_nowcast_corto_plazo.py` con su control
negativo.

- Validación (criterio): objetivos en 2019, 2021, 2022, 2023 y 2024, h = 1 a 8.
- Serie del tablero (se reporta, no decide): objetivos de 2025-S1 a 2026-S37, h = 1 a 8. Para
  cada variante se reporta también la mezcla C construida con ella (peso 0,5 con la tendencia
  amortiguada, sin cambios), porque eso es lo que se publica en ese tramo. Esos años sirvieron
  para elegir C y no son dato no visto. Ninguna semana objetivo desde 2026-S38 entra.

## Referencias

Las del experimento de mejora, calculadas sobre los mismos orígenes: persistencia limpia
(criterio en la validación), persistencia publicada y, en el tablero, la persistencia
suavizada del experimento de tendencia.

## Métrica

WIS sobre los 23 cuantiles, agrupado y por año. Skill `1 − WIS_modelo / WIS_referencia`.
Skill de cada variante contra I0, agrupado: `s = 1 − WIS_variante / WIS_I0`. Cobertura
empírica del 50 % y del 95 %. Sesgo: fracción de lo observado por debajo de la mediana.

## Criterio

Para I1 a I4, en la validación, a h = 4 y a h = 8, con `s` el skill de la variante contra I0:

- el insumo aporta si `s ≤ −0,03` en los dos horizontes y la variante pierde contra I0 en al
  menos 4 de los 5 años en los dos;
- el insumo estorba si `s ≥ +0,03` en los dos horizontes y la variante gana a I0 en al menos 4
  de los 5 años en los dos;
- en cualquier otro caso el efecto no es medible con estos datos.

Para I5, que es un candidato y no una ablación, el criterio del experimento de mejora: pasa la
validación si, a h = 4 y a h = 8, contra la persistencia limpia, el skill medio por año es
mayor que 0, gana en al menos 4 de 5 años, la cobertura del 95 % está en [0,85; 0,99] y la del
50 % en [0,35; 0,65], y su WIS agrupado no supera al de I0. Si pasa, se mira la serie del
tablero: C construida con I5 debe tener, a h = 4 y a h = 8, WIS no mayor que la C publicada y
cobertura del 95 % de al menos 0,85, con skill mayor que 0 contra la persistencia suavizada.

## Qué habilita cada resultado

- Un insumo que aporta: el sitio puede decir que el modelo usa ese insumo y que su retiro
  empeora la predicción en la validación, con la cifra.
- Un insumo que estorba: se deja descrita la variante sin ese insumo como candidata; cambiar el
  modelo publicado requiere su propia firma y una prueba con semanas posteriores.
- Un insumo sin efecto medible: el sitio sigue sin afirmar que mejora la predicción. Si el
  clima no tiene efecto medible, queda la decisión de conservarlo como insumo descriptivo o
  retirarlo del modelo para simplificar la carga de datos.
- I5 que pasa validación y tablero: queda descrito como candidato a prueba prospectiva. Si no,
  resultado negativo con las cifras.

## Controles

- Aserción anti-fuga y control negativo a h = 4 sobre los orígenes de la validación.
- I0 reproduce los cuantiles de M0 de `mejora_validacion.json` y `mejora_confirmacion.json`
  (diferencia 0 en todas las predicciones comparables); si no, el experimento se detiene.
- Control de mutación para I3 a h = 4 (etiquetas permutadas con semilla 12345): el WIS debe
  empeorar. I3 es la variante con menos información y la que más podría parecerse a una regla
  trivial.

## Reproducibilidad

Script `backend/ingestion/experimento_nowcast_insumos.py`, solo lectura sobre Postgres, con
semillas fijas, 4 procesos de un hilo cada uno y `nice`. Salida en
`backend/ingestion/data/interim/nowcast/insumos_*.json` y copia versionada en
`docs/agentes/mejora-predictor/resultados-nuevos/`.
