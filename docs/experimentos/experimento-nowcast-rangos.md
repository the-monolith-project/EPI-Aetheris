# Experimento: calibración de los rangos y ajustes de corto plazo (2026-10-02)

> Protocolo fijado el 2026-10-02, antes de la primera corrida, en la rama
> `feat/mejora-predictor-agente`. Las variantes, las fases, la métrica y los criterios quedan
> escritos aquí antes de ver un resultado. Cualquier cambio posterior va en una sección de
> enmiendas con fecha, antes de la corrida a la que afecta.

## Motivación

1. **Los rangos quedan por debajo del nominal.** En la validación de OpenDengue (2019 y
   2021-2024) M0 calibrado cubre 0,55 al 50 % y 0,88 al 95 % a 4 semanas. Con la serie del
   tablero (2025-2026) la mezcla C cubre 0,39 y 0,91; en 2026 solo, 0,79 al 95 %, por debajo
   del 0,85 que exige la prueba prospectiva. La calibración CQR-r actual estira cada semiancho
   con un factor simétrico calculado sobre 52 pares, winsorizado y topado, y los tres
   intervalos externos colapsan al mismo factor (`modelo-actual.md`, sección 2.3).
2. **A 1 a 3 semanas la ventaja es casi nula.** Contra la persistencia limpia, M0 vale entre
   −0,04 y 0,05 a 1 a 3 semanas en la validación, y C vale −0,08 a 1 semana en 2024-2026.
   En 2025 el modelo predijo de más casi todo el año: el problema estaba en la posición de la
   mediana, no en el ancho (experimento de mejora, lectura).

Las dos cosas se pueden tratar sin reentrenar nada: son capas que actúan sobre los cuantiles
que el modelo ya produce, con información anterior al origen. Por eso van en un solo
experimento con dos preguntas.

## Preguntas

A. ¿Alguna calibración alternativa acerca la cobertura al nominal con un costo en WIS de a lo
sumo 5 %?

B. ¿Una corrección del sesgo reciente o un peso de mezcla elegido por desempeño reciente
mejora la predicción a 1 a 3 semanas sin empeorarla a 4 y a 8?

## Qué no se hace

- No se reentrena M0 ni se cambian sus hiperparámetros, sus variables ni su cadencia.
- No se tocan la base de datos, la API, el frontend ni los artefactos publicados.
- No se usan semanas objetivo desde 2026-S38.
- No se añaden variantes después de ver un resultado.

## Capas

Todas actúan sobre los cuantiles en escala `log1p`, se reordenan y vuelven a escala natural
con piso 0. Todas usan solo pares con fecha objetivo anterior a la del origen.

Calibración (pregunta A):

| Capa | Definición |
|---|---|
| R0 | CQR-r publicada: factor simétrico por intervalo sobre los 52 pares más recientes, score winsorizado al p90, factor en [0; 4]. Control. |
| R1 | CQR-r asimétrica: un factor para el semiancho inferior y otro para el superior, cada uno al nivel conformal `1 − α/2` de su propio score (`(m − y)/semi_inf` y `(y − m)/semi_sup`), con la misma winsorización y el mismo tope. |
| R2 | CQR-r con 104 pares de calibración en lugar de 52 (mínimo de entrenamiento propio 120, como ahora; los orígenes con menos de 224 pares no tienen predicción con esta capa). |
| R3 | Conformal adaptativo (Gibbs y Candès, 2021) sobre R0: por intervalo, el nivel nominal `1 − α` se reemplaza por `1 − α_t`, con `α_{t+1} = α_t + γ (α − err_t)`, `err_t = 1` si el valor observado del par más reciente ya conocido quedó fuera del intervalo R0 y 0 si no, `α_0 = α`, `γ = 0,03`, `α_t` acotado en [0,001; 0,5]. El factor se lee de los mismos scores de R0 al nivel `1 − α_t`. |

Capas de corto plazo (pregunta B):

