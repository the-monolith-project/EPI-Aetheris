# Experimento: predicción de dengue con la serie suavizada del tablero (2026-09-27)

> Firmado por Eduardo el 2026-09-27. El candidato, la referencia, el conjunto de prueba y el
> criterio quedaron fijados aquí antes de que exista el dato con que se evalúan: la prueba son
> semanas que MINSAL todavía no había publicado. El script se congeló con un commit antes de la
> siguiente captura del tablero. Cualquier cambio posterior va en una sección de enmiendas con su
> fecha y no puede tocar el candidato, la referencia ni el criterio.

## Motivación

1. **La serie del tablero es un promedio de varias semanas.** Varía de una semana a otra entre
 0,26 y 0,28 veces lo que varía un conteo Poisson (0,70 en 2026, con el salto de la semana 1).
 Las diferencias semanales tienen autocorrelación positiva, alrededor de +0,6. En los años
 crudos de OpenDengue esa variación va de 1,2 a 8,3 y la autocorrelación es negativa. Pasa lo
 mismo con IRA y neumonías en el tablero, y con dengue en OpenDengue 2024.
 El promedio no lo aplica el tablero: la consulta solo suma `total_casos` de la tabla
 `diagnosticos_acumulados`, y el «Año actual» del corredor endémico es la misma serie. Aplicado
 a los años crudos de OpenDengue, un promedio de las últimas 6 o 7 semanas deja la misma huella.
 La caída de Semana Santa de 2026 aparece en la semana 13, sin adelantarse, lo que apunta a un
 promedio hacia atrás. El núcleo exacto no se puede recuperar: invertir un promedio de 1 a 8
 semanas da casos negativos en todos los casos.
2. **El modelo publicado aprendió lo contrario de lo que pasa en esa serie.** M0 se entrenó con
 datos crudos, donde un salto de una semana suele ser ruido que se deshace. En un promedio, un
 movimiento continúa. Con los datos del tablero, M0 pierde contra la persistencia de 1 a 5
 semanas y predice de más (experimento de mejora, confirmación 2025–2026).
3. **Una exploración sin firmar sobre 2024–2026 sugiere un candidato.** Una tendencia amortiguada,
 con su margen de error aprendido de la historia promediada a 7 semanas, gana a la persistencia
 en todos los horizontes. Combinada con M0 gana además a 5–8 semanas. Skill agrupado de
 2024–2026 contra la persistencia suavizada (definida abajo):
   
   | h   | M0    | tendencia (T) | mezcla (C) |
   | --- | ----- | ------------- | ---------- |
   | 1   | −0,79 | 0,19          | −0,08      |
   | 2   | −0,33 | 0,19          | 0,09       |
   | 4   | −0,19 | 0,15          | 0,12       |
   | 6   | 0,05  | 0,11          | 0,19       |
   | 8   | 0,19  | 0,06          | 0,21       |
   

    C gana en los tres años de 2 a 8 semanas, con cobertura del 95 % entre 0,93 y 0,96.
    El resultado no depende de los parámetros: con ventanas de 5, 7 o 9 semanas, amortiguación de
    0,6 a 0,9 y pendiente de 2 a 4 semanas, T a 4 semanas queda entre +0,19 y +0,24 contra la
    referencia limpia. En 2019 y 2021–2023 promediados a 7 semanas, años que no se usaron para
    elegir nada, T gana a la persistencia con la misma historia: +0,39 a 1 semana, +0,34 a 4 y
    +0,13 a 8. Reentrenar M0 con la historia promediada se descartó: mejora a 1–2 semanas y en
    2026 empeora a 5–8 (entre −0,38 y −0,71).

2024, 2025 y 2026 se usaron para diseñar el candidato y no sirven como prueba. Por eso la
prueba son semanas futuras.

## Pregunta

¿La mezcla C supera a la persistencia suavizada a 4 y a 8 semanas en las semanas objetivo que
MINSAL publique después de la firma, sin quedar peor que el modelo publicado?

## Qué no se hace

