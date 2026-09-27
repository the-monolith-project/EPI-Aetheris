# Experimento: mejora de la predicción de dengue a 4–8 semanas (2026-09-27)

> Firmado por Eduardo el 2026-09-27, antes de cualquier corrida. Los parámetros, los candidatos y
> el criterio de éxito quedaron fijados en este documento antes de ver un resultado, igual que en
> el experimento original del ADR 0020. Cualquier cambio posterior va en una sección de enmiendas
> con su fecha, antes de la corrida a la que afecta.

## Motivación

La predicción publicada (ADR 0020) se validó en 2019 y 2021–2024 contra la referencia más fuerte
de tres (persistencia, climatología estacional, persistencia estacional). Dos mediciones
posteriores cambian cómo se lee esa validación:

1. **La ventaja a 1–3 semanas depende de nueve semanas.** La serie de OpenDengue tiene nueve
 semanas con 0 casos notificados (2016-S15, S30, S51; 2018-S2; 2020-S53; 2022-S51; 2023-S30,
 S51, S52), seguidas de una semana con aproximadamente el doble de lo habitual. La referencia
 aprende de su historia esos saltos (de hasta ±4 en escala log) y abre sus cuantiles extremos.
 Repuntuando las predicciones publicadas sin cambiar el modelo:
   
   | horizonte | skill publicado | referencia que no aprende de esas semanas |
   | --------- | --------------- | ----------------------------------------- |
   | 1         | 0,28 (5/5 años) | −0,09 (2/5)                               |
   | 4         | 0,29 (5/5)      | 0,06 (4/5)                                |
   | 6         | 0,28 (5/5)      | 0,13 (4/5)                                |
   | 8         | 0,35 (5/5)      | 0,18 (4/5)                                |
   

    Quitar esas semanas solo de la puntuación no cambia el resultado: el modelo no gana por acertar
    en ellas, sino porque la referencia se ensancha por ellas.
2. **Con los datos del tablero de MINSAL (2025–2026) el modelo no mejora a la referencia.** Con la
 serie extendida (ADR 0021) y la misma evaluación, el skill es negativo en 2025 y cercano a cero
 en 2026, y en 2025 el modelo predice de más casi todo el año (el rango del 50 % contiene entre el
 27 % y el 29 % de lo observado). Recalibrar los rangos no lo corrige.

La ventaja que se sostiene está a 5–8 semanas en 2019–2024. Este experimento busca un modelo que
la conserve con los datos del tablero y que no quede por detrás de la persistencia a 4 semanas.

## Pregunta

¿Alguno de dos candidatos fijados de antemano supera a la referencia más fuerte a 4 y a 8 semanas
en la validación 2019, 2021–2024, sin quedar peor que el modelo publicado, y mantiene esa ventaja
en 2025–2026, que no se usan para elegir?

## Qué no se hace

- No se modifica la base de datos. Las nueve semanas con 0 casos se conservan como las publica la
fuente.
- No se toca FastAPI, el frontend ni los artefactos publicados hasta tener el veredicto.
- No se barren hiperparámetros contra los años de prueba. La configuración es la del modelo
publicado (HistGradientBoostingRegressor por cuantil, `max_iter=150`, `max_leaf_nodes=7`,
`min_samples_leaf=20`, `l2_regularization=1.0`, `learning_rate=0.05`, sin early stopping,
`random_state=0`).
- No se añaden candidatos después de ver un resultado. Si ninguno pasa, el experimento cierra con
resultado negativo.

## Datos


| Insumo         | Detalle                                                                                                                                                                                                                                                           |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Serie de casos | OpenDengue `total`, región SV, hasta 2024; sospechosos de dengue del tablero de MINSAL (`minsal_tablero`) desde 2025. 2025-S53 no está publicada y queda como hueco: un origen cuyos rezagos la tocan no predice y un par cuyo objetivo es esa semana no entrena. |
| Clima          | Media nacional de las 7 variables de Open-Meteo, igual que el modelo publicado.                                                                                                                                                                                   |
| ONI            | Anomalía al origen, arrastrando el último valor disponible.                                                                                                                                                                                                       |
| Historia       | Desde 2014 (`ALCANCE_HISTORIA`). 2020 se usa solo como rezago, nunca como objetivo.                                                                                                                                                                               |


El empalme de 2024 a 2025 une dos series de clasificación distinta (`total` y `sospechoso`). El
ADR 0021 documenta que el tablero está suavizado y que OpenDengue 2024 probablemente viene de la
misma fuente. El experimento no corrige el nivel: si el empalme introduce un sesgo, debe verse en
2025–2026 y se reporta.

## Candidatos

Los tres comparten features, rezagos (8), cadencia de reajuste (cada 2 semanas), ventana
expansiva y calibración CQR-r con los 52 pares más recientes (winsorización al p90 y factor
topado en 4,0), salvo lo que se indica.

- **M0, control.** El modelo publicado, sin cambios. Sirve para comprobar que la corrida reproduce
lo publicado y como vara de "no quedar peor".
- **M1, predice el cambio.** El objetivo pasa de `z[t+h]` a `z[t+h] − z[t]` (escala `log1p`), y la
predicción es `z[t] + cuantil`. Los árboles no extrapolan: predecir el nivel los hace saturar ante
cambios de nivel; predecir el cambio parte de la persistencia y aprende cuándo desviarse de ella.
Se añade una feature conocida de antemano: si la semana objetivo toca Semana Santa (domingo de
Ramos a domingo de Pascua), fiestas agostinas (1–6 de agosto) o fin de año (20 de diciembre a 2
de enero).
- **M2, combinación con la persistencia.** Promedio por cuantil, en escala log, de M0 y de la
persistencia: `q = w · q_M0 + (1 − w) · q_persistencia`, con `w ∈ {0; 0,25; 0,5; 0,75; 1}`
elegido en cada reajuste por menor WIS sobre los mismos 52 pares de calibración. Solo usa datos
anteriores al origen.

