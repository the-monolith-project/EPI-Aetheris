# Experimento: suavizado exponencial (ETS) y Theta como base de C (2026-10-03)

> Protocolo fijado el 2026-10-03, antes de escribir y de correr el script, en la rama
> `feat/mejora-tablero-theta-ets` (sale de `feat/mejora-tablero-firma-candidatas`). Es la parte B
> de la Fase 2 del plan de mejora del predictor para la serie del tablero. No toca la prueba
> prospectiva congelada (`experimento-nowcast-tendencia.md`, script
> `40b6ebb78fe670222966a225438155b83ada876d`) ni la firma de K1, K2 y K3
> (`firma-candidatas-ventana-prospectiva.md`). Ninguna decisión de este documento usa una semana
> objetivo posterior a 2026-S37 y no se carga ninguna captura nueva.

## Enmienda del mismo día, antes del script y del barrido

Al escribir las pruebas se vio que el par cuyo origen es la primera semana de la serie no es un
pronóstico de ETS: la pendiente inicial es 0 por construcción. Ese par no entra en los errores de
ETS, que es lo que deja los mismos pares que T con pendiente de una semana y hace alcanzable el
control de abajo. Es un detalle de implementación; no se había calculado ninguna métrica.

## Pregunta

C promedia M0 con T, la tendencia amortiguada que mide su pendiente con las últimas 3 semanas de
la historia promediada. T es una regla de dos números. Dos familias clásicas de pronóstico
estiman la misma idea con otra forma:

- ETS con tendencia aditiva amortiguada: el nivel y la pendiente son medias móviles exponenciales,
  de modo que la pendiente usa todas las semanas anteriores con peso decreciente y no solo tres.
- Theta: nivel por suavizado exponencial simple más una deriva igual a la mitad de la pendiente
  de una recta ajustada a las últimas L semanas.

¿Alguna de las dos, puesta en lugar de T dentro de C, mejora la predicción? ¿Y un promedio de las
tres bases (T, ETS y Theta) dentro de C?

## Exploración previa, declarada

- Antes de este protocolo se leyó la estructura de los scripts de T y de su selección
  (`experimento_nowcast_tendencia.py`, `experimento_nowcast_tendencia_seleccion.py`) y se consultó
  la forma de la serie (664 semanas, de 2013-12-29 a 2026-09-13, un hueco en 2025-S53). No se
  calculó ninguna métrica de ETS ni de Theta.
- T se fijó en la exploración del 2026-09-27 mirando 2024 a 2026-S37. Por eso 2025 a 2026-S37 no es
  una ventana limpia para C, y todo lo que se mida ahí se rotula dentro de muestra, como en las
  fases anteriores. Los parámetros de ETS y de Theta se eligen con la historia hasta 2023, no con
  esas semanas.
- No se añaden pruebas después de ver los resultados. Lo que se mire después se rotula
  exploratorio.

## Datos y reglas comunes

- Serie mixta nacional (`cargar_serie_mixta`), historia promediada a 7 semanas hasta 2023 y escala
  `log1p`, igual que T. Semana sin dato (2025-S53): queda como NaN.
- Los modelos se comparan en los mismos pares origen-horizonte que T. Un origen es admisible si
  tiene dato en las 6 semanas anteriores y en el objetivo (la misma regla de la selección de T).
- Cada base da una mediana para cada origen y horizonte. Los cuantiles son los de T: la mediana
  más los 23 cuantiles de los errores de los pares (t, t + h) cuyo objetivo cae antes del origen,
  de 2014 en adelante y sin 2020, con al menos 30 errores. Así cada modelo se diferencia de T solo
  en la mediana.
- Las bases usan únicamente datos hasta el origen. Los parámetros se fijan una vez, con la
  validación de la parte A, y no se reajustan por origen.
- C' es el promedio por cuantil, en `log1p`, de M0 y de la base con peso 0,5 de M0, como C. M0 sale
  de `rangos.json` (bloques `B_h1` a `B_h8`, `q_R0`).