- No se modifica la base de datos. La historia promediada se calcula en memoria.
- No se toca FastAPI, el frontend ni los artefactos publicados hasta tener el veredicto.
- No se cambian parámetros ni se añaden candidatos después de firmar. Si C no pasa, el
experimento cierra con resultado negativo.
- No se calculan métricas sobre las semanas de prueba antes del corte.

## Datos


| Insumo              | Detalle                                                                                                                                                                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Serie de casos      | La serie mixta del experimento de mejora: OpenDengue `total` hasta 2024 y sospechosos del tablero (`minsal_tablero`) desde 2025. Las dos usan la misma definición de caso. 2025-S53 no está publicada y queda como hueco.                              |
| Historia promediada | La misma serie con cada semana hasta 2023 reemplazada por el promedio de las 7 semanas que terminan en ella. Los 0 de OpenDengue entran al promedio como dato. Desde 2024 la serie ya viene promediada y no se toca. La usan T y la referencia; M0 no. |
| Capturas nuevas     | Capturas HAR del tablero hechas por una persona y cargadas con `cargar_minsal_tablero.py` (ADR 0021). Si MINSAL revisa una semana, gana la captura más reciente y la revisión se reporta.                                                              |
| Clima y ONI         | Como en el modelo publicado.                                                                                                                                                                                                                           |


## Modelos

- **M0, control.** El modelo publicado sobre la serie mixta, sin cambios: la misma cadena que en
la confirmación del experimento de mejora.
- **T, tendencia amortiguada.** Componente de C; se reporta pero no compite. En escala `log1p`,
la mediana es `z[o] + b · (φ + φ² + … + φʰ)`, con `b = (z[o] − z[o−3]) / 3` y `φ = 0,8`. Los 23
cuantiles suman a esa mediana los cuantiles empíricos de los errores de la misma regla en todos
los pares de la historia promediada cuyo objetivo es anterior al origen, desde 2014 y sin 2020
como objetivo. Se vuelve a escala natural con `expm1`, con piso 0. No se entrena nada.
- **C, candidato.** Promedio por cuantil, en escala `log1p`, de M0 y T con peso fijo 0,5:
`q = expm1(0,5 · log1p(q_M0) + 0,5 · log1p(q_T))`, ordenado y con piso 0.

## Referencia

- **Persistencia suavizada (criterio).** Mediana `z[o]` más los cuantiles empíricos de
`z[t+h] − z[t]` en la historia promediada, con las mismas reglas de pares que T.
- **Persistencia limpia (se reporta al lado).** La referencia del criterio del experimento de
mejora.

El criterio usa la suavizada porque la limpia aprende su margen de error de datos crudos, más
ruidosos que el tablero. Con la serie promediada ese margen queda ancho de más: en 2024–2026, solo
cambiar la historia de la persistencia la mejora en 0,10 a 4 semanas. Evaluar contra la limpia
inflaría la ventaja.

## Prueba prospectiva

- **Congelamiento.** Al firmar se hace commit del script y su hash queda anotado abajo. La
siguiente captura del tablero se hace después de ese commit. Al firmar, la última semana
capturada es 2026-S37.
- **Conjunto de prueba.** Todos los pares (origen, h), con h de 1 a 8, cuya semana objetivo sea
2026-S38 (20 al 26 de septiembre) o posterior. Cada predicción usa solo datos hasta el origen.
- **Corte.** La evaluación se corre una sola vez, cuando estén publicadas 20 semanas objetivo
desde 2026-S38, es decir, hasta 2027-S05 (31 de enero al 6 de febrero de 2027), hacia mediados
de febrero. El script se niega a puntuar antes. El conjunto incluye el cambio de año.
- **Datos al corte.** La evaluación principal usa la captura más reciente. Si MINSAL revisó
semanas que sirven de rezago, se repite como sensibilidad con los datos de la primera captura
que incluye cada origen; las capturas viejas se conservan.
- **Controles.** Aserción anti-fuga en cada reajuste de M0. M0 debe reproducir los cuantiles de la
confirmación del experimento de mejora en 2025–2026 (diferencia 0). T y C deben reproducir las
cifras de la exploración sobre 2024–2026, solo como verificación.