## Referencia

Para cada horizonte, la más fuerte de las tres del ADR 0020 por WIS medio sobre la validación,
calculadas de dos maneras y reportadas ambas:

- **publicada:** como en el ADR 0020, aprendiendo de toda la historia;
- **limpia:** sin aprender de las 17 semanas afectadas (cada 0 y la semana siguiente), ni en los
cambios semanales de la persistencia ni en los conjuntos de la climatología.

El criterio se evalúa contra la referencia limpia, que es la más exigente.

## Protocolo

Forward-chaining sin fuga, idéntico al del ADR 0020: cada predicción usa solo pares cuyo objetivo
tiene fecha anterior al origen, con la aserción anti-fuga contra los índices reales. Se heredan
los controles: mutación deliberada (adelantar el objetivo una semana debe empeorar el WIS) y
repetibilidad (dos corridas dan métricas idénticas).

- **Validación (para elegir):** objetivos en 2019, 2021, 2022, 2023 y 2024.
- **Confirmación (se mira una sola vez):** objetivos en 2025 y 2026 hasta la última semana
publicada. Solo se evalúan M0 y el candidato elegido en la validación.

Se puntúan todas las semanas. Aparte, y solo como sensibilidad, se reporta la puntuación sin las
17 semanas afectadas.

## Métrica

WIS sobre los 23 cuantiles y skill `1 − WIS_modelo / WIS_referencia`. Cobertura empírica de los
rangos del 50 % y del 95 %. Se reportan h = 1 a 8; los decisivos son h = 4 y h = 8.

## Criterio de éxito

**Validación.** Un candidato pasa si, a h = 4 **y** a h = 8, contra la referencia limpia:

1. skill medio por año &gt; 0;
2. skill &gt; 0 en al menos 4 de los 5 años;
3. cobertura del 95 % en \[0,85; 0,99\] y del 50 % en \[0,35; 0,65\];
4. WIS medio ≤ el de M0 en la validación.

Si pasan los dos candidatos, se elige el de mayor skill medio a h = 8. Si no pasa ninguno, el
experimento cierra aquí con resultado negativo.

**Confirmación.** El candidato elegido se confirma si, en 2025–2026 agrupados, contra la
referencia limpia:

5. skill &gt; 0 a h = 4 y a h = 8;
6. cobertura del 95 % en \[0,85; 0,99\].

## Qué habilita cada resultado

- **Validación y confirmación superadas:** el candidato reemplaza al modelo publicado. Se
regeneran la estimación y el artefacto retrospectivo, se enmienda el ADR 0020 y las métricas del
sitio pasan a mostrar la referencia limpia y la confirmación en 2025–2026.
- **Validación superada, confirmación no:** no cambia el modelo publicado. El sitio dice que la
ventaja a 5–8 semanas se midió en 2019–2024 y que con los datos del tablero todavía no se
sostiene.
- **Validación no superada:** no cambia el modelo publicado y el resultado se archiva como
negativo. Las métricas del sitio se corrigen igualmente con la referencia limpia.

En los tres casos se reportan todas las cifras, por año y horizonte, para M0, M1 y M2.

## Reproducibilidad

Script nuevo, `backend/ingestion/experimento_nowcast_mejora.py`, en modo solo lectura sobre
Postgres, con salida en `backend/ingestion/data/interim/nowcast/`. Reutiliza la serie mixta, el
tratamiento del hueco y las referencias de `experimento_nowcast_tablero.py`. Para no sobrecargar
la máquina se corre con 4 procesos de un hilo cada uno y `nice`.

## Decisiones firmadas (Eduardo, 2026-09-27)

1. **Referencia del criterio:** la limpia (la publicada se reporta al lado). firmada
2. **Horizontes decisivos:** 4 y 8 semanas, las dos. firmada
3. **Candidatos:** M1 (cambio + marca de vacaciones) y M2 (combinación con la persistencia). Ni  
 uno más. firmada
4. **Confirmación:** 2025–2026, mirada una sola vez y solo para M0 y el candidato elegido. firmada
5. **Umbrales:** los del ADR 0020 (4 de 5 años, bandas de cobertura), más "no quedar peor que M0". firmada


## Enmiendas (2026-09-27, antes de la primera corrida)

Decisiones de implementación que el documento no fijaba o describía distinto del script original.
Ninguna cambia candidatos, referencia ni criterio.

1. **Control de mutación.** Se implementa como en el script del ADR 0020: etiquetas de
   entrenamiento permutadas (semilla 12345), no adelantando el objetivo una semana como decía la
   sección de protocolo. Se corre a h = 4 sobre la validación; debe empeorar el WIS de M0 y de M1.
   M2 se reporta sin exigencia, porque con etiquetas permutadas puede elegir peso 0 y quedarse con
   la persistencia.
2. **Repetibilidad.** Se repite la cadena completa a h = 4 sobre la validación y se exige que los
   cuantiles de los tres modelos sean idénticos.
3. **Persistencia de M2.** La combinación usa la persistencia publicada (la del ADR 0020, que
   aprende de toda la historia), no la limpia: M2 es un modelo y no debe depender de la elección
   de la referencia con la que se evalúa.
4. **Marca de vacaciones de M1.** Se calcula por calendario sobre la semana objetivo (domingo a
   sábado): toca el período si comparte al menos un día con él.
5. **Dos fases.** El script corre la validación y la confirmación en dos invocaciones. La
   confirmación usa, en cada horizonte, la referencia decisiva elegida en la validación, y se niega
   a correr si la validación no eligió candidato o si la confirmación ya se corrió.
