# Experimento: peso de M0 por horizonte en la mezcla C (2026-10-03)

> Protocolo fijado el 2026-10-03, antes de escribir y de correr el script, en la rama
> `feat/mejora-tablero-ch`, que sale de `feat/mejora-tablero-banda-alta`. Es la Fase 2 (línea D, C_h)
> del plan de mejora del predictor para la serie del tablero. No toca la prueba prospectiva firmada
> en `experimento-nowcast-tendencia.md` (script congelado en 40b6ebb, semanas objetivo desde
> 2026-S38). Ninguna decisión de este documento usa una semana objetivo posterior a 2026-S37. No
> modifica `nowcast_estimacion_dengue.py` ni los artefactos publicados.

## Pregunta

C mezcla M0 y T cuantil a cuantil en escala log1p con el mismo peso, 0,5, en los ocho horizontes.
Hay indicios de que el peso conviene distinto según el horizonte: a 1 y 2 semanas T sola rinde
mejor que C. Tres preguntas:

1. Elegido con la historia y no con 2025 a 2026, ¿cambia el peso de M0 por tramo de horizonte?
2. ¿Ese peso se confirma en 2024 y en el tablero?
3. Si el peso baja y los intervalos pierden cobertura, ¿se puede separar el centro del ancho?

## Exploración previa, declarada

- En `experimento-nowcast-rangos.md` (parte B) se publicó, para 2025 a 2026-S37, el WIS por horizonte
  de C, de T sola y de M0 sola. T sola: 4,7; 10,4; 15,5; 19,5; 22,8; 26,0; 29,3; 32,1 (h = 1 a 8). C:
  5,9; 11,2; 15,9; 19,1; 21,7; 23,9; 26,4; 28,6. M0 sola: 10,1; 16,4; 22,1; 25,6; 28,1; 29,0; 30,6; 31,5.
  La cobertura al 95 % de T sola va de 0,84 a 0,90 y la de C de 0,89 a 0,94. Esa es la pista que motiva
  este experimento, y la razón de que 2025 a 2026-S37 ya no sea una ventana limpia para C_h.
- Se probó antes un peso por desempeño reciente (C1, `experimento-nowcast-rangos.md`), que se
  descartó. C_h es otra cosa: pesos fijos por tramo, elegidos con la historia.
- Antes de este protocolo se leyó el código de la Fase 1 y la estructura de `rangos.json`, y no se
  calculó ninguna métrica de esta fase.
- No se añaden pruebas después de ver los resultados. Lo que se mire después se rotula
  exploratorio.

## Datos

- Serie mixta nacional (`cargar_serie_mixta`) con la historia suavizada de k = 7 hasta 2023
  (`historia`). T es la vigente, φ = 0,8, v = 3, k = 7, con los errores de la propia historia
  (`Reglas`). La referencia es la persistencia suavizada con v = 3.
- Cuantiles de M0 (`q_R0`, ya calibrado con CQR-r) guardados en `rangos.json`: bloques `A_h1` a
  `A_h8` para los objetivos de 2019, 2021, 2022 y 2023, y `B_h1` a `B_h8` para 2024 y para 2025 a
  2026-S37. M0 no se reentrena. C_w es la mezcla `_mezcla(q_M0, q_T, w)` con w el peso de M0; w = 1
  deja M0 sola y w = 0 deja T sola.
- Validación: objetivos de 2019, 2021, 2022 y 2023 (2018 no tiene M0 y 2020 se excluye, como en todo
  el proyecto), con el objetivo en la historia suavizada, igual que la validación de T en la Fase 1.
  Sesgo conocido: M0 se entrenó y se calibró contra objetivos crudos y con rezagos crudos, de modo que
  frente a un objetivo suavizado sus intervalos resultan anchos, y ese ancho se hereda en C. Eso sesga
  la validación hacia pesos menores de M0. Por eso un cambio exige que también lo respalden 2024 y
  2025 a 2026-S37, donde la serie ya viene suavizada.