- Referencia: la persistencia suavizada (v = 3, sin pendiente), como en todas las fases.

## Los dos modelos

ETS (tendencia aditiva amortiguada, sin estacionalidad). Estado de nivel l y pendiente b:

- l(t) = α · z(t) + (1 − α) · (l(t−1) + φ · b(t−1))
- b(t) = β · (l(t) − l(t−1)) + (1 − β) · φ · b(t−1)
- mediana a h semanas: l(t) + b(t) · (φ + φ² + … + φ^h)
- inicio: l(0) = z(0), b(0) = 0. En una semana sin dato el estado avanza sin actualizarse:
  l(t) = l(t−1) + φ · b(t−1) y b(t) = φ · b(t−1).
- rejilla: α en {0,4; 0,6; 0,8; 1,0}, β en {0,2; 0,4; 0,6; 0,8; 1,0}, φ en {0,8; 0,9; 0,95}. Son 60
  configuraciones. Con α = 1 y β = 1 es T con pendiente de una semana.

Theta (forma de Hyndman y Billah del método de Assimakopoulos y Nikolopoulos):

- ℓ(t): suavizado exponencial simple de z con α, ℓ(0) = z(0); en una semana sin dato ℓ no cambia.
- b(t): pendiente de la recta de mínimos cuadrados de z sobre las últimas L semanas, con las
  semanas que tienen dato y exigiendo al menos max(3, L/2) de ellas.
- mediana a h semanas: ℓ(t) + (b(t) / 2) · (h − 1 + 1/α).
- rejilla: α en {0,3; 0,5; 0,7; 0,9; 1,0} y L en {6, 8, 12, 16, 26}. Son 25 configuraciones.
- Sobre la serie completa la pendiente de una recta es casi cero (doce años de ondas epidémicas),
  por eso la recta es local. La deriva no se amortigua; es la diferencia de diseño con ETS.

Ninguna de las dos lleva estacionalidad: de eso se ocupa M0, y T tampoco la lleva.

## Controles antes de cualquier barrido

- Las pruebas del script comparan ETS y Theta con implementaciones independientes escritas con
  bucles explícitos, con series lineales y constantes, y comprueban que cortar la serie en un
  origen no cambia su mediana (sin fuga del futuro).
- ETS con α = 1, β = 1 y φ = 0,8 debe reproducir T con φ = 0,8 y pendiente de una semana
  (`Reglas.cuantiles(o, h, 0.8, 1)` de la selección), con diferencia máxima menor o igual que
  1e-9, en la validación, en H1 y en los orígenes de H2 anteriores al hueco de 2025-S53 (después
  del hueco los conjuntos de errores difieren por una semana).
- T vigente reproduce `q_T` y `q_C_R0` de `rangos.json` con las tolerancias de la selección (T
  0,0005; C 0,003; WIS de la referencia 0,0005): se llama al control de la selección.

Si un control falla no se barre nada.

## A. Elegir con la historia hasta 2023

Validación: objetivos de 2018, 2019, 2021, 2022 y 2023, con la historia promediada a 7 semanas y
como objetivo la propia historia, igual que la selección de T. Puntaje de una configuración en un
horizonte: 1 − WIS(configuración) / WIS(referencia), con el WIS promediado dentro de cada año.
Puntaje de la configuración: promedio sobre los cinco años y los ocho horizontes. Una sola
configuración por familia para los ocho horizontes; no se eligen tramos.

Regla de cambio, fijada ahora. La mejor configuración de una familia pasa solo si supera a T
vigente (φ = 0,8, pendiente de 3 semanas) en al menos 0,005 de puntaje promedio y la supera en al
menos 3 de los 5 años. Es la misma regla con que se examinó T. Si una familia no la pasa, el
resultado de esa familia es que no supera a T en la historia y no se confirma nada.

