# Experimento: elegir la tendencia con la historia suavizada y recortar el entrenamiento de M0 (2026-10-03)

> Protocolo fijado el 2026-10-03, antes de escribir y de correr el script, en la rama
> `feat/mejora-tablero-fase0`. Es la Fase 1 del plan de mejora del predictor para la serie del
> tablero. No toca la prueba prospectiva firmada en `experimento-nowcast-tendencia.md` (script
> congelado en 40b6ebb, semanas objetivo desde 2026-S38). Ninguna decisión de este documento usa
> una semana objetivo posterior a 2026-S37.

## Pregunta

La Fase 0 no pudo identificar el filtro con que MINSAL construye la serie del tablero
(`analisis-forma-serie-tablero.md`). Queda lo que sí se puede hacer sin conocerlo: tratar la
historia de OpenDengue anterior a 2024 con un promedio causal de k semanas, como ya hace la
tendencia amortiguada T para aprender sus errores. Tres preguntas:

1. Suavizar la historia, ¿ayuda de verdad a T? Se compara contra no suavizar y contra otros k.
2. Los parámetros de T (amortiguación y ventana de la pendiente) se fijaron en la exploración
   del 2026-09-27 mirando 2024 a 2026. Elegidos solo con la historia suavizada hasta 2023,
   ¿salen los mismos? ¿Rinden igual o mejor fuera de esa historia?
3. M0 se entrena con OpenDengue crudo hasta 2023 y con 2024, que ya viene suavizado. ¿Mejora
   al predecir 2025 y 2026 si el entrenamiento se corta en 2023?

## Exploración previa, declarada

- T usa K = 7, φ = 0,8 y pendiente de 3 semanas desde el experimento firmado el 2026-09-27, que
  se fijó después de mirar 2024 a 2026-S37 (la constante `EXPLORACION` del script). Por eso
  2024 a 2026-S37 no es una ventana limpia para T vigente.
- Antes de este protocolo se leyó la estructura de `rangos.json` (guarda, por origen y horizonte,
  los cuantiles de M0 y de C de 2024 a 2026-S37) pero no se calculó ninguna métrica de esta
  fase. Los criterios de abajo se fijan antes de calcular nada.
- No se añaden pruebas después de ver los resultados. Lo que se mire después se rotula
  exploratorio.

## Datos

- Serie mixta nacional: OpenDengue total hasta 2024 y tablero sospechoso desde 2025
  (`cargar_serie_mixta`). Semanas sin dato, como 2025-S53, quedan como NaN y los orígenes que
  las necesitan se descartan.
- Historia suavizada con k: desde el inicio de la serie hasta 2023, cada semana pasa a ser el
  promedio de las k semanas que terminan en ella, contando los 0 como dato. De 2024 en adelante
  no se toca. Con k = 1 es la serie cruda.
- Cuantiles de M0, T y C de 2024 a 2026-S37: `docs/agentes/mejora-predictor/resultados-nuevos/rangos.json`,
  bloques `B_h1` a `B_h8` (`q_R0` es M0 publicado, `q_T`, `q_C_R0`). M0 no se reentrena salvo
  en la parte C.

## Regla T parametrizada

Mediana: z(o) + (z(o) − z(o − v)) / v · (φ + φ² + … + φ^h), con z = log1p(casos). Cuantiles:
mediana más los 23 cuantiles de los errores de los pares (t, t + h) cuyo objetivo cae antes del
origen, de 2014 en adelante y sin 2020. Vigente: φ = 0,8, v = 3, k = 7. La referencia es la
persistencia suavizada con v = 3 y el mismo k, igual que en el experimento firmado.

Controles antes de cualquier barrido: con (0,8; 3; 7) el código nuevo debe reproducir `q_T` de
`rangos.json` y, mezclado al 50 % con `q_R0`, `q_C_R0`, con diferencia máxima de cero en las
filas que existan en ambos.

## A. Elegir la tendencia con la historia hasta 2023

Validación: objetivos de 2018, 2019, 2021, 2022 y 2023 (2020 se excluye como en todo el
proyecto), con la historia suavizada con k = 7. Los errores para los cuantiles salen de 2014 en
adelante y de antes del origen, así que 2018 ya tiene cuatro años de errores.

Rejilla: φ en {0,5; 0,6; 0,7; 0,8; 0,9; 1,0} y v en {2, 3, 4, 5, 6}. Son 30 configuraciones.

Puntaje de una configuración en un horizonte h: promedio sobre los cinco años de
1 − WIS(T) / WIS(referencia), con el WIS promediado dentro de cada año. Se promedia por año y
no sobre todas las semanas para que los años de brote grande no manden.

Tres tipos de elección, todas con la validación y con las mismas semanas para todas las
configuraciones:

- Común: una sola (φ, v) para los ocho horizontes, la de mayor puntaje promedio sobre h = 1 a 8.
- Por tramo: una (φ, v) para h = 1 a 2, otra para 3 a 4 y otra para 5 a 8. Es exploratoria:
  triplica los grados de libertad con unas 90 semanas de tablero para confirmar.