- H1: objetivos de 2024 (OpenDengue ya suavizado por MINSAL). H2: objetivos de 2025 a 2026-S37
  (tablero), rotulada dentro de muestra.

Controles antes de cualquier barrido: con w = 0,5, el código nuevo debe reproducir `q_T` y `q_C_R0` de
`rangos.json` en H1 y H2 con las tolerancias de la Fase 1 (T: 0,0005; C: 0,003; WIS de la referencia:
0,0005). Además, w = 1 devuelve M0 y w = 0 devuelve T.

## Candidatos

Rejilla de pesos: w en {0; 0,25; 0,5; 0,75; 1}. Tramos de horizonte, los de la Fase 1: h = 1 a 2,
3 a 4 y 5 a 8. Cada tramo elige su peso por separado, sin restricción de monotonía. El punto de
comparación es la vigente, w = 0,5.

Puntaje de un peso en un tramo: promedio sobre los horizontes del tramo y sobre los cuatro años de
validación de 1 − WIS(C_w) / WIS(referencia), con el WIS promediado dentro de cada año para que los
años de brote grande no manden.

Admisible: el peso cuya cobertura al 95 % en la validación (agrupando los horizontes del tramo y los
cuatro años) no queda más de 0,03 por debajo de la de w = 0,5. De los admisibles gana el de mayor
puntaje.

## Regla de cambio

La carga de la prueba está en el cambio. Para un tramo, el mejor peso admisible sustituye a 0,5 solo
si, en la validación, supera a 0,5 en al menos 0,005 de puntaje promedio y lo supera en al menos 3 de
los 4 años. Si no, el tramo se queda en 0,5 y el resultado es que el peso está en la meseta.

Confirmación, solo para los tramos que pasen la regla de cambio. El peso nuevo queda como candidato
para la siguiente fase solo si se cumple todo:

- (a) la regla de cambio en la validación;
- (b) en H1 y en H2, el promedio sobre los horizontes del tramo de WIS(C_w') / WIS(C_0,5) es menor que
  1, y en H2 es menor o igual a 0,99;
- (c) la cobertura al 95 % de C_w' en H2, agrupando los horizontes del tramo, no baja más de 0,03
  respecto a C_0,5.

Se reporta además, como descripción, el WIS por horizonte de C_w', de C_0,5, de T sola y de M0 sola, el
skill contra la referencia, la cobertura al 50 % y al 95 %, el resultado de aplicar los tres pesos
elegidos a la vez (C_h completo) y una prueba de Diebold-Mariano por horizonte con varianza de largo
plazo de Newey-West (rezagos h − 1) y corrección de Harvey-Leybourne-Newbold. La prueba no decide
nada: con unas 80 semanas autocorrelacionadas solo mide la incertidumbre.

## Extensión E1, condicionada

La cobertura puede ser la razón por la que un peso bajo no pase. Si en un tramo el mejor peso sin la
restricción de admisibilidad supera la regla de cambio en puntaje y años pero es inadmisible por
cobertura, se corre esta extensión solo para ese tramo: el centro (la mediana de la mezcla) usa ese
peso y el ancho (las desviaciones de cada cuantil respecto a la mediana, en log1p) usa w = 0,5. Con
el mismo peso en las dos partes se recupera la mezcla simple. La extensión se evalúa con la misma regla
de cambio y la misma confirmación. Si ningún tramo cumple la condición, no se corre.

## Qué se decide y qué no

Se decide si hay un C_h candidato para la Fase 4, que lo registraría como predicción paralela firmada
antes de la ventana prospectiva, y con qué pesos. No se cambia la web, el backend ni C. Un resultado
dentro de muestra no demuestra mejora; solo la ventana prospectiva puede hacerlo.

## Salidas

- Script `backend/ingestion/experimento_nowcast_peso_horizonte.py` con `--control`, `--validacion`,
  `--confirmacion` y `--extension-e1`.
- `docs/agentes/mejora-predictor/resultados-nuevos/peso_m0_por_horizonte.json`.
- Sección de resultados en este documento.