| Capa | Definición |
|---|---|
| S1 | Sesgo reciente: todos los cuantiles se desplazan en `log1p` por `−β · ē`, con `ē` el promedio de `log1p(mediana) − log1p(y)` en los últimos `K = 8` pares conocidos del mismo horizonte (objetivo anterior al origen), `β = 1`. Si hay menos de 4 pares conocidos no se corrige. |
| C1 | Peso por desempeño reciente, solo para la mezcla C: `w ∈ {0; 0,25; 0,5; 0,75; 1}` es el peso de M0 que minimiza el WIS medio de la mezcla con T sobre los últimos `K = 26` pares conocidos del mismo horizonte. Con menos de 8 pares conocidos, `w = 0,5`. |

Sensibilidades, que se reportan y no deciden: R3 con `γ` en {0,01; 0,10}; S1 con `K` en
{4; 13} y con `β = 0,5`; C1 con `K` en {13; 52}.

## Fases

**Fase A, validación (decide):** M0 sobre la serie mixta con objetivos en 2019, 2021, 2022,
2023 y 2024, h = 1 a 8. Capas R1, R2, R3 y S1 sobre M0. La cadena de M0 es la del experimento
de mejora y debe reproducir sus cuantiles.

**Fase B, serie del tablero (se mira una vez):** objetivos de 2025-S1 a 2026-S37, h = 1 a 8.
La predicción publicada ahí es C, mezcla de M0 calibrado y T. Se evalúan:

- C con R0 (control, debe reproducir `tendencia_verificacion.json`);
- C con la capa de calibración elegida en la fase A aplicada a M0 antes de mezclar;
- R4: CQR-r simétrica de 52 pares aplicada a la mezcla C misma, con los errores de C en los
  pares de calibración (T se evalúa en esos pares con la historia promediada). Solo existe en
  esta fase porque C solo existe aquí;
- S1 y C1 sobre C, si pasaron la fase A (S1) o directamente (C1, que no tiene equivalente en
  la fase A; el experimento de mejora ya midió la mezcla con la persistencia por desempeño
  reciente y no se confirmó).

Las demás capas se calculan y se reportan en la fase B, pero su cifra no decide nada. Los
orígenes de la fase B que necesitan historia de 2024 para las ventanas de S1 y C1 la toman de
la cadena de validación, como hace `experimento_nowcast_tendencia.py --verificar`.

2025 y 2026 sirvieron para elegir C. Un resultado positivo en la fase B es candidato a una
prueba prospectiva futura, no una confirmación.

## Referencias

Persistencia limpia (validación) y persistencia suavizada (tablero), como en los experimentos
de mejora y de tendencia. Se reportan también la publicada y, en el tablero, la limpia.

## Métrica

WIS sobre 23 cuantiles, agrupado y por año; skill contra la referencia y contra la capa de
control; cobertura del 50 % y del 95 %; fracción de lo observado bajo la mediana. Horizontes
decisivos: h = 4 y h = 8 para la pregunta A; h = 1, 2 y 3 (ganancia) más h = 4 y h = 8 (no
empeorar) para la pregunta B.

## Criterios

**Pregunta A, fase A.** Una capa de calibración pasa si, agrupado sobre la validación, a
h = 4 y a h = 8: cobertura del 95 % en [0,90; 0,99], cobertura del 50 % en [0,40; 0,60] y
WIS ≤ 1,05 × WIS de R0. Si pasa más de una, se elige la de menor WIS medio entre h = 4 y
h = 8. Si no pasa ninguna, resultado negativo.

**Pregunta A, fase B.** La capa elegida (y R4) cumple si, sobre 2025-2026 agrupados, a h = 4 y
a h = 8: cobertura del 95 % de al menos 0,85 en 2025 y en 2026 por separado, cobertura del
50 % en [0,35; 0,65], WIS ≤ 1,05 × WIS de C con R0 y skill mayor que 0 contra la persistencia
suavizada.

**Pregunta B, fase A (S1).** Pasa si, agrupado sobre la validación, el WIS de M0 con S1 es
menor que el de M0 en h = 1, 2 y 3, con skill mayor que 0 contra la persistencia limpia en
los tres, y a h = 4 y h = 8 su WIS no supera 1,02 × WIS de M0.