- Vigente: (0,8; 3), el punto de comparación.

Regla de cambio, fijada ahora. La carga de la prueba está en el cambio: la mejor configuración
sustituye a la vigente solo si, en la validación, supera a la vigente en al menos 0,005 de
puntaje promedio y la supera en al menos 3 de los 5 años. Si no, T vigente se queda y el
resultado es que está en la meseta. Para un tramo, lo mismo con el puntaje promedio de sus
horizontes.

Confirmación fuera de la selección, solo para lo que pase la regla de cambio:

- H1: objetivos de 2024 (OpenDengue ya suavizado por MINSAL).
- H2: objetivos de 2025 a 2026-S37 (tablero). Rotulada dentro de muestra, porque T vigente se
  fijó mirándola.

La configuración nueva T' queda como candidata para la siguiente fase solo si se cumple todo:

- (a) la regla de cambio en la validación;
- (b) en H1 y en H2, el promedio sobre los horizontes de WIS(T') / WIS(T vigente) es menor que 1;
- (c) la cobertura al 95 % de T' en H2, agrupando horizontes, no baja más de 0,03 respecto a T
  vigente.

Se reporta además, como descripción, el WIS de C' (50 % M0 y 50 % T') contra C, y una prueba de
Diebold-Mariano por horizonte con varianza de largo plazo de Newey-West (rezagos h − 1) y
corrección de Harvey-Leybourne-Newbold. La prueba no decide nada: con unas 80 semanas
autocorrelacionadas solo sirve para saber qué tan grande es la incertidumbre.

## B. Sensibilidad al k del suavizado

k en {1, 3, 5, 6, 7, 8, 9, 12} con T vigente (y con T' si existe). k = 1 es no suavizar la
historia, la respuesta directa a la pregunta de la parte 1.

- En H1 y en H2 el objetivo no depende de k (solo cambian los errores que aprende T y, en 2024,
  algunos rezagos), así que el WIS es comparable entre k. Se reporta WIS, cobertura al 50 % y al
  95 % y skill contra la referencia oficial (persistencia suavizada con k = 7).
- En la validación el objetivo sí cambia con k, de modo que solo se reporta el skill contra la
  referencia del mismo k, y no se compara el WIS entre k.

No se elige k en esta fase. Regla de lectura fijada ahora: si el WIS agrupado en H2 de k = 6, 7 y
8 difiere menos de 3 %, la ambigüedad sobre el filtro no importa para T y K = 7 se queda. Si
k = 1 queda a menos de 3 % de k = 7 en H1 y en H2, suavizar la historia no aporta a T y se dice
así.

## C. M0 entrenado solo hasta 2023

M0 se reajusta cada dos semanas con ventana expansiva, de modo que al predecir 2025 y 2026 ya
entrena con 2024 (suavizado por MINSAL) y con el tablero. Variante M0_corte: los pares de
entrenamiento y de calibración quedan limitados a objetivos de 2023 o antes. Como ya no entra
ningún par nuevo, basta un ajuste por horizonte, hecho en el primer origen de H2. Recorta dos
cosas a la vez, el ajuste y la calibración CQR-r (los 104 pares más recientes), y no se pueden
separar.

- Solo H2, rotulada dentro de muestra.
- Controles: con corte en un año posterior al final de la serie y cadencia estándar, M0 debe
  reproducir `q_R0` guardado en 3 orígenes por horizonte con diferencia máxima de cero; la
  comprobación de ausencia de fuga del proyecto se corre sobre la serie y los orígenes usados.
- Lectura fijada ahora: el corte es ventaja solo si el WIS de M0_corte es menor que el de M0 en
  al menos 6 de los 8 horizontes y el promedio de WIS(M0_corte) / WIS(M0) es menor que 0,98. Si
  no, M0 se queda como está. Se reporta también C con M0_corte.

## Grados de libertad del analista

- Rejilla de 30 configuraciones para la elección común y para cada tramo (hasta 4 elecciones).
- 8 valores de k, descriptivos.
- 1 variante de M0.
- Cuatro conjuntos de semanas (validación, H1, H2, y la mezcla con C) y 8 horizontes. Con tan
  pocas semanas de tablero una diferencia pequeña no es evidencia. La estructura de elegir con
  la validación y confirmar fuera acota el exceso de optimismo de la rejilla, pero no lo
  elimina.

## Lo que sigue a este experimento

- Si T' pasa la regla, se firma como candidata para una ventana prospectiva nueva (Fase 4), con
  semanas objetivo posteriores a la firma. No sustituye a C en la prueba prospectiva ya
  congelada, que se evalúa una sola vez con el script de 40b6ebb.
- Si no pasa, T vigente queda como línea de base de las fases siguientes (modelos nuevos para la
  serie suavizada).

## Resultados

Pendientes. Se añaden después de correr el script, en este mismo documento.