## Métrica

WIS sobre los 23 cuantiles y skill `1 − WIS_C / WIS_referencia`, agrupado sobre el conjunto de
prueba. Cobertura empírica de los rangos del 50 % y del 95 %, y fracción de lo observado bajo la
mediana. Se reportan h = 1 a 8 para M0, T y C; los decisivos son h = 4 y h = 8. Como
sensibilidad se reportan las cifras sin las semanas objetivo de la 50 a la 3 del año siguiente.

## Criterio de éxito

C se confirma si, sobre el conjunto de prueba al corte, a h = 4 **y** a h = 8:

1. skill agrupado &gt; 0 contra la persistencia suavizada;
2. WIS medio ≤ el de M0;
3. cobertura del 95 % ≥ 0,85, es decir, a lo sumo 3 de 20 semanas fuera del rango.

No se exige techo de cobertura: con 20 semanas, que todas caigan dentro es un resultado posible
con un rango bien calibrado.

## Qué habilita cada resultado

- **C se confirma.** C reemplaza a M0 en las predicciones hechas sobre la serie del tablero. Se
regeneran la estimación y el artefacto retrospectivo, se enmiendan los ADR 0020 y 0021, y las
métricas del sitio muestran esta prueba contra la persistencia suavizada. La medición sigue con
las semanas siguientes y se reporta.
- **C no se confirma.** M0 sigue publicado y el sitio dice que, con la serie del tablero, no supera
a la persistencia. El hallazgo sobre el promedio se documenta en el ADR 0021. Otro candidato
requiere su propia firma y semanas posteriores a ella.

Con 20 semanas correlacionadas entre sí, la prueba es corta. En los dos casos se reportan todas
las cifras por horizonte.

## Reproducibilidad

Script nuevo, `backend/ingestion/experimento_nowcast_tendencia.py`, en modo solo lectura sobre
Postgres, con salida en `backend/ingestion/data/interim/nowcast/`. Reutiliza la serie mixta, la
cadena de M0 y las referencias de `experimento_nowcast_mejora.py`. Se corre con 4 procesos de un
hilo cada uno y `nice`. Antes de cargar las capturas de 2027 hay que añadir ese año a
`semanas_epidemiologicas` con `poblar_semanas_epidemiologicas.py`.

## Decisiones firmadas (Eduardo, 2026-09-27)

1. **Candidato único:** C, mezcla con peso fijo 0,5 de M0 y T. T se reporta pero no compite. firmado
2. **Parámetros fijos:** promedio de 7 semanas para la historia, φ = 0,8 y pendiente de 3 semanas. firmado
3. **Referencia del criterio:** la persistencia suavizada; la limpia se reporta al lado. firmado
4. **Horizontes decisivos:** 4 y 8 semanas, los dos. firmado
5. **Prueba:** semanas objetivo desde 2026-S38, con corte al tener 20 publicadas (hasta 2027-S05,  
 con el cambio de año incluido). La alternativa es cortar a las 15 (hasta 2026-S52), con  
 resultado en enero pero sin el cambio de año. firmado
6. **Umbrales:** skill &gt; 0, WIS ≤ M0 y cobertura del 95 % ≥ 0,85, a h = 4 y a h = 8. firmado

## Congelamiento

- Commit del script: `40b6ebb78fe670222966a225438155b83ada876d` (2026-09-27).
- Última semana capturada al congelar: 2026-S37.
- Verificación sobre semanas ya vistas, antes del commit: la aserción anti-fuga pasa, M0 reproduce
  las 1.063 predicciones de la confirmación del experimento de mejora sin diferencia, y T, C y M0
  reproducen las cifras de la exploración con diferencia máxima de 0,005.
- Evaluación: `experimento_nowcast_tendencia.py --evaluar`, una sola vez al tener publicada
  2027-S05. El script se niega si su archivo tiene cambios sin commit, si faltan semanas o si la
  salida ya existe.