**Pregunta B, fase B (S1 y C1).** Cumple si, sobre 2025-2026 agrupados, el WIS de la capa
sobre C es menor que el de C en h = 1, 2 y 3, con skill mayor que 0 contra la persistencia
suavizada en los tres, a h = 4 y h = 8 su WIS no supera 1,02 × WIS de C, y la cobertura del
95 % a h = 4 y h = 8 es de al menos 0,85.

## Qué habilita cada resultado

- Una capa que pasa la fase A y cumple en la fase B queda descrita como candidata a prueba
  prospectiva, con el procedimiento para aplicarla al artefacto. No reemplaza nada.
- Una capa que pasa la fase A y no cumple en la fase B se archiva con las cifras; el sitio no
  cambia.
- Ninguna capa pasa: resultado negativo; la cobertura por debajo del nominal queda como
  limitación medida y no corregible con estas capas.

## Controles

- Aserción anti-fuga y control negativo a h = 4 en las dos fases.
- M0 con R0 reproduce los cuantiles de `mejora_validacion.json` y `mejora_confirmacion.json`
  (diferencia 0); C con R0 reproduce `tendencia_verificacion.json` en 2025-2026.
- Las capas R3, S1 y C1 solo pueden usar pares cuyo objetivo es anterior a la fecha del
  origen; el script lo comprueba con una aserción sobre los índices reales.
- Número de variantes: 4 capas de calibración (una de control), 2 capas de corto plazo y 6
  sensibilidades. Se reportan todas.

## Reproducibilidad

Script `backend/ingestion/experimento_nowcast_rangos.py`, solo lectura sobre Postgres, 4
procesos de un hilo y `nice`. La cadena de M0 guarda, por origen, los cuantiles sin calibrar
y las predicciones del conjunto de calibración, de modo que todas las capas se calculan sobre
la misma corrida. Salida en `backend/ingestion/data/interim/nowcast/rangos_*.json` y copia
versionada en `docs/agentes/mejora-predictor/resultados-nuevos/`.

## Enmiendas

### 2026-10-02, antes de la primera corrida

Decisiones de implementación que el protocolo no fijaba. Ninguna cambia las capas elegibles,
las fases ni los criterios.

1. **Ventana de recencia de S1 y C1.** Las cadenas de validación solo contienen pares con
   objetivo en los años de validación, de modo que para los primeros orígenes de 2021 los
   "últimos pares conocidos" serían de 2019. Para que la corrección sea reciente de verdad, S1
   y C1 solo consideran pares cuyo objetivo cae dentro de las 52 semanas anteriores a la fecha
   del origen, y dentro de ellos toman los últimos `K`. Con menos de 4 pares (S1) u 8 pares (C1)
   no se corrige y el peso queda en 0,5.
2. **Empates en C1.** Si varios pesos dan el mismo WIS medio, se elige el más cercano a 0,5.
3. **Mediana en S1.** El sesgo se mide con la mediana calibrada por R0, que coincide con la del
   modelo sin calibrar porque CQR-r no mueve la mediana.
4. **R3 durante 2020.** No hay pares con objetivo en 2020 en la cadena; el nivel adaptado se
   conserva sin actualizar entre el último par de 2019 y el primero de 2021.
5. **Orígenes sin predicción.** Los orígenes que R2 deja sin predicción por el mínimo de 224
   pares se excluyen de la comparación de todas las capas en ese horizonte, para que todas se
   midan sobre los mismos orígenes; el número excluido se reporta.
6. **Control de reproducción en la fase B.** Por la misma razón que en la enmienda del
   experimento de insumos (sin ONI de 2025-2026 en la semilla de esta rama), M0 con R0 y C con
   R0 reproducen con diferencia 0 la validación, y en 2025-2026 el script reporta la diferencia
   máxima frente a `mejora_confirmacion.json` y `tendencia_verificacion.json` sin detenerse.
   Todas las capas de la fase B se comparan sobre la misma corrida.