## B. Confirmación fuera de la selección

Solo para las familias que pasen A. Dos conjuntos que no sirvieron para elegir la configuración:

- H1: objetivos de 2024 (OpenDengue ya promediado por MINSAL).
- H2: objetivos de 2025 a 2026-S37 (tablero). Rotulada dentro de muestra: T y C se fijaron mirándola.

Una familia (con su configuración elegida en A) queda elegible para firmarse como candidata
paralela a C si cumple todo:

- (a) la regla de cambio de A;
- (b) en H1 y en H2, el promedio sobre los ocho horizontes de WIS(C') / WIS(C) es menor que 1;
- (c) la cobertura al 95 % de C' en H2, agrupando horizontes, no baja más de 0,03 respecto a la de C.

Se reportan, sin criterio: el WIS de la base contra T, el skill contra la persistencia suavizada,
las coberturas del 50 % y del 95 %, la razón por horizonte y por grupo (h1-2, h3-4, h5-8), y la
prueba de Diebold-Mariano contra C por horizonte (Newey-West con h − 1 rezagos y corrección de
Harvey-Leybourne-Newbold, con Holm entre todas las comparaciones). La prueba no decide nada:
con unas 80 semanas autocorrelacionadas solo sirve para ver cuánta incertidumbre hay.

También se reporta, como descripción y aunque la familia no pase A, el mejor de cada familia
contra C en H1 y en H2. Esa fila no habilita nada.

## C. Promedio de bases (rotulado exploratorio)

Base ensamblada: promedio por cuantil, en `log1p`, de T vigente, del mejor ETS y del mejor Theta de
A (los mejores de cada familia por puntaje de validación, pasen o no la regla de cambio), con peso
1/3 cada uno. C'' es su mezcla al 50 % con M0. Se corre siempre. No tiene regla de selección
propia, así que se rotula exploratorio. Queda elegible para firmarse si cumple (b) y (c) con C''
en lugar de C'.

## Qué habilita cada resultado

- Una candidata elegible (ETS, Theta o el promedio) se propone a Eduardo para firmarse como
  predicción paralela a C en la ventana de la prueba congelada, en un documento aparte, con el
  criterio de K1 a K3: razón media de WIS contra C menor o igual que 0,99, razón menor que 1 en
  al menos 5 de 8 horizontes y cobertura del 95 % no más de 0,03 bajo C. Esto solo es posible
  antes de cargar una captura con 2026-S38 o posterior.
- Si ninguna es elegible, es un resultado negativo con sus cifras: la tendencia de 3 semanas está
  en la meseta de estas familias y no se firma nada nuevo.
- Estar elegible no confirma nada. La confirmación solo la da la ventana prospectiva.

## Probabilidad previa y comparaciones múltiples

T ya es una regla de tendencia amortiguada, y ETS la contiene como caso límite (α = β = 1, pendiente
de una semana). La ganancia esperable es pequeña. Con tres candidatas posibles y dos conjuntos
de confirmación que se ven a la vez, la regla puede dejar pasar por azar una variante sin ventaja.
Por eso la elegibilidad solo habilita a firmar una predicción paralela, cuyo costo es bajo, y no
cambia el sitio. En el peor caso la ventana prospectiva tendría seis candidatas contra C y la
corrección de Holm se hace sobre todas las comparaciones.

## Reproducibilidad

- Script `backend/ingestion/experimento_nowcast_theta_ets.py`, con pruebas en
  `backend/ingestion/tests/test_theta_ets.py`. Reutiliza `historia`, `Reglas`, `cargar_b` y las
  funciones de métrica de `experimento_nowcast_tendencia_seleccion.py`.
- Modos `--control`, `--parte-a`, `--parte-b` y `--parte-c`. Salida en
  `docs/agentes/mejora-predictor/resultados-nuevos/theta_ets.json`.
- El script se escribe y se commitea, con sus pruebas, antes de correr cualquier parte.
